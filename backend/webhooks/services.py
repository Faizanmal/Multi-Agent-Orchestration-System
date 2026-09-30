"""
Service classes for webhook delivery and notification sending
"""

import logging

import requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail
from django.utils import timezone

from .models import WebhookDelivery

logger = logging.getLogger(__name__)


class WebhookService:
    """Handle webhook delivery with retries"""

    def deliver_webhook(self, webhook, event_type, payload, attempt=1):
        """Deliver webhook payload to endpoint"""
        try:
            import time

            start_time = time.time()

            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "X-Event-Type": event_type,
                "X-Webhook-Signature": self._generate_signature(
                    webhook.secret_key, payload
                ),
                **webhook.custom_headers,
            }

            # Make request
            response = requests.post(
                webhook.url,
                json=payload,
                headers=headers,
                timeout=webhook.timeout_seconds,
            )

            duration_ms = int((time.time() - start_time) * 1000)
            success = 200 <= response.status_code < 300

            # Create delivery record
            delivery = WebhookDelivery.objects.create(
                webhook=webhook,
                event_type=event_type,
                payload=payload,
                status_code=response.status_code,
                response_body=response.text[:1000],  # Limit response size
                success=success,
                attempt_number=attempt,
                duration_ms=duration_ms,
                delivered_at=timezone.now(),
            )

            # Update webhook stats
            webhook.total_deliveries += 1
            if success:
                webhook.successful_deliveries += 1
            else:
                webhook.failed_deliveries += 1
            webhook.last_triggered = timezone.now()
            webhook.save()

            # Retry on failure
            if (
                not success
                and webhook.retry_on_failure
                and attempt < webhook.max_retries
            ):
                logger.info(f"Retrying webhook {webhook.name}, attempt {attempt + 1}")
                return self.deliver_webhook(webhook, event_type, payload, attempt + 1)

            return {
                "success": success,
                "status_code": response.status_code,
                "delivery_id": delivery.id,
            }

        except Exception as e:  # noqa: BLE001
            logger.error(f"Webhook delivery failed: {e!s}")

            # Create failed delivery record
            delivery = WebhookDelivery.objects.create(
                webhook=webhook,
                event_type=event_type,
                payload=payload,
                success=False,
                error_message=str(e),
                attempt_number=attempt,
            )

            webhook.total_deliveries += 1
            webhook.failed_deliveries += 1
            webhook.save()

            # Retry on exception
            if webhook.retry_on_failure and attempt < webhook.max_retries:
                return self.deliver_webhook(webhook, event_type, payload, attempt + 1)

            return {"success": False, "error": str(e), "delivery_id": delivery.id}

    def _generate_signature(self, secret_key, payload):
        """Generate HMAC signature for webhook"""
        import hashlib
        import hmac
        import json

        message = json.dumps(payload, sort_keys=True).encode()
        signature = hmac.new(secret_key.encode(), message, hashlib.sha256).hexdigest()

        return signature


