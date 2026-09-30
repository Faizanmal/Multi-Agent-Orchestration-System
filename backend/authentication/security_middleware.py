"""
Enterprise-grade security middleware for API protection
"""
import hashlib
import logging
import time

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import status

logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """
    Advanced rate limiting middleware with multiple strategies
    - IP-based rate limiting
    - User-based rate limiting
    - Endpoint-specific limits
    - Sliding window algorithm
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limits = {
            'default': (100, 60),  # 100 requests per 60 seconds
            'auth': (5, 300),      # 5 requests per 5 minutes for auth endpoints
            'api': (1000, 3600),   # 1000 requests per hour for API
            'heavy': (10, 60),     # 10 requests per minute for heavy operations
        }
    
    def __call__(self, request):
        if not self._check_rate_limit(request):
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.',
                'retry_after': self._get_retry_after(request)
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        response = self.get_response(request)
        self._add_rate_limit_headers(request, response)
        return response
    
    def _get_rate_limit_key(self, request):
        """Generate unique rate limit key"""
        identifier = self._get_client_identifier(request)
        endpoint_type = self._get_endpoint_type(request.path)
        return f"rate_limit:{endpoint_type}:{identifier}"
    
    def _get_client_identifier(self, request):
        """Get unique client identifier (user ID or IP)"""
        if request.user and request.user.is_authenticated:
            return f"user_{request.user.id}"
        return self._get_client_ip(request)
    
    def _get_client_ip(self, request):
        """Extract client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _get_endpoint_type(self, path):
        """Determine endpoint type for rate limiting"""
        if '/authentication/' in path or '/login' in path or '/register' in path:
            return 'auth'
        elif '/agents/api/multimodal/' in path or '/agents/api/workflows/' in path:
            return 'heavy'
        elif '/api/' in path:
            return 'api'
        return 'default'
    
    def _check_rate_limit(self, request):
        """Check if request exceeds rate limit"""
        key = self._get_rate_limit_key(request)
        endpoint_type = self._get_endpoint_type(request.path)
        max_requests, window = self.rate_limits.get(endpoint_type, self.rate_limits['default'])
        
        current_time = time.time()
        window_key = f"{key}:window"
        
        # Get current window data
        window_data = cache.get(window_key, [])
        
        # Remove old requests outside the window
        window_data = [req_time for req_time in window_data if current_time - req_time < window]
        
        # Check if limit exceeded
        if len(window_data) >= max_requests:
            return False
        
        # Add current request
        window_data.append(current_time)
        cache.set(window_key, window_data, window + 10)
        
        return True
    
    def _get_retry_after(self, request):
        """Calculate retry after time in seconds"""
        key = self._get_rate_limit_key(request)
        endpoint_type = self._get_endpoint_type(request.path)
        _, window = self.rate_limits.get(endpoint_type, self.rate_limits['default'])
        
        window_key = f"{key}:window"
        window_data = cache.get(window_key, [])
        
        if window_data:
            oldest_request = min(window_data)
            retry_after = int(window - (time.time() - oldest_request))
            return max(retry_after, 1)
        return window
    
    def _add_rate_limit_headers(self, request, response):
        """Add rate limit information to response headers"""
        key = self._get_rate_limit_key(request)
        endpoint_type = self._get_endpoint_type(request.path)
        max_requests, window = self.rate_limits.get(endpoint_type, self.rate_limits['default'])
        
        window_key = f"{key}:window"
        window_data = cache.get(window_key, [])
        current_requests = len(window_data)
        
        response['X-RateLimit-Limit'] = str(max_requests)
        response['X-RateLimit-Remaining'] = str(max(0, max_requests - current_requests))
        response['X-RateLimit-Reset'] = str(int(time.time() + window))


class SecurityHeadersMiddleware:
    """
    Add enterprise security headers to all responses
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response['Content-Security-Policy'] = "default-src 'self'"
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response


class AuditLoggingMiddleware:
    """
    Comprehensive audit logging for security and compliance
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        # Capture request details
        audit_data = {
            'timestamp': timezone.now().isoformat(),
            'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            'user_id': str(request.user.id) if request.user.is_authenticated else None,
            'method': request.method,
            'path': request.path,
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'referer': request.META.get('HTTP_REFERER', ''),
        }
        
        # Process request
        response = self.get_response(request)
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Add response details
        audit_data.update({
            'status_code': response.status_code,
            'processing_time_ms': round(processing_time, 2),
        })
        
        # Log sensitive operations
        if self._is_sensitive_operation(request):
            logger.warning(f"AUDIT: Sensitive operation - {audit_data}")
        
        # Log failed authentication attempts
        if response.status_code == 401 or response.status_code == 403:
            logger.warning(f"AUDIT: Unauthorized access attempt - {audit_data}")
        
        # Log all API requests in production
        if not settings.DEBUG and '/api/' in request.path:
            logger.info(f"AUDIT: API request - {audit_data}")
        
        return response
    
    def _get_client_ip(self, request):
        """Extract client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _is_sensitive_operation(self, request):
        """Determine if operation is sensitive"""
        sensitive_paths = [
            '/admin/', '/authentication/', '/api-keys/',
            '/delete', '/remove', '/destroy'
        ]
        sensitive_methods = ['DELETE', 'PUT', 'PATCH']
        
        return any(path in request.path for path in sensitive_paths) or \
               request.method in sensitive_methods


class IPWhitelistMiddleware:
    """
    IP whitelisting for admin and sensitive endpoints
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.whitelist = getattr(settings, 'IP_WHITELIST', [])
        self.protected_paths = ['/admin/', '/api/system/']
    
    def __call__(self, request):
        if self._is_protected_path(request.path):
            client_ip = self._get_client_ip(request)
            if self.whitelist and client_ip not in self.whitelist:
                logger.warning(f"IP whitelist violation: {client_ip} attempted to access {request.path}")
                return JsonResponse({
                    'error': 'Access denied',
                    'message': 'Your IP address is not authorized to access this resource'
                }, status=status.HTTP_403_FORBIDDEN)
        
        return self.get_response(request)
    
    def _is_protected_path(self, path):
        """Check if path requires IP whitelisting"""
        return any(protected in path for protected in self.protected_paths)
    
    def _get_client_ip(self, request):
        """Extract client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RequestIDMiddleware:
    """
    Add unique request ID for tracking and debugging
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Generate unique request ID
        request_id = hashlib.sha256(
            f"{time.time()}{request.path}{id(request)}".encode()
        ).hexdigest()[:16]
        
        request.request_id = request_id
        
        response = self.get_response(request)
        response['X-Request-ID'] = request_id
        
        return response
