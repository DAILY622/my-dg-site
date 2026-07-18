"""
Cloudflare R2 Storage Backend for Django
S3-compatible object storage with zero egress fees
"""
from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings


class R2MediaStorage(S3Boto3Storage):
    """
    Cloudflare R2 storage for media files (user uploads, KYC docs, payment proofs, receipts)
    """
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    custom_domain = settings.AWS_S3_CUSTOM_DOMAIN
    file_overwrite = False
    default_acl = 'private'  # Keep files private by default
    
    def __init__(self, *args, **kwargs):
        kwargs['bucket_name'] = self.bucket_name
        kwargs['custom_domain'] = self.custom_domain
        super().__init__(*args, **kwargs)


class R2StaticStorage(S3Boto3Storage):
    """
    Cloudflare R2 storage for static files (optional, can keep WhiteNoise)
    """
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    custom_domain = settings.AWS_S3_CUSTOM_DOMAIN
    location = 'static'
    default_acl = 'public-read'
