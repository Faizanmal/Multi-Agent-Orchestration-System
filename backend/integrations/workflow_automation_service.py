from datetime import timezone

"""
Zapier and Make.com Integration Service
Enables workflow automation across 5000+ apps
"""

import hashlib
import hmac
import json
import logging
import os
from datetime import datetime
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class ZapierService:
    """Service for Zapier integration"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'ZAPIER_API_KEY', os.getenv('ZAPIER_API_KEY'))
        self.webhook_secret = getattr(settings, 'ZAPIER_WEBHOOK_SECRET', os.getenv('ZAPIER_WEBHOOK_SECRET'))
        self.enabled = bool(self.api_key)
    
    def trigger_zap(self, webhook_url: str, data: dict[str, Any]) -> dict[str, Any]:
        """
        Trigger a Zap via webhook
        
        Args:
            webhook_url: Zapier webhook URL
            data: Data to send
            
        Returns:
            Response data
        """
        try:
            response = requests.post(
                webhook_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            response.raise_for_status()
            
            logger.info(f"Zap triggered successfully: {webhook_url[:50]}...")
            
            return {
                'success': True,
                'status_code': response.status_code,
                'response': response.text
            }
            
        except requests.RequestException as e:
            logger.error(f"Zap trigger failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Zapier webhook signature"""
        if not self.webhook_secret:
            return True  # Skip verification if no secret configured
        
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def create_webhook_subscription(
        self,
        target_url: str,
        event_type: str,
        filters: dict | None = None
    ) -> dict[str, Any]:
        """
        Create webhook subscription for Zapier triggers
        
        Args:
            target_url: URL to send webhooks to
            event_type: Event type to subscribe to
            filters: Optional filters
            
        Returns:
            Subscription details
        """
        if not self.enabled:
            return {'error': 'Zapier not configured'}
        
        # Store subscription in database
        from webhooks.models import Webhook
        
        try:
            # Create webhook for Zapier integration
            webhook = Webhook.objects.create(
                name=f"Zapier - {event_type}",
                url=target_url,
                event_types=[event_type],
                is_active=True,
                description=f"Zapier integration for {event_type}"
            )
            
            return {
                'success': True,
                'subscription_id': str(webhook.id),
                'event_type': event_type,
                'target_url': target_url
            }
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to create webhook subscription: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class MakeService:
    """Service for Make.com (formerly Integromat) integration"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'MAKE_API_KEY', os.getenv('MAKE_API_KEY'))
        self.webhook_secret = getattr(settings, 'MAKE_WEBHOOK_SECRET', os.getenv('MAKE_WEBHOOK_SECRET'))
        self.enabled = bool(self.api_key)
    
    def trigger_scenario(self, webhook_url: str, data: dict[str, Any]) -> dict[str, Any]:
        """
        Trigger a Make scenario via webhook
        
        Args:
            webhook_url: Make webhook URL
            data: Data to send
            
        Returns:
            Response data
        """
        try:
            # Add timestamp and metadata
            payload = {
                **data,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'source': 'MultiAgentSystem'
            }
            
            response = requests.post(
                webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            response.raise_for_status()
            
            logger.info("Make scenario triggered successfully")
            
            return {
                'success': True,
                'status_code': response.status_code,
                'response': response.json() if response.content else {}
            }
            
        except requests.RequestException as e:
            logger.error(f"Make scenario trigger failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Make webhook signature"""
        if not self.webhook_secret:
            return True
        
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def execute_rpc_call(
        self,
        module: str,
        action: str,
        parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute Make RPC call
        
        Args:
            module: Module name
            action: Action to perform
            parameters: Action parameters
            
        Returns:
            Result
        """
        if not self.enabled:
            return {'error': 'Make not configured'}
        
        try:
            url = "https://www.make.com/api/v2/rpc"
            
            payload = {
                'module': module,
                'action': action,
                'parameters': parameters
            }
            
            headers = {
                'Authorization': f'Token {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            return {
                'success': True,
                'result': response.json()
            }
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Make RPC call failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class WorkflowAutomationService:
    """Unified service for workflow automation platforms"""
    
    def __init__(self):
        self.zapier = ZapierService()
        self.make = MakeService()
    
    def trigger_automation(
        self,
        platform: str,
        webhook_url: str,
        event_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Trigger automation on specified platform
        
        Args:
            platform: 'zapier' or 'make'
            webhook_url: Webhook URL
            event_data: Event data
            
        Returns:
            Result
        """
        if platform.lower() == 'zapier':
            return self.zapier.trigger_zap(webhook_url, event_data)
        elif platform.lower() == 'make':
            return self.make.trigger_scenario(webhook_url, event_data)
        else:
            return {'error': f'Unsupported platform: {platform}'}
    
    def handle_incoming_webhook(
        self,
        platform: str,
        payload: bytes,
        signature: str
    ) -> dict[str, Any]:
        """
        Handle incoming webhook from automation platform
        
        Args:
            platform: Platform name
            payload: Webhook payload
            signature: Signature header
            
        Returns:
            Verification result
        """
        if platform.lower() == 'zapier':
            verified = self.zapier.verify_webhook_signature(payload, signature)
        elif platform.lower() == 'make':
            verified = self.make.verify_webhook_signature(payload, signature)
        else:
            return {'verified': False, 'error': 'Unknown platform'}
        
        return {
            'verified': verified,
            'payload': json.loads(payload) if verified else None
        }
    
    def get_available_platforms(self) -> list[dict[str, Any]]:
        """Get list of configured automation platforms"""
        platforms = []
        
        if self.zapier.enabled:
            platforms.append({
                'name': 'Zapier',
                'id': 'zapier',
                'enabled': True,
                'apps_count': 5000
            })
        
        if self.make.enabled:
            platforms.append({
                'name': 'Make',
                'id': 'make',
                'enabled': True,
                'apps_count': 1500
            })
        
        return platforms


# Singleton instance
_automation_service = None

def get_automation_service() -> WorkflowAutomationService:
    """Get or create workflow automation service singleton"""
    global _automation_service
    if _automation_service is None:
        _automation_service = WorkflowAutomationService()
    return _automation_service
