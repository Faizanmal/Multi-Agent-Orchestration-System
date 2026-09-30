"""
Webhook Service
Manages webhook delivery and notification dispatch
"""
import json
import logging
import time
from datetime import timedelta

import requests
from django.utils import timezone

from ..webhook_models import (
    AlertInstance,
    AlertRule,
    Notification,
    NotificationChannel,
    NotificationPreference,
    NotificationType,
    Webhook,
    WebhookDelivery,
)

logger = logging.getLogger(__name__)


class WebhookService:
    """Service for webhook management and delivery"""
    
    @staticmethod
    def trigger_webhooks(event_type: str, event_data: dict, event_id: str | None = None):
        """Trigger all webhooks subscribed to an event type"""
        from uuid import uuid4
        
        if not event_id:
            event_id = str(uuid4())
        
        # Find all webhooks that should trigger for this event
        webhooks = Webhook.objects.filter(is_active=True)
        
        for webhook in webhooks:
            if webhook.should_trigger(event_type, event_data):
                WebhookService.deliver_webhook(webhook, event_type, event_data, event_id)
    
    @staticmethod
    def deliver_webhook(webhook: Webhook, event_type: str, event_data: dict, event_id: str):
        """Deliver a webhook"""
        
        # Prepare payload
        payload = {
            'event_id': event_id,
            'event_type': event_type,
            'timestamp': timezone.now().isoformat(),
            'data': event_data
        }
        
        payload_json = json.dumps(payload)
        
        # Generate signature
        signature = webhook.generate_signature(payload_json)
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            webhook.signature_header: signature,
            **webhook.custom_headers
        }
        
        # Add authentication
        if webhook.auth_type == 'bearer':
            headers['Authorization'] = f'Bearer {webhook.auth_token}'
        elif webhook.auth_type == 'api_key':
            headers['X-API-Key'] = webhook.auth_token
        
        # Create delivery record
        delivery = WebhookDelivery.objects.create(
            webhook=webhook,
            event_type=event_type,
            event_id=event_id,
            event_data=event_data,
            request_url=webhook.url,
            request_headers=headers,
            request_payload=payload,
            max_attempts=webhook.max_retries
        )
        
        # Attempt delivery
        WebhookService._attempt_delivery(delivery, headers, payload_json, webhook.timeout_seconds)
    
    @staticmethod
    def _attempt_delivery(delivery: WebhookDelivery, headers: dict, payload: str, timeout: int):
        """Attempt to deliver a webhook"""
        
        try:
            start_time = time.time()
            
            response = requests.post(
                delivery.request_url,
                data=payload,
                headers=headers,
                timeout=timeout
            )
            
            response_time = int((time.time() - start_time) * 1000)
            
            # Record response
            delivery.response_status_code = response.status_code
            delivery.response_headers = dict(response.headers)
            delivery.response_body = response.text[:5000]  # Limit size
            delivery.response_time_ms = response_time
            
            # Check if successful
            if 200 <= response.status_code < 300:
                delivery.status = 'success'
                delivery.delivered_at = timezone.now()
                delivery.webhook.update_stats(True, response_time)
            else:
                delivery.status = 'failed'
                delivery.error_message = f"HTTP {response.status_code}"
                delivery.webhook.update_stats(False)
                
                # Schedule retry if attempts remaining
                if delivery.attempt_number < delivery.max_attempts:
                    WebhookService._schedule_retry(delivery)
            
            delivery.save()
            
        except requests.exceptions.Timeout:
            delivery.status = 'failed'
            delivery.error_message = 'Request timeout'
            delivery.webhook.update_stats(False)
            
            if delivery.attempt_number < delivery.max_attempts:
                WebhookService._schedule_retry(delivery)
            
            delivery.save()
            
        except Exception as e:  # noqa: BLE001
            delivery.status = 'failed'
            delivery.error_message = str(e)
            delivery.error_trace = str(e.__traceback__)
            delivery.webhook.update_stats(False)
            
            if delivery.attempt_number < delivery.max_attempts:
                WebhookService._schedule_retry(delivery)
            
            delivery.save()
    
    @staticmethod
    def _schedule_retry(delivery: WebhookDelivery):
        """Schedule a retry for failed delivery"""
        
        # Exponential backoff
        retry_delay = delivery.webhook.retry_delay_seconds * (2 ** (delivery.attempt_number - 1))
        delivery.next_retry_at = timezone.now() + timedelta(seconds=retry_delay)
        delivery.status = 'retrying'
        delivery.save()
    
    @staticmethod
    def process_retries():
        """Process pending webhook retries"""
        
        retries = WebhookDelivery.objects.filter(
            status='retrying',
            next_retry_at__lte=timezone.now()
        )
        
        for delivery in retries:
            delivery.attempt_number += 1
            
            # Re-attempt delivery
            headers = delivery.request_headers
            payload = json.dumps(delivery.request_payload)
            
            WebhookService._attempt_delivery(
                delivery,
                headers,
                payload,
                delivery.webhook.timeout_seconds
            )


