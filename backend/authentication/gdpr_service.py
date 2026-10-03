"""
GDPR Compliance and Data Privacy Service
"""

import json
import logging
import os
from typing import Any

from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

logger = logging.getLogger(__name__)

User = get_user_model()


class EncryptionService:
    """Service for data encryption/decryption"""

    def __init__(self):
        # Get encryption key from settings or environment
        key = getattr(settings, "ENCRYPTION_KEY", os.getenv("ENCRYPTION_KEY"))

        if not key:
            # Generate new key if not provided (for development)
            key = Fernet.generate_key().decode()
            logger.warning(
                "No encryption key provided, generated new key (NOT for production)"
            )

        if isinstance(key, str):
            key = key.encode()

        self.cipher = Fernet(key)

    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        try:
            encrypted = self.cipher.encrypt(data.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt encrypted string"""
        try:
            decrypted = self.cipher.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    def encrypt_dict(self, data: dict) -> str:
        """Encrypt dictionary to encrypted JSON string"""
        json_str = json.dumps(data)
        return self.encrypt(json_str)

    def decrypt_dict(self, encrypted_data: str) -> dict:
        """Decrypt encrypted JSON string to dictionary"""
        json_str = self.decrypt(encrypted_data)
        return json.loads(json_str)


class GDPRComplianceService:
    """Service for GDPR compliance management"""

    def __init__(self):
        self.encryption = EncryptionService()

    def record_consent(
        self, user_id: str, consent_type: str, granted: bool, purpose: str
    ) -> dict[str, Any]:
        """
        Record user consent

        Args:
            user_id: User identifier
            consent_type: Type of consent (e.g., 'marketing', 'analytics')
            granted: Whether consent was granted
            purpose: Purpose of data collection

        Returns:
            Consent record
        """
        from authentication.models import UserConsent

        try:
            user = User.objects.get(id=user_id)

            consent = UserConsent.objects.create(
                user=user,
                consent_type=consent_type,
                granted=granted,
                purpose=purpose,
                ip_address=None,  # Should be passed from request
                user_agent=None,  # Should be passed from request
            )

            logger.info(
                f"Consent recorded for user {user_id}: {consent_type}={granted}"
            )

            return {
                "id": str(consent.id),
                "consent_type": consent_type,
                "granted": granted,
                "timestamp": consent.created_at.isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to record consent: {e}")
            raise

    def get_user_consents(self, user_id: str) -> list[dict[str, Any]]:
        """Get all consent records for user"""
        from authentication.models import UserConsent

        consents = UserConsent.objects.filter(user_id=user_id).order_by("-created_at")

        return [
            {
                "id": str(c.id),
                "consent_type": c.consent_type,
                "granted": c.granted,
                "purpose": c.purpose,
                "created_at": c.created_at.isoformat(),
            }
            for c in consents
        ]

    def export_user_data(self, user_id: str) -> dict[str, Any]:
        """
        Export all user data (GDPR Right to Data Portability)

        Args:
            user_id: User identifier

        Returns:
            Complete user data export
        """
        from agents.models import Agent, Session
        from authentication.models import UserDataExport
        from Multi_model_Intelligence.models import ModelExecution

        try:
            user = User.objects.get(id=user_id)

            # Collect all user data
            user_data = {
                "user": {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "created_at": user.date_joined.isoformat(),
                    "role": user.role,
                    "subscription_tier": user.subscription_tier,
                },
                "agents": [
                    {
                        "id": str(a.id),
                        "name": a.name,
                        "type": a.type,
                        "created_at": a.created_at.isoformat(),
                    }
                    for a in Agent.objects.filter(owner=user)
                ],
                "sessions": [
                    {
                        "id": str(s.id),
                        "name": s.name,
                        "created_at": s.created_at.isoformat(),
                        "message_count": s.messages.count(),
                    }
                    for s in Session.objects.filter(user=user)
                ],
                "model_executions": [
                    {
                        "provider": e.provider,
                        "model": e.model_name,
                        "tokens_used": e.tokens_used,
                        "created_at": e.created_at.isoformat(),
                    }
                    for e in ModelExecution.objects.filter(user=user)[:100]
                ],
                "consents": self.get_user_consents(user_id),
            }

            # Create export record
            export = UserDataExport.objects.create(
                user=user, data=user_data, status="completed"
            )

            logger.info(f"Data export completed for user {user_id}")

            return {
                "export_id": str(export.id),
                "created_at": export.created_at.isoformat(),
                "data": user_data,
            }

        except Exception as e:
            logger.error(f"Data export failed: {e}")
            raise

    def delete_user_data(
        self, user_id: str, reason: str | None = None
    ) -> dict[str, Any]:
        """
        Delete all user data (GDPR Right to Erasure)

        Args:
            user_id: User identifier
            reason: Reason for deletion

        Returns:
            Deletion summary
        """
        from agents.models import Agent, Session
        from authentication.models import UserDeletionLog
        from Multi_model_Intelligence.models import ModelExecution

        try:
            user = User.objects.get(id=user_id)

            # Count data before deletion
            agents_count = Agent.objects.filter(owner=user).count()
            sessions_count = Session.objects.filter(user=user).count()
            executions_count = ModelExecution.objects.filter(user=user).count()

            # Create deletion log
            deletion_log = UserDeletionLog.objects.create(
                user_id=user_id,
                username=user.username,
                email=user.email,
                reason=reason,
                data_summary={
                    "agents": agents_count,
                    "sessions": sessions_count,
                    "executions": executions_count,
                },
            )

            # Delete related data
            Agent.objects.filter(owner=user).delete()
            Session.objects.filter(user=user).delete()
            ModelExecution.objects.filter(user=user).delete()

            # Anonymize or delete user
            user.email = f"deleted_{user.id}@anonymized.com"
            user.username = f"deleted_{user.id}"
            user.is_active = False
            user.save()

            logger.info(f"User data deleted: {user_id}")

            return {
                "deletion_id": str(deletion_log.id),
                "deleted_at": deletion_log.created_at.isoformat(),
                "summary": deletion_log.data_summary,
            }

        except Exception as e:
            logger.error(f"Data deletion failed: {e}")
            raise

    def anonymize_data(self, data: dict[str, Any], fields: list[str]) -> dict[str, Any]:
        """Anonymize specified fields in data"""
        anonymized = data.copy()

        for field in fields:
            if field in anonymized:
                anonymized[field] = self._anonymize_value(anonymized[field])

        return anonymized

    def _anonymize_value(self, value: Any) -> str:
        """Anonymize a single value"""
        if isinstance(value, str):
            if "@" in value:  # Email
                return f"***@{value.split('@')[1]}"
            return "***"
        return "***"

    def check_data_retention(self) -> dict[str, Any]:
        """Check and enforce data retention policies"""
        from datetime import timedelta

        retention_days = 365  # 1 year retention
        cutoff_date = timezone.now() - timedelta(days=retention_days)

        # Find old data
        from agents.models import Session

        old_sessions = Session.objects.filter(
            updated_at__lt=cutoff_date, is_active=False
        )

        count = old_sessions.count()

        # Delete old inactive sessions
        if count > 0:
            old_sessions.delete()
            logger.info(f"Deleted {count} old sessions per retention policy")

        return {"deleted_sessions": count, "cutoff_date": cutoff_date.isoformat()}

    def encrypt_sensitive_field(self, data: str) -> str:
        """Encrypt sensitive field"""
        return self.encryption.encrypt(data)

    def decrypt_sensitive_field(self, encrypted_data: str) -> str:
        """Decrypt sensitive field"""
        return self.encryption.decrypt(encrypted_data)


# Singleton instance
_gdpr_service = None


def get_gdpr_service() -> GDPRComplianceService:
    """Get or create GDPR compliance service singleton"""
    global _gdpr_service
    if _gdpr_service is None:
        _gdpr_service = GDPRComplianceService()
    return _gdpr_service