class NotificationService:
    """Handle multi-channel notifications"""

    def send_notification(self, channel, title, message, event_type, data=None):
        """Send notification through specified channel"""
        from .models import WebhookNotification

        try:
            # Create notification record
            notification = WebhookNotification.objects.create(
                user=channel.user,
                channel=channel,
                event_type=event_type,
                title=title,
                message=message,
                data=data or {},
            )

            # Send based on channel type
            if channel.channel_type == "email":
                result = self._send_email(channel, title, message)
            elif channel.channel_type == "slack":
                result = self._send_slack(channel, title, message)
            elif channel.channel_type == "discord":
                result = self._send_discord(channel, title, message)
            elif channel.channel_type == "telegram":
                result = self._send_telegram(channel, title, message)
            elif channel.channel_type == "sms":
                result = self._send_sms(channel, title, message)
            elif channel.channel_type == "push":
                result = self._send_push(channel, title, message)
            else:
                result = {"success": False, "error": "Unsupported channel type"}

            # Update notification status
            if result.get("success"):
                notification.is_sent = True
                notification.sent_at = timezone.now()
                notification.save()

            return result

        except Exception as e:  # noqa: BLE001
            logger.error(f"Notification send failed: {e!s}")
            return {"success": False, "error": str(e)}

    def _send_email(self, channel, title, message):
        """Send email notification"""
        try:
            email_config = channel.channel_config
            recipients = email_config.get("recipients", [])

            if not recipients:
                return {"success": False, "error": "No recipients configured"}

            # Convert single string to list
            if isinstance(recipients, str):
                recipients = [r.strip() for r in recipients.split(",")]

            # Get email settings from channel config or use Django defaults
            from_email = email_config.get("from_email", settings.DEFAULT_FROM_EMAIL)

            # Create email message
            if email_config.get("html", False):
                # HTML email
                email = EmailMultiAlternatives(
                    subject=title, body=message, from_email=from_email, to=recipients
                )
                email.attach_alternative(message, "text/html")
            else:
                # Plain text email
                send_mail(
                    subject=title,
                    message=message,
                    from_email=from_email,
                    recipient_list=recipients,
                    fail_silently=False,
                )
                return {
                    "success": True,
                    "channel": "email",
                    "recipients": len(recipients),
                }

            # Send HTML email
            email.send(fail_silently=False)

            logger.info(
                f"Email notification sent to {len(recipients)} recipients: {title}"
            )
            return {"success": True, "channel": "email", "recipients": len(recipients)}

        except Exception as e:  # noqa: BLE001
            logger.error(f"Email notification failed: {e!s}")
            return {"success": False, "error": str(e)}

    def _send_slack(self, channel, title, message):
        """Send Slack notification"""
        try:
            webhook_url = channel.channel_config.get("webhook_url")
            if not webhook_url:
                return {"success": False, "error": "No webhook URL configured"}

            payload = {"text": f"*{title}*\n{message}"}

            response = requests.post(webhook_url, json=payload, timeout=10)
            return {"success": response.status_code == 200}

        except Exception as e:  # noqa: BLE001
            logger.error(f"Slack notification failed: {e!s}")
            return {"success": False, "error": str(e)}

    def _send_discord(self, channel, title, message):
        """Send Discord notification"""
        try:
            webhook_url = channel.channel_config.get("webhook_url")
            if not webhook_url:
                return {"success": False, "error": "No webhook URL configured"}

            payload = {
                "embeds": [
                    {
                        "title": title,
                        "description": message,
                        "color": 3447003,  # Blue color
                    }
                ]
            }

            response = requests.post(webhook_url, json=payload, timeout=10)
            return {"success": 200 <= response.status_code < 300}

        except Exception as e:  # noqa: BLE001
            logger.error(f"Discord notification failed: {e!s}")
            return {"success": False, "error": str(e)}

    def _send_telegram(self, channel, title, message):
        """Send Telegram notification"""
        try:
            telegram_config = channel.channel_config
            bot_token = telegram_config.get("bot_token")
            chat_id = telegram_config.get("chat_id")

            if not bot_token or not chat_id:
                return {
                    "success": False,
                    "error": "Bot token or chat ID not configured",
                }

            # Format message with title
            full_message = f"*{title}*\n\n{message}"

            # Telegram Bot API URL
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

            # Prepare payload
            payload = {
                "chat_id": chat_id,
                "text": full_message,
                "parse_mode": telegram_config.get("parse_mode", "Markdown"),
                "disable_web_page_preview": telegram_config.get(
                    "disable_preview", False
                ),
                "disable_notification": telegram_config.get("silent", False),
            }

            # Add optional reply_to_message_id
            if telegram_config.get("reply_to_message_id"):
                payload["reply_to_message_id"] = telegram_config["reply_to_message_id"]

            # Send request to Telegram API
            response = requests.post(url, json=payload, timeout=10)
            response_data = response.json()

            if response.status_code == 200 and response_data.get("ok"):
                logger.info(f"Telegram notification sent: {title}")
                return {
                    "success": True,
                    "channel": "telegram",
                    "message_id": response_data.get("result", {}).get("message_id"),
                }
            else:
                error_msg = response_data.get("description", "Unknown error")
                logger.error(f"Telegram API error: {error_msg}")
                return {"success": False, "error": error_msg}

        except Exception as e:  # noqa: BLE001
            logger.error(f"Telegram notification failed: {e!s}")
            return {"success": False, "error": str(e)}

    def _send_sms(self, channel, title, message):
        """Send SMS notification via Twilio"""
        try:
            sms_config = channel.channel_config
            account_sid = sms_config.get("account_sid")
            auth_token = sms_config.get("auth_token")
            from_number = sms_config.get("from_number")
            to_numbers = sms_config.get("to_numbers", [])

            if not all([account_sid, auth_token, from_number]):
                return {"success": False, "error": "Twilio credentials not configured"}

            if not to_numbers:
                return {"success": False, "error": "No recipient numbers configured"}

            # Convert single string to list
            if isinstance(to_numbers, str):
                to_numbers = [n.strip() for n in to_numbers.split(",")]

            # Prepare message text
            sms_text = f"{title}\\n\\n{message}"[:160]  # SMS character limit

            # Twilio API URL
            url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"

            sent_count = 0
            errors = []

            # Send to each number
            for to_number in to_numbers:
                try:
                    payload = {"From": from_number, "To": to_number, "Body": sms_text}

                    response = requests.post(
                        url, data=payload, auth=(account_sid, auth_token), timeout=10
                    )

                    if response.status_code == 201:
                        sent_count += 1
                    else:
                        errors.append(f"{to_number}: {response.json().get('message')}")

                except Exception as e:  # noqa: BLE001
                    errors.append(f"{to_number}: {e!s}")

            if sent_count > 0:
                logger.info(f"SMS sent to {sent_count} recipients: {title}")
                return {
                    "success": True,
                    "channel": "sms",
                    "sent_count": sent_count,
                    "errors": errors if errors else None,
                }
            else:
                return {"success": False, "error": f"Failed to send: {errors}"}

        except Exception as e:  # noqa: BLE001
            logger.error(f"SMS notification failed: {e!s}")
            return {"success": False, "error": str(e)}

    def _send_push(self, channel, title, message):
        """Send Push notification via Firebase Cloud Messaging"""
        try:
            push_config = channel.channel_config
            server_key = push_config.get("server_key")
            device_tokens = push_config.get("device_tokens", [])

            if not server_key:
                return {"success": False, "error": "Firebase server key not configured"}

            if not device_tokens:
                return {"success": False, "error": "No device tokens configured"}

            # Convert single string to list
            if isinstance(device_tokens, str):
                device_tokens = [t.strip() for t in device_tokens.split(",")]

            # FCM API URL
            url = "https://fcm.googleapis.com/fcm/send"

            headers = {
                "Authorization": f"key={server_key}",
                "Content-Type": "application/json",
            }

            sent_count = 0
            errors = []

            # Send to each device
            for token in device_tokens:
                try:
                    payload = {
                        "to": token,
                        "notification": {
                            "title": title,
                            "body": message,
                            "sound": push_config.get("sound", "default"),
                            "badge": push_config.get("badge", 1),
                        },
                        "priority": push_config.get("priority", "high"),
                        "data": push_config.get("data", {}),
                    }

                    response = requests.post(
                        url, json=payload, headers=headers, timeout=10
                    )
                    response_data = response.json()

                    if response_data.get("success") == 1:
                        sent_count += 1
                    else:
                        errors.append(
                            f"{token[:20]}...: {response_data.get('results', [{}])[0].get('error')}"
                        )

                except Exception as e:  # noqa: BLE001
                    errors.append(f"{token[:20]}...: {e!s}")

            if sent_count > 0:
                logger.info(f"Push notifications sent to {sent_count} devices: {title}")
                return {
                    "success": True,
                    "channel": "push",
                    "sent_count": sent_count,
                    "errors": errors if errors else None,
                }
            else:
                return {"success": False, "error": f"Failed to send: {errors}"}

        except Exception as e:  # noqa: BLE001
            logger.error(f"Push notification failed: {e!s}")
            return {"success": False, "error": str(e)}
