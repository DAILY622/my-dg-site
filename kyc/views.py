from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import KYCDocument
from accounts.email_notifications import send_deposit_notification
import requests
import json
import os
import logging

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/jpg']
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def validate_uploaded_file(file_obj, field_name):
    """Validate uploaded file type and size."""
    if not file_obj:
        return
    
    # Check file size
    if file_obj.size > MAX_FILE_SIZE:
        raise ValidationError(f'{field_name} exceeds maximum size of 10MB')
    
    # Check file type
    if file_obj.content_type not in ALLOWED_IMAGE_TYPES:
        raise ValidationError(f'{field_name} must be JPEG or PNG image')
    
    # Verify it's actually an image by checking magic bytes
    file_obj.seek(0)
    header = file_obj.read(8)
    file_obj.seek(0)
    
    # JPEG starts with FF D8 FF, PNG starts with 89 50 4E 47
    is_jpeg = header[:3] == b'\xff\xd8\xff'
    is_png = header[:8] == b'\x89PNG\r\n\x1a\n'
    
    if not (is_jpeg or is_png):
        raise ValidationError(f'{field_name} is not a valid image file')


@login_required
def upload_kyc(request):
    """KYC document upload"""
    # Check if user already has KYC submitted
    try:
        kyc_doc = KYCDocument.objects.get(user=request.user)
        if kyc_doc.status in ['submitted', 'verified']:
            messages.info(request, 'You have already submitted KYC documents.')
            return redirect('kyc:status')
    except KYCDocument.DoesNotExist:
        kyc_doc = None
    
    if request.method == 'POST':
        document_type = request.POST.get('document_type')
        front_image = request.FILES.get('front_image')
        back_image = request.FILES.get('back_image')
        selfie_image = request.FILES.get('selfie_image')
        
        if not all([document_type, front_image, back_image, selfie_image]):
            messages.error(request, 'All fields are required.')
            return redirect('kyc:upload')
        
        # Validate uploaded files
        try:
            validate_uploaded_file(front_image, 'Front image')
            validate_uploaded_file(back_image, 'Back image')
            validate_uploaded_file(selfie_image, 'Selfie image')
        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('kyc:upload')
        
        # Create or update KYC document
        if kyc_doc:
            kyc_doc.document_type = document_type
            kyc_doc.front_image = front_image
            kyc_doc.back_image = back_image
            kyc_doc.selfie_image = selfie_image
            kyc_doc.status = 'submitted'
            kyc_doc.save()
        else:
            kyc_doc = KYCDocument.objects.create(
                user=request.user,
                document_type=document_type,
                front_image=front_image,
                back_image=back_image,
                selfie_image=selfie_image,
                status='submitted'
            )
        
        messages.success(request, 'KYC documents uploaded successfully! We will review them within 24-48 hours.')
        return redirect('kyc:status')
    
    return render(request, 'kyc/upload.html')


@login_required
def kyc_status(request):
    """Display KYC verification status"""
    try:
        kyc_document = KYCDocument.objects.get(user=request.user)
    except KYCDocument.DoesNotExist:
        kyc_document = None
    
    return render(request, 'kyc/status.html', {
        'kyc_document': kyc_document
    })


@login_required
def kyc_ai_verify(request):
    """KYC AI verification using Cloudflare Workers AI"""
    if request.method == 'POST':
        document_type = request.POST.get('document_type')
        document_image = request.FILES.get('document_image')
        
        if not all([document_type, document_image]):
            messages.error(request, 'Document type and image are required.')
            return redirect('kyc:ai_verify')
        
        # Validate file
        try:
            validate_uploaded_file(document_image, 'Document image')
        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('kyc:ai_verify')
        
        # Send to Cloudflare Worker for AI extraction
        extracted_data = extract_document_data(document_image, document_type)
        
        if extracted_data.get('success'):
            confidence_score = extracted_data.get('confidence', 0)
            extracted_fields = extracted_data.get('data', {})
            
            # Auto-approve if confidence > 85%
            if confidence_score > 85:
                auto_approved = True
                # Create or update KYC document with extracted data
                kyc_doc, created = KYCDocument.objects.get_or_create(user=request.user)
                kyc_doc.document_type = document_type
                kyc_doc.document_number = extracted_fields.get('document_number', '')
                kyc_doc.issuing_country = extracted_fields.get('country', '')
                kyc_doc.nationality = extracted_fields.get('nationality', '')
                kyc_doc.date_of_birth = extracted_fields.get('date_of_birth')
                kyc_doc.issue_date = extracted_fields.get('issue_date')
                kyc_doc.expires_at = extracted_fields.get('expiry_date')
                kyc_doc.status = 'verified'
                kyc_doc.save()
                
                messages.success(request, 'KYC verification successful! Your documents have been auto-approved.')
            else:
                auto_approved = False
                messages.warning(
                    request, 
                    f'Confidence score: {confidence_score}%. Document requires manual review.'
                )
            
            context = {
                'confidence_score': confidence_score,
                'extracted_data': extracted_fields,
                'auto_approved': auto_approved,
                'document_type': document_type,
            }
            return render(request, 'kyc/verify_ai_result.html', context)
        else:
            error_message = extracted_data.get('error', 'Failed to extract document data')
            messages.error(request, error_message)
            return redirect('kyc:ai_verify')
    
    return render(request, 'kyc/verify_ai.html')


def extract_document_data(image_file, document_type):
    """Call Cloudflare Workers AI to extract document data"""
    try:
        cloudflare_url = os.getenv('CLOUDFLARE_WORKER_URL', '')
        api_token = os.getenv('CLOUDFLARE_API_TOKEN', '')
        
        if not cloudflare_url:
            return {
                'success': False,
                'error': 'Cloudflare Worker not configured'
            }
        
        # Read image file as binary
        image_file.seek(0)
        image_data = image_file.read()
        
        # Prepare request to Cloudflare Worker
        headers = {
            'Authorization': f'Bearer {api_token}',
        }
        
        files = {
            'document': image_data,
            'document_type': (None, document_type),
        }
        
        response = requests.post(
            f'{cloudflare_url}/kyc-extract',
            headers=headers,
            files=files,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                'success': True,
                'confidence': result.get('confidence_score', 0),
                'data': result.get('extracted_data', {}),
            }
        else:
            logger.error(f"Cloudflare Worker error: {response.status_code} - {response.text}")
            return {
                'success': False,
                'error': 'AI extraction service unavailable. Please try again later.'
            }
    
    except requests.RequestException as e:
        logger.error(f"KYC AI extraction error: {str(e)}")
        return {
            'success': False,
            'error': 'Failed to connect to AI service. Please try again later.'
        }
    except Exception as e:
        logger.error(f"Unexpected error in extract_document_data: {str(e)}")
        return {
            'success': False,
            'error': 'An unexpected error occurred'
        }