class NotificationService:
    """Service for managing notifications"""
    
    @staticmethod
    def create_notification(user,
                          title: str,
                          message: str,
                          notification_type: str = NotificationType.INFO,
                          channels: list[str] | None = None,
                          action_url: str = "",
                          action_text: str = "",
                          resource_type: str = "",
                          resource_id: str | None = None,
                          priority: int = 0,
                          metadata: dict | None = None) -> Notification:
        """Create and deliver a notification"""
        
        # Get user preferences
        prefs = NotificationPreference.objects.filter(user=user).first()
        
        # Check if in quiet hours
        if prefs and prefs.is_in_quiet_hours():
            priority = min(priority, 1)  # Lower priority during quiet hours
        
        # Determine channels
        if not channels:
            channels = [NotificationChannel.IN_APP]
        
        # Filter channels based on preferences
        if prefs:
            filtered_channels = []
            for channel in channels:
                if channel == NotificationChannel.EMAIL and prefs.enable_email or channel == NotificationChannel.PUSH and prefs.enable_push or channel == NotificationChannel.SMS and prefs.enable_sms or channel == NotificationChannel.SLACK and prefs.enable_slack or channel == NotificationChannel.IN_APP:
                    filtered_channels.append(channel)
            
            channels = filtered_channels
        
        # Create notification
        notification = Notification.objects.create(
            user=user,
            type=notification_type,
            title=title,
            message=message,
            channels=channels,
            action_url=action_url,
            action_text=action_text,
            resource_type=resource_type,
            resource_id=resource_id,
            priority=priority,
            metadata=metadata or {}
        )
        
        # Deliver to channels
        NotificationService.deliver_notification(notification)
        
        return notification
    
    @staticmethod
    def deliver_notification(notification: Notification):
        """Deliver notification to specified channels"""
        
        for channel in notification.channels:
            try:
                if channel == NotificationChannel.EMAIL:
                    NotificationService._send_email(notification)
                elif channel == NotificationChannel.PUSH:
                    NotificationService._send_push(notification)
                elif channel == NotificationChannel.SMS:
                    NotificationService._send_sms(notification)
                elif channel == NotificationChannel.SLACK:
                    NotificationService._send_slack(notification)
                # IN_APP is automatically handled by database record
                
            except Exception as e:  # noqa: BLE001
                logger.error(f"Failed to deliver notification via {channel}: {e!s}")
        
        notification.delivered_at = timezone.now()
        notification.save()
    
    @staticmethod
    def _send_email(notification: Notification):
        """Send email notification"""
        from django.conf import settings
        from django.core.mail import send_mail
        
        send_mail(
            subject=notification.title,
            message=notification.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.user.email],
            fail_silently=False
        )
    
    @staticmethod
    def _send_push(notification: Notification):
        """
        Send a web-push notification via the Django Channels layer (WebSocket broadcast).
        Falls back gracefully if the channel layer is unavailable.
        """
        try:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer

            channel_layer = get_channel_layer()
            if channel_layer is None:
                logger.warning('Push notification skipped: channel layer not configured')
                return

            async_to_sync(channel_layer.group_send)(
                f'user_{notification.user.id}',
                {
                    'type': 'push_notification',
                    'notification_id': str(notification.id),
                    'title': notification.title,
                    'message': notification.message,
                    'notification_type': notification.type,
                    'action_url': notification.action_url,
                    'timestamp': timezone.now().isoformat(),
                },
            )
        except Exception as e:  # noqa: BLE001
            logger.error(f'Push notification failed for user {notification.user.id}: {e}')

    @staticmethod
    def _send_sms(notification: Notification):
        """
        Send an SMS notification.
        Uses Twilio if TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN / TWILIO_FROM_NUMBER
        are set in settings; silently skips if not configured.
        """
        from django.conf import settings as django_settings

        account_sid = getattr(django_settings, 'TWILIO_ACCOUNT_SID', None)
        auth_token = getattr(django_settings, 'TWILIO_AUTH_TOKEN', None)
        from_number = getattr(django_settings, 'TWILIO_FROM_NUMBER', None)

        if not all([account_sid, auth_token, from_number]):
            logger.info('SMS notification skipped: Twilio credentials not configured')
            return

        phone = getattr(notification.user, 'phone_number', None)
        if not phone:
            logger.warning(f'SMS skipped: user {notification.user.id} has no phone number')
            return

        try:
            resp = requests.post(
                f'https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json',
                auth=(account_sid, auth_token),
                data={
                    'From': from_number,
                    'To': phone,
                    'Body': f'{notification.title}: {notification.message}',
                },
                timeout=10,
            )
            if resp.status_code not in (200, 201):
                logger.error(f'Twilio SMS failed ({resp.status_code}): {resp.text[:200]}')
        except Exception as e:  # noqa: BLE001
            logger.error(f'SMS notification failed for user {notification.user.id}: {e}')
    
    @staticmethod
    def _send_slack(notification: Notification):
        """Send Slack notification"""
        prefs = NotificationPreference.objects.filter(user=notification.user).first()
        
        if not prefs or not prefs.slack_webhook_url:
            return
        
        payload = {
            'text': notification.title,
            'attachments': [{
                'text': notification.message,
                'color': NotificationService._get_slack_color(notification.type)
            }]
        }
        
        if prefs.slack_channel:
            payload['channel'] = prefs.slack_channel
        
        requests.post(prefs.slack_webhook_url, json=payload)
    
    @staticmethod
    def _get_slack_color(notification_type: str) -> str:
        """Get Slack color for notification type"""
        colors = {
            NotificationType.INFO: '#3B82F6',
            NotificationType.SUCCESS: '#10B981',
            NotificationType.WARNING: '#F59E0B',
            NotificationType.ERROR: '#EF4444',
            NotificationType.ALERT: '#DC2626'
        }
        return colors.get(notification_type, '#6B7280')
    
    @staticmethod
    def mark_all_read(user):
        """Mark all notifications as read for a user"""
        Notification.objects.filter(user=user, is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
    
    @staticmethod
    def get_unread_count(user) -> int:
        """Get count of unread notifications"""
        return Notification.objects.filter(user=user, is_read=False).count()
    
    @staticmethod
    def cleanup_old_notifications(days: int = 30):
        """Delete old read notifications"""
        cutoff = timezone.now() - timedelta(days=days)
        
        Notification.objects.filter(
            is_read=True,
            read_at__lt=cutoff
        ).delete()


class AlertService:
    """Service for managing alerts"""
    
    @staticmethod
    def evaluate_rules():
        """Evaluate all active alert rules"""
        
        rules = AlertRule.objects.filter(is_active=True)
        
        for rule in rules:
            if rule.can_trigger():
                AlertService._evaluate_rule(rule)
    
    @staticmethod
    def _evaluate_rule(rule: AlertRule):
        """Evaluate a single alert rule"""
        
        # Get current metric value
        # This would integrate with your metrics/monitoring system
        current_value = AlertService._get_metric_value(rule.metric)
        
        if current_value is None:
            return
        
        # Update last evaluated time
        rule.last_evaluated_at = timezone.now()
        rule.save()
        
        # Evaluate condition
        should_alert = rule.evaluate(current_value)
        
        if should_alert:
            AlertService._trigger_alert(rule, current_value)
    
    @staticmethod
    def _get_metric_value(metric: str) -> float | None:
        """
        Resolve a named metric to its current value by querying live DB data.

        Supported metric names:
          task_completion_rate, task_failure_rate, active_agents,
          active_sessions, pending_tasks, failed_tasks_1h, messages_1h
        """
        from datetime import timedelta

        from django.utils import timezone as tz

        from ..models import Agent, AgentStatus, Message, Session, Task, TaskStatus

        try:
            now = tz.now()

            if metric == 'task_completion_rate':
                total = Task.objects.count()
                if total == 0:
                    return 0.0
                completed = Task.objects.filter(status=TaskStatus.COMPLETED).count()
                return round(completed / total, 4)

            elif metric == 'task_failure_rate':
                total = Task.objects.count()
                if total == 0:
                    return 0.0
                failed = Task.objects.filter(status=TaskStatus.FAILED).count()
                return round(failed / total, 4)

            elif metric == 'active_agents':
                return float(Agent.objects.filter(status=AgentStatus.ACTIVE).count())

            elif metric == 'active_sessions':
                return float(Session.objects.filter(is_active=True).count())

            elif metric == 'pending_tasks':
                return float(Task.objects.filter(status=TaskStatus.PENDING).count())

            elif metric == 'failed_tasks_1h':
                cutoff = now - timedelta(hours=1)
                return float(
                    Task.objects.filter(
                        status=TaskStatus.FAILED,
                        completed_at__gte=cutoff,
                    ).count()
                )

            elif metric == 'messages_1h':
                cutoff = now - timedelta(hours=1)
                return float(Message.objects.filter(created_at__gte=cutoff).count())

            else:
                logger.warning(f"Unknown metric '{metric}' in AlertService._get_metric_value")
                return None

        except Exception as exc:  # noqa: BLE001
            logger.error(f"_get_metric_value failed for '{metric}': {exc}")
            return None
    
    @staticmethod
    def _trigger_alert(rule: AlertRule, metric_value: float):
        """Trigger an alert"""
        
        # Create alert instance
        message = f"Alert: {rule.name} - {rule.metric} is {metric_value} (threshold: {rule.threshold})"
        
        alert = AlertInstance.objects.create(
            rule=rule,
            metric_value=metric_value,
            message=message
        )
        
        # Update rule stats
        rule.trigger_count += 1
        rule.last_triggered_at = timezone.now()
        rule.save()
        
        # Send notifications
        notification_type = {
            'low': NotificationType.INFO,
            'medium': NotificationType.WARNING,
            'high': NotificationType.ERROR,
            'critical': NotificationType.ALERT
        }.get(rule.severity, NotificationType.WARNING)
        
        NotificationService.create_notification(
            user=rule.user,
            title=f"Alert: {rule.name}",
            message=message,
            notification_type=notification_type,
            channels=rule.notification_channels,
            priority=5 if rule.severity == 'critical' else 3,
            metadata={
                'alert_id': str(alert.id),
                'rule_id': str(rule.id),
                'metric': rule.metric,
                'value': float(metric_value)
            }
        )
