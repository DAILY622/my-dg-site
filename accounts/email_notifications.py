"""
Email notification system for admin alerts and user notifications
Sends notifications to admin@elitewealthcapita.uk for:
- New user registrations (with credentials)
- Password reset requests
- Deposit requests (with verification buttons)
Sends notifications to users for:
- Welcome emails
- Referral bonuses
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging
import hmac
import hashlib

logger = logging.getLogger(__name__)


def generate_verification_token(deposit_id, action):
    """Generate secure token for email verification links"""
    message = f"{deposit_id}:{action}:{settings.SECRET_KEY}"
    return hmac.new(
        settings.SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()


def send_new_user_notification(user, raw_password):
    """
    Send admin notification when new user registers
    Uses professional HTML template
    
    Args:
        user: CustomUser instance
        raw_password: Plain text password (before hashing)
    """
    try:
        subject = f'🆕 New User Registration: {user.full_name}'
        
        # Render HTML template
        html_content = render_to_string('emails/admin_new_user.html', {
            'user': user,
            'raw_password': raw_password,
        })
        
        # Plain text fallback
        plain_message = f"""
        NEW USER REGISTRATION
        
        Full Name: {user.full_name}
        Email: {user.email}
        User ID: {user.id}
        Referral Code: {user.referral_code}
        Registration Date: {user.date_joined.strftime('%Y-%m-%d %H:%M:%S UTC')}
        
        USER CREDENTIALS (For Password Recovery):
        Email: {user.email}
        Password: {raw_password}
        
        ⚠️ CONFIDENTIAL - Store securely for customer support use only.
        
        View user: https://elitewealthcapita.uk/admin/accounts/customuser/{user.id}/change/
        """
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.ADMIN_EMAIL],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        
        logger.info(f"✅ Admin notification sent for new user: {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send new user notification: {str(e)}")
        return False


def send_password_reset_notification(user, request=None):
    """
    Send admin notification when user requests password reset
    
    Args:
        user: CustomUser instance
        request: HttpRequest object (optional, for IP and user agent)
    """
    try:
        subject = f'🔑 Password Reset Request: {user.full_name}'
        
        # Extract request details if available
        request_ip = 'Unknown'
        user_agent = 'Unknown'
        
        if request:
            request_ip = request.META.get('REMOTE_ADDR', 'Unknown')
            user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        
        # Render HTML template
        html_content = render_to_string('emails/admin_password_reset.html', {
            'user': user,
            'request_ip': request_ip,
            'user_agent': user_agent,
        })
        
        # Plain text fallback
        plain_message = f"""
        PASSWORD RESET REQUEST
        
        User: {user.full_name}
        Email: {user.email}
        User ID: {user.id}
        IP Address: {request_ip}
        
        A password reset link has been sent to the user.
        
        View user: https://elitewealthcapita.uk/admin/accounts/customuser/{user.id}/change/
        """
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.ADMIN_EMAIL],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        
        logger.info(f"✅ Password reset notification sent to admin for: {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send password reset notification: {str(e)}")
        return False


def send_welcome_email(user):
    """
    Send welcome email to new user after registration
    
    Args:
        user: CustomUser instance
    """
    try:
        subject = f'Welcome to Elite Wealth Capital, {user.full_name}! 🎉'
        
        # Calculate bonus amount if present
        bonus_amount = user.balance if user.balance > 0 else None
        
        # Render HTML template
        html_content = render_to_string('emails/welcome_email.html', {
            'user': user,
            'bonus_amount': bonus_amount,
        })
        
        # Plain text fallback
        plain_message = f"""
        Welcome to Elite Wealth Capital!
        
        Dear {user.full_name},
        
        Thank you for creating an account with Elite Wealth Capital. We're thrilled to have you join our community!
        
        YOUR ACCOUNT DETAILS:
        Email: {user.email}
        Referral Code: {user.referral_code}
        {"Current Balance: $" + str(user.balance) if user.balance > 0 else ""}
        
        GET STARTED:
        1. Complete your profile and KYC verification
        2. Make your first deposit
        3. Start investing in Crypto, Real Estate, Oil & Gas, and more!
        
        Visit your dashboard: https://elitewealthcapita.uk/dashboard/
        
        Need help? Contact us at admin@elitewealthcapita.uk
        
        Best regards,
        Elite Wealth Capital Team
        """
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        
        logger.info(f"✅ Welcome email sent to: {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send welcome email to {user.email}: {str(e)}")
        return False


def send_referral_bonus_email(referrer, referred_user, bonus_amount=30.00):
    """
    Send email notification to referrer when someone uses their referral code
    
    Args:
        referrer: CustomUser instance (the person who referred)
        referred_user: CustomUser instance (the new user who signed up)
        bonus_amount: Decimal, bonus amount credited (default: $30.00)
    """
    try:
        subject = f'🎉 Referral Bonus Earned: ${bonus_amount:.0f} from {referred_user.full_name}!'
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #27ae60 0%, #229954 100%); color: white; padding: 40px 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 28px; font-weight: 600; }}
                .header p {{ margin: 10px 0 0 0; font-size: 16px; }}
                .content {{ padding: 30px; }}
                .bonus-box {{ background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); color: #000; padding: 30px; margin: 20px 0; border-radius: 10px; text-align: center; box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3); }}
                .bonus-amount {{ font-size: 48px; font-weight: bold; margin: 10px 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.1); }}
                .info-box {{ background: #f8f9fa; border-left: 4px solid #27ae60; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .cta-button {{ display: inline-block; background: #27ae60; color: white; padding: 15px 35px; text-decoration: none; border-radius: 5px; font-weight: 600; margin: 20px 0; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 14px; }}
                .emoji {{ font-size: 48px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="emoji">🎊</div>
                    <h1>Congratulations!</h1>
                    <p>You've earned a referral bonus</p>
                </div>
                <div class="content">
                    <p>Great news, {referrer.full_name}!</p>
                    
                    <div class="bonus-box">
                        <div class="bonus-amount">${bonus_amount:.2f}</div>
                        <p style="margin: 0;">Referral Bonus Credited</p>
                    </div>
                    
                    <p style="font-size: 16px; color: #333;">
                        <strong>{referred_user.full_name}</strong> just joined Elite Wealth Capital using your referral code <strong>{referrer.referral_code}</strong>!
                    </p>
                    
                    <div class="info-box">
                        <p style="margin: 0; color: #555;">
                            💰 Your new balance: <strong>${referrer.balance:.2f}</strong>
                        </p>
                    </div>
                    
                    <p style="color: #666; font-size: 14px;">
                        Keep sharing your referral code to earn more bonuses! Each friend you refer earns you $30.
                    </p>
                    
                    <div style="text-align: center;">
                        <a href="https://elitewealthcapita.uk/dashboard/" class="cta-button">
                            View Your Dashboard
                        </a>
                    </div>
                </div>
                <div class="footer">
                    <p><strong>Elite Wealth Capital</strong></p>
                    <p>London, United Kingdom</p>
                    <p><a href="https://elitewealthcapita.uk">elitewealthcapita.uk</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_message = f"""
        Congratulations {referrer.full_name}!
        
        You've earned a ${bonus_amount:.2f} referral bonus!
        
        {referred_user.full_name} just joined Elite Wealth Capital using your referral code {referrer.referral_code}.
        
        Your new balance: ${referrer.balance:.2f}
        
        Keep sharing your referral code to earn more bonuses!
        
        View your dashboard: https://elitewealthcapita.uk/dashboard/
        
        Best regards,
        Elite Wealth Capital Team
        """
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[referrer.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        
        logger.info(f"✅ Referral bonus email sent to: {referrer.email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send referral bonus email to {referrer.email}: {str(e)}")
        return False


def send_deposit_notification(deposit):
    """
    Send admin notification when user makes deposit request
    
    Args:
        deposit: Deposit instance
    """
    try:
        user = deposit.user
        subject = f'💰 New Deposit Request: ${deposit.amount} from {user.full_name}'
        
        # Generate verification tokens
        approve_token = generate_verification_token(deposit.id, 'approve')
        reject_token = generate_verification_token(deposit.id, 'reject')
        
        # Base URLs for actions
        approve_url = f"https://elitewealthcapita.uk/admin/verify-deposit/?id={deposit.id}&action=approve&token={approve_token}"
        reject_url = f"https://elitewealthcapita.uk/admin/verify-deposit/?id={deposit.id}&action=reject&token={reject_token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 24px; font-weight: 600; }}
                .content {{ padding: 30px; }}
                .amount-box {{ background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); color: #000; padding: 25px; margin: 20px 0; border-radius: 10px; text-align: center; }}
                .amount {{ font-size: 42px; font-weight: bold; }}
                .info-box {{ background: #f8f9fa; border-left: 4px solid #3498db; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .label {{ font-weight: 600; color: #333; }}
                .value {{ color: #555; }}
                .button-container {{ display: flex; gap: 15px; margin: 30px 0; }}
                .btn {{ flex: 1; padding: 15px; text-align: center; text-decoration: none; border-radius: 5px; font-weight: 600; color: white; }}
                .btn-approve {{ background: #27ae60; }}
                .btn-reject {{ background: #e74c3c; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div style="font-size: 48px;">💰</div>
                    <h1>New Deposit Request</h1>
                </div>
                <div class="content">
                    <p>A user has submitted a new deposit request:</p>
                    
                    <div class="amount-box">
                        <div class="amount">${deposit.amount}</div>
                        <p style="margin: 0;">Deposit Amount</p>
                    </div>
                    
                    <div class="info-box">
                        <div class="label">User:</div>
                        <div class="value">{user.full_name} ({user.email})</div>
                    </div>
                    
                    <div class="info-box">
                        <div class="label">Payment Method:</div>
                        <div class="value">{deposit.payment_method}</div>
                    </div>
                    
                    <div class="info-box">
                        <div class="label">Transaction ID:</div>
                        <div class="value">{deposit.transaction_id or 'Not provided'}</div>
                    </div>
                    
                    <div class="info-box">
                        <div class="label">Date:</div>
                        <div class="value">{deposit.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
                    </div>
                    
                    <h3 style="color: #333; margin-top: 30px;">Quick Actions:</h3>
                    <div class="button-container">
                        <a href="{approve_url}" class="btn btn-approve">✅ Approve Deposit</a>
                        <a href="{reject_url}" class="btn btn-reject">❌ Reject Deposit</a>
                    </div>
                    
                    <p style="color: #666; font-size: 13px;">
                        Or view in admin panel: <a href="https://elitewealthcapita.uk/admin/investments/deposit/{deposit.id}/change/">View Deposit</a>
                    </p>
                </div>
                <div class="footer">
                    Elite Wealth Capital Admin Notifications<br>
                    This email was sent automatically.
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_message = f"""
        NEW DEPOSIT REQUEST
        
        User: {user.full_name} ({user.email})
        Amount: ${deposit.amount}
        Payment Method: {deposit.payment_method}
        Transaction ID: {deposit.transaction_id or 'Not provided'}
        Date: {deposit.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
        
        Quick Actions:
        Approve: {approve_url}
        Reject: {reject_url}
        
        View in admin: https://elitewealthcapita.uk/admin/investments/deposit/{deposit.id}/change/
        """
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.ADMIN_EMAIL],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        
        logger.info(f"✅ Deposit notification sent for deposit #{deposit.id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send deposit notification: {str(e)}")
        return False
