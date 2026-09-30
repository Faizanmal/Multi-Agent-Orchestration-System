from datetime import timezone

"""
Request Logging and Monitoring Middleware
"""
import json
import logging
import time
from datetime import datetime

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all HTTP requests and responses
    """
    
    def process_request(self, request):
        """Log incoming request"""
        request._start_time = time.time()
        
        # Log request details
        logger.info(f"Request: {request.method} {request.path}")
        logger.debug(f"Headers: {dict(request.headers)}")
        
    
    def process_response(self, request, response):
        """Log outgoing response"""
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            
            # Log response details
            logger.info(
                f"Response: {request.method} {request.path} "
                f"[{response.status_code}] {duration:.3f}s"
            )
            
            # Add response time header
            response['X-Response-Time'] = f"{duration:.3f}s"
        
        return response
    
    def process_exception(self, request, exception):
        """Log exceptions"""
        logger.error(
            f"Exception: {request.method} {request.path} - {exception!s}"
        )


class APIMetricsMiddleware(MiddlewareMixin):
    """
    Middleware to collect API metrics
    """
    
    def process_request(self, request):
        """Start timing request"""
        request._metrics_start = time.time()
    
    def process_response(self, request, response):
        """Collect metrics"""
        if hasattr(request, '_metrics_start'):
            duration = time.time() - request._metrics_start
            
            # Store metrics (can be sent to monitoring system)
            metrics = {
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'duration_ms': round(duration * 1000, 2),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'user': request.user.username if request.user.is_authenticated else 'anonymous'
            }
            
            # Log slow requests
            if duration > 1.0:  # Slower than 1 second
                logger.warning(f"Slow request detected: {json.dumps(metrics)}")
            
            # Add metrics to response headers
            response['X-Request-Duration-Ms'] = str(metrics['duration_ms'])
        
        return response


class ErrorTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to track and log errors
    """
    
    def process_exception(self, request, exception):
        """Track exceptions"""
        error_data = {
            'type': type(exception).__name__,
            'message': str(exception),
            'path': request.path,
            'method': request.method,
            'user': request.user.username if request.user.is_authenticated else 'anonymous',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        logger.error(f"Error tracked: {json.dumps(error_data)}")
        
        # Could send to error tracking service (Sentry, etc.)
        if hasattr(settings, 'SENTRY_DSN'):
            # Send to Sentry
            pass
        


class CORSDebugMiddleware(MiddlewareMixin):
    """
    Middleware to debug CORS issues
    """
    
    def process_request(self, request):
        """Log CORS-related headers"""
        if settings.DEBUG:
            origin = request.headers.get('Origin')
            if origin:
                logger.debug(f"CORS Request - Origin: {origin}, Path: {request.path}")
    
    def process_response(self, request, response):
        """Log CORS response headers"""
        if settings.DEBUG:
            cors_headers = {
                k: v for k, v in response.items()
                if k.startswith('Access-Control-')
            }
            if cors_headers:
                logger.debug(f"CORS Response Headers: {cors_headers}")
        return response
