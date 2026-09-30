"""
GDPR Compliance Models
"""

import uuid

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class UserConsent(models.Model):
    """Track user consent for GDPR compliance"""
    CONSENT_TYPES = [  # noqa: RUF012
        ('necessary', 'Necessary'),
        ('analytics', 'Analytics'),
        ('marketing', 'Marketing'),
        ('personalization', 'Personalization'),
        ('third_party', 'Third Party'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='consents')
    
    # Consent details
    consent_type = models.CharField(max_length=50, choices=CONSENT_TYPES)
    granted = models.BooleanField()
    purpose = models.TextField()
    
    # Tracking
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'user_consents'
        ordering = ['-created_at']  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=['user', 'consent_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.consent_type}: {self.granted}"


class UserDataExport(models.Model):
    """Track data export requests (GDPR Right to Data Portability)"""
    STATUS_CHOICES = [  # noqa: RUF012
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='data_exports')
    
    # Export details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    data = models.JSONField(null=True, blank=True)
    file_path = models.CharField(max_length=500, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'user_data_exports'
        ordering = ['-created_at']  # noqa: RUF012
    
    def __str__(self):
        return f"Export for {self.user.username} - {self.status}"


class UserDeletionLog(models.Model):
    """Log user data deletions (GDPR Right to Erasure)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # User info (stored after deletion)
    user_id = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    email = models.EmailField()
    
    # Deletion details
    reason = models.TextField(blank=True)
    requested_by = models.CharField(max_length=100, default='user')
    data_summary = models.JSONField(default=dict)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_deletion_logs'
        ordering = ['-created_at']  # noqa: RUF012
    
    def __str__(self):
        return f"Deletion: {self.username} at {self.created_at}"


class DataProcessingActivity(models.Model):
    """Record of data processing activities (GDPR Article 30)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Activity details
    activity_name = models.CharField(max_length=200)
    purpose = models.TextField()
    legal_basis = models.CharField(max_length=100)
    data_categories = models.JSONField(default=list)
    data_subjects = models.JSONField(default=list)
    recipients = models.JSONField(default=list)
    
    # Technical and organizational measures
    security_measures = models.TextField()
    retention_period = models.CharField(max_length=200)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'data_processing_activities'
    
    def __str__(self):
        return self.activity_name
