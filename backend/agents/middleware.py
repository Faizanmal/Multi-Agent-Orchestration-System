import logging
import time

from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class PerformanceTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to track performance metrics for agent operations
    """

    def process_request(self, request):
        """Record the start time of the request"""
        request.start_time = time.time()

    def process_response(self, request, response):
        """Calculate and log the response time"""
        if hasattr(request, "start_time"):
            duration = time.time() - request.start_time

            # Log performance metrics
            logger.info(
                f"Request Performance - "
                f"Method: {request.method}, "
                f"Path: {request.path}, "
                f"Status: {response.status_code}, "
                f"Duration: {duration:.4f}s"
            )

            # Add performance headers for debugging
            response["X-Response-Time"] = f"{duration:.4f}s"

            # For agent-related endpoints, log additional metrics
            if "/agents/" in request.path:
                logger.info(
                    f"Agent Request Performance - "
                    f"Path: {request.path}, "
                    f"Duration: {duration:.4f}s"
                )

        return response

    def process_exception(self, request, exception):
        """Log exceptions with performance context"""
        if hasattr(request, "start_time"):
            duration = time.time() - request.start_time
            logger.error(
                f"Request Exception - "
                f"Method: {request.method}, "
                f"Path: {request.path}, "
                f"Duration: {duration:.4f}s, "
                f"Exception: {exception!s}"
            )
