from django.db import models
from django.conf import settings
from django.utils import timezone


class NotificationPreference(models.Model):
    """User notification preferences"""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notification_preferences'
    )
    
    # Email notifications
    email_on_deposit = models.BooleanField(default=True, help_text='Email when deposit is approved')
    email_on_withdrawal = models.BooleanField(default=True, help_text='Email when withdrawal is processed')
    email_on_investment = models.BooleanField(default=True, help_text='Email when investment is created')
    email_on_profit = models.BooleanField(default=True, help_text='Email on profit credited')
    email_on_kyc = models.BooleanField(default=True, help_text='Email on KYC status change')
    email_on_referral = models.BooleanField(default=True, help_text='Email when someone uses your referral')
    email_on_security = models.BooleanField(default=True, help_text='Email on security alerts')
    
    # Push notifications
    push_enabled = models.BooleanField(default=False, help_text='Enable browser push notifications')
    push_on_deposit = models.BooleanField(default=True)
    push_on_withdrawal = models.BooleanField(default=True)
    push_on_investment = models.BooleanField(default=True)
    push_on_profit = models.BooleanField(default=False)
    push_on_kyc = models.BooleanField(default=True)
    push_on_referral = models.BooleanField(default=True)
    
    # SMS notifications
    sms_enabled = models.BooleanField(default=False, help_text='Enable SMS notifications')
    sms_on_deposit = models.BooleanField(default=False)
    sms_on_withdrawal = models.BooleanField(default=True)
    sms_on_security = models.BooleanField(default=True)
    
    # Phone verification (SMS)
    phone_number = models.CharField(max_length=20, blank=True, help_text='Phone number for SMS')
    phone_verified = models.BooleanField(default=False, help_text='Phone number verified')
    phone_verification_code = models.CharField(max_length=6, blank=True, help_text='6-digit verification code')
    phone_verification_attempts = models.IntegerField(default=0, help_text='Failed verification attempts')
    
    # Notification sounds
    sound_enabled = models.BooleanField(default=True, help_text='Play sound for notifications')
    
    # Digest emails
    daily_digest = models.BooleanField(default=False, help_text='Send daily summary email')
    weekly_digest = models.BooleanField(default=False, help_text='Send weekly summary email')
    
    # Marketing
    marketing_emails = models.BooleanField(default=True, help_text='Receive promotional emails')
    
    # Push device tracking
    push_devices_count = models.IntegerField(default=0, help_text='Number of active push subscriptions')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'
    
    def __str__(self):
        return f"Preferences for {self.user.email}"
    
    @classmethod
    def get_or_create_for_user(cls, user):
        """Get or create preferences for a user"""
        prefs, created = cls.objects.get_or_create(user=user)
        return prefs


class Notification(models.Model):
    """User notifications"""
    
    TYPE_CHOICES = [
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('transaction', 'Transaction'),
        ('investment', 'Investment'),
        ('system', 'System'),
    ]
    
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('financial', 'Financial'),
        ('security', 'Security'),
        ('promotional', 'Promotional'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Classification
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    email_sent = models.BooleanField(default=False)
    
    # Action
    action_url = models.CharField(max_length=500, blank=True, help_text='Optional URL for CTA')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    @classmethod
    def mark_all_as_read(cls, user):
        """Mark all user notifications as read"""
        cls.objects.filter(user=user, is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
    
    @classmethod
    def create_notification(cls, user, title, message, notification_type='info', category='general', priority='normal', action_url=''):
        """Helper method to create notifications"""
        return cls.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            category=category,
            priority=priority,
            action_url=action_url
        )


class PushSubscription(models.Model):
    """
    Browser push notification subscriptions
    Stores device subscription details for Web Push API
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='push_subscriptions'
    )
    
    # Push endpoint and keys
    endpoint = models.CharField(max_length=1000, unique=True, help_text='Push service endpoint URL')
    auth_key = models.CharField(max_length=255, help_text='Authentication key for this device')
    p256dh_key = models.CharField(max_length=255, help_text='Public key for encryption')
    
    # Device info
    user_agent = models.CharField(max_length=500, blank=True, help_text='Device user agent')
    browser = models.CharField(
        max_length=100, 
        blank=True, 
        help_text='Browser type (Chrome, Firefox, Safari, Edge)'
    )
    device_type = models.CharField(
        max_length=50, 
        default='web',
        choices=[('web', 'Web'), ('mobile', 'Mobile'), ('tablet', 'Tablet')],
        help_text='Type of device'
    )
    
    # Status
    is_active = models.BooleanField(default=True, help_text='Is subscription still valid')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text='Subscription expiration date')
    
    class Meta:
        verbose_name = 'Push Subscription'
        verbose_name_plural = 'Push Subscriptions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"Push subscription for {self.user.email} ({self.browser})"
    
    def is_expired(self) -> bool:
        """Check if subscription has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class SMSDelivery(models.Model):
    """
    SMS delivery tracking
    Records all SMS sent via Twilio integration
    """
    
    DELIVERY_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('undelivered', 'Undelivered'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='sms_deliveries'
    )
    
    phone_number = models.CharField(max_length=20, help_text='Recipient phone number')
    message = models.TextField(help_text='SMS message content')
    
    # Status tracking
    status = models.CharField(
        max_length=20, 
        choices=DELIVERY_STATUS_CHOICES, 
        default='pending'
    )
    twilio_sid = models.CharField(
        max_length=255, 
        unique=True,
        help_text='Twilio message SID for tracking'
    )
    error_message = models.TextField(blank=True, help_text='Error details if failed')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'SMS Delivery'
        verbose_name_plural = 'SMS Deliveries'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['twilio_sid']),
        ]
    
    def __str__(self):
        return f"SMS to {self.phone_number} ({self.status})"
    
    def mark_as_delivered(self):
        """Mark SMS as delivered"""
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at'])
    
    def mark_as_failed(self, error: str = ''):
        """Mark SMS as failed"""
        self.status = 'failed'
        self.error_message = error
        self.save(update_fields=['status', 'error_message'])
