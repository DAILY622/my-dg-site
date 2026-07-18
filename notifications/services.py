"""
Notification Service Layer
Unified service for sending notifications via multiple channels (Email, SMS, Push, WebSocket)
"""

import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.utils import timezone
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Unified notification service that handles all channels:
    - Email (Zoho SMTP)
    - Push (Browser push notifications)
    - SMS (Twilio)
    - WebSocket (Real-time)
    """

    # Notification types for routing
    NOTIFICATION_TYPES = {
        'deposit': {
            'default_channels': ['email', 'push', 'websocket'],
            'event_type': 'financial',
        },
        'withdrawal': {
            'default_channels': ['email', 'push', 'websocket'],
            'event_type': 'financial',
        },
        'investment': {
            'default_channels': ['email', 'push', 'websocket'],
            'event_type': 'financial',
        },
        'profit': {
            'default_channels': ['email', 'push', 'websocket'],
            'event_type': 'financial',
        },
        'kyc': {
            'default_channels': ['email', 'push', 'websocket'],
            'event_type': 'security',
        },
        'security': {
            'default_channels': ['email', 'sms', 'push', 'websocket'],
            'event_type': 'security',
        },
        'referral': {
            'default_channels': ['email', 'push', 'websocket'],
            'event_type': 'financial',
        },
        'system': {
            'default_channels': ['email', 'push', 'websocket'],
            'event_type': 'system',
        },
    }

    @staticmethod
    def send_notification(
        user,
        title: str,
        message: str,
        notification_type: str = 'info',
        category: str = 'general',
        priority: str = 'normal',
        action_url: str = '',
        channels: Optional[List[str]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send notification via multiple channels based on user preferences

        Args:
            user: CustomUser instance
            title: Notification title
            message: Notification message
            notification_type: Type of notification (info, success, warning, error, etc.)
            category: Category (general, financial, security, promotional)
            priority: Priority level (low, normal, high, urgent)
            action_url: Optional URL for CTA
            channels: List of specific channels to use (None = auto-detect)
            data: Additional data dict for custom fields

        Returns:
            dict: {
                'success': bool,
                'notification_id': int,
                'channels_sent': list,
                'channels_failed': list,
                'details': dict,
            }
        """
        from .models import Notification, NotificationPreference

        try:
            # Get user preferences
            prefs = NotificationPreference.get_or_create_for_user(user)

            # Create notification record in database
            notification = Notification.objects.create(
                user=user,
                title=title,
                message=message,
                notification_type=notification_type,
                category=category,
                priority=priority,
                action_url=action_url,
            )

            logger.info(
                f"Created notification {notification.id} for user {user.email}"
            )

            # Determine which channels to use
            if channels is None:
                channels = NotificationService._get_default_channels(
                    notification_type, prefs
                )

            channels_sent = []
            channels_failed = []
            delivery_status = {}

            # Send via each channel
            if 'email' in channels:
                try:
                    NotificationService._send_email(
                        user, notification, prefs, title, message, action_url
                    )
                    channels_sent.append('email')
                    notification.email_sent = True
                    delivery_status['email'] = 'sent'
                except Exception as e:
                    logger.error(f"Failed to send email notification: {e}")
                    channels_failed.append('email')
                    delivery_status['email'] = f'failed: {str(e)}'

            if 'push' in channels and prefs.push_enabled:
                try:
                    NotificationService._send_push(
                        user, notification, prefs, title, message, action_url, data
                    )
                    channels_sent.append('push')
                    delivery_status['push'] = 'sent'
                except Exception as e:
                    logger.error(f"Failed to send push notification: {e}")
                    channels_failed.append('push')
                    delivery_status['push'] = f'failed: {str(e)}'

            if 'sms' in channels and prefs.sms_enabled and prefs.phone_verified:
                try:
                    NotificationService._send_sms(
                        user, notification, prefs, message
                    )
                    channels_sent.append('sms')
                    delivery_status['sms'] = 'sent'
                except Exception as e:
                    logger.error(f"Failed to send SMS notification: {e}")
                    channels_failed.append('sms')
                    delivery_status['sms'] = f'failed: {str(e)}'

            if 'websocket' in channels:
                try:
                    NotificationService._broadcast_websocket(
                        user, notification, title, message, action_url, data
                    )
                    channels_sent.append('websocket')
                    delivery_status['websocket'] = 'sent'
                except Exception as e:
                    logger.warning(f"WebSocket broadcast failed (non-critical): {e}")
                    # Don't fail on WebSocket - user might not be online

            notification.save()

            logger.info(
                f"Sent notification {notification.id} via channels: {channels_sent}"
            )

            return {
                'success': len(channels_sent) > 0,
                'notification_id': notification.id,
                'channels_sent': channels_sent,
                'channels_failed': channels_failed,
                'details': delivery_status,
            }

        except Exception as e:
            logger.error(f"Error in send_notification: {e}", exc_info=True)
            return {
                'success': False,
                'notification_id': None,
                'channels_sent': [],
                'channels_failed': channels or [],
                'details': {'error': str(e)},
            }

    @staticmethod
    def _get_default_channels(notification_type: str, prefs) -> List[str]:
        """Get default channels for a notification type based on preferences"""
        type_config = NotificationService.NOTIFICATION_TYPES.get(
            notification_type, {'default_channels': ['email']}
        )
        channels = type_config['default_channels'].copy()

        # Filter channels based on user preferences
        if 'push' in channels and not prefs.push_enabled:
            channels.remove('push')
        if 'sms' in channels and (not prefs.sms_enabled or not prefs.phone_verified):
            channels.remove('sms')

        # Always keep email and websocket
        if 'email' not in channels:
            channels.append('email')
        if 'websocket' not in channels:
            channels.append('websocket')

        return channels

    @staticmethod
    def _send_email(user, notification, prefs, title, message, action_url) -> bool:
        """Send email notification"""

        # Check if user disabled this type
        pref_map = {
            'deposit': 'email_on_deposit',
            'withdrawal': 'email_on_withdrawal',
            'investment': 'email_on_investment',
            'profit': 'email_on_profit',
            'kyc': 'email_on_kyc',
            'referral': 'email_on_referral',
            'security': 'email_on_security',
        }

        pref_field = pref_map.get(notification.notification_type)
        if pref_field and not getattr(prefs, pref_field, True):
            logger.info(f"Email disabled for {notification.notification_type}")
            return False

        # Prepare email content
        context = {
            'user': user,
            'title': title,
            'message': message,
            'action_url': action_url,
            'notification_type': notification.notification_type,
            'company_name': settings.COMPANY_NAME,
            'company_website': settings.COMPANY_WEBSITE,
        }

        # Render HTML email template
        try:
            html_message = render_to_string(
                'notifications/email/notification.html', context
            )
        except:
            # Fallback to plain text
            html_message = None

        # Send email
        subject = f"{settings.COMPANY_NAME} - {title}"
        from_email = settings.DEFAULT_FROM_EMAIL

        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Email sent to {user.email} for notification {notification.id}")
        return True

    @staticmethod
    def _send_push(
        user, notification, prefs, title, message, action_url, data
    ) -> bool:
        """Send push notification to all subscribed devices"""

        # Check if push is disabled for this type
        pref_map = {
            'deposit': 'push_on_deposit',
            'withdrawal': 'push_on_withdrawal',
            'investment': 'push_on_investment',
            'profit': 'push_on_profit',
            'kyc': 'push_on_kyc',
            'referral': 'push_on_referral',
        }

        pref_field = pref_map.get(notification.notification_type)
        if pref_field and not getattr(prefs, pref_field, True):
            logger.info(f"Push disabled for {notification.notification_type}")
            return False

        try:
            from .models import PushSubscription

            # Get all active subscriptions for this user
            subscriptions = PushSubscription.objects.filter(user=user, is_active=True)

            if not subscriptions.exists():
                logger.info(f"No push subscriptions found for user {user.email}")
                return False

            # Send to each device
            sent_count = 0
            for subscription in subscriptions:
                try:
                    NotificationService._send_push_to_device(
                        subscription, title, message, action_url, data
                    )
                    sent_count += 1
                except Exception as e:
                    logger.error(
                        f"Failed to send push to subscription {subscription.id}: {e}"
                    )
                    # Mark as inactive if it fails
                    subscription.is_active = False
                    subscription.save()

            logger.info(f"Sent push notification to {sent_count} devices for user {user.email}")
            return sent_count > 0

        except ImportError:
            logger.warning("PushSubscription model not found - push notifications disabled")
            return False

    @staticmethod
    def _send_push_to_device(subscription, title, message, action_url, data) -> bool:
        """Send push to specific device"""
        try:
            import base64
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.backends import default_backend
            import json
            import requests
            from django.conf import settings

            # This is a simplified version - real implementation needs:
            # - VAPID public/private keys
            # - Proper Web Push encryption
            # For now, we'll log it and assume FCM integration will handle it

            logger.info(
                f"Push notification queued: {title} -> {subscription.endpoint[:50]}..."
            )

            # TODO: Implement actual Web Push sending with VAPID
            # payload = {
            #     'title': title,
            #     'body': message,
            #     'icon': '/static/images/icon-192x192.png',
            #     'badge': '/static/images/badge-72x72.png',
            #     'tag': f'notification_{subscription.user_id}',
            #     'data': data or {},
            #     'actions': [
            #         {
            #             'action': 'open',
            #             'title': 'Open',
            #         },
            #         {
            #             'action': 'close',
            #             'title': 'Close',
            #         },
            #     ],
            # }

            return True

        except Exception as e:
            logger.error(f"Error sending push to device: {e}")
            raise

    @staticmethod
    def _send_sms(user, notification, prefs, message) -> bool:
        """Send SMS notification"""

        # Check SMS preference for this type
        pref_map = {
            'deposit': 'sms_on_deposit',
            'withdrawal': 'sms_on_withdrawal',
            'security': 'sms_on_security',
        }

        pref_field = pref_map.get(notification.notification_type)
        if pref_field and not getattr(prefs, pref_field, True):
            logger.info(f"SMS disabled for {notification.notification_type}")
            return False

        try:
            from twilio.rest import Client

            # Get Twilio credentials
            account_sid = settings.TWILIO_ACCOUNT_SID
            auth_token = settings.TWILIO_AUTH_TOKEN
            from_number = settings.TWILIO_PHONE_NUMBER

            if not all([account_sid, auth_token, from_number]):
                logger.warning("Twilio not configured - SMS not sent")
                return False

            # Initialize Twilio client
            client = Client(account_sid, auth_token)

            # Truncate message to 160 chars for SMS
            sms_message = message[:160]

            # Send SMS
            message_obj = client.messages.create(
                body=sms_message,
                from_=from_number,
                to=prefs.phone_number,
            )

            logger.info(
                f"SMS sent to {prefs.phone_number} (SID: {message_obj.sid})"
            )

            # Log SMS delivery
            from .models import SMSDelivery

            SMSDelivery.objects.create(
                user=user,
                phone_number=prefs.phone_number,
                message=sms_message,
                status='sent',
                twilio_sid=message_obj.sid,
            )

            return True

        except ImportError:
            logger.warning("Twilio library not installed - SMS not sent")
            return False
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False

    @staticmethod
    def _broadcast_websocket(user, notification, title, message, action_url, data):
        """Broadcast notification via WebSocket"""

        try:
            from channels.layers import get_channel_layer

            channel_layer = get_channel_layer()

            payload = {
                'type': 'notification_message',
                'notification_id': notification.id,
                'title': title,
                'message': message,
                'action_url': action_url,
                'notification_type': notification.notification_type,
                'priority': notification.priority,
                'timestamp': notification.created_at.isoformat(),
                'data': data or {},
            }

            # Send to user's notification group
            group_name = f'user_{user.id}_notifications'
            async_to_sync(channel_layer.group_send)(group_name, payload)

            logger.info(f"WebSocket broadcast to group: {group_name}")

        except ImportError:
            logger.warning("Channels not installed - WebSocket broadcast skipped")
        except Exception as e:
            logger.warning(f"WebSocket broadcast failed: {e}")

    @staticmethod
    def send_security_alert(user, alert_title: str, alert_message: str) -> Dict:
        """
        Send security alert (highest priority, all channels)

        Args:
            user: CustomUser instance
            alert_title: Title of security alert
            alert_message: Detailed message

        Returns:
            dict: Notification result
        """
        return NotificationService.send_notification(
            user=user,
            title=alert_title,
            message=alert_message,
            notification_type='security',
            category='security',
            priority='urgent',
            channels=['email', 'sms', 'push', 'websocket'],
        )

    @staticmethod
    def send_transaction_notification(
        user, transaction_type: str, amount: Decimal, status: str, details: str = ''
    ) -> Dict:
        """
        Send transaction notification

        Args:
            user: CustomUser instance
            transaction_type: 'deposit' | 'withdrawal' | 'profit'
            amount: Transaction amount
            status: 'pending' | 'completed' | 'failed'
            details: Optional additional details

        Returns:
            dict: Notification result
        """

        status_map = {
            'pending': '⏳',
            'completed': '✅',
            'failed': '❌',
        }

        status_emoji = status_map.get(status, '')
        title = f'{status_emoji} {transaction_type.title()} {status.title()}'
        message = f'Your {transaction_type} of ${amount:.2f} has been {status}. {details}'

        return NotificationService.send_notification(
            user=user,
            title=title,
            message=message,
            notification_type=transaction_type,
            category='financial',
            priority='high' if status == 'completed' else 'normal',
            action_url=f'/dashboard/',
        )

    @staticmethod
    def batch_send_notifications(user_ids: List[str], title: str, message: str) -> Dict:
        """
        Send same notification to multiple users (for announcements)

        Args:
            user_ids: List of user IDs
            title: Notification title
            message: Notification message

        Returns:
            dict: {
                'success_count': int,
                'failed_count': int,
                'details': list of results
            }
        """
        from accounts.models import CustomUser

        results = {
            'success_count': 0,
            'failed_count': 0,
            'details': [],
        }

        for user_id in user_ids:
            try:
                user = CustomUser.objects.get(id=user_id)
                result = NotificationService.send_notification(
                    user=user,
                    title=title,
                    message=message,
                    notification_type='system',
                    category='general',
                )

                if result['success']:
                    results['success_count'] += 1
                else:
                    results['failed_count'] += 1

                results['details'].append(result)

            except Exception as e:
                logger.error(f"Failed to send to user {user_id}: {e}")
                results['failed_count'] += 1

        return results
