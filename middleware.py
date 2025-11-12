"""
Middleware for request logging, monitoring, and security
"""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import logging

from logging_config import log_request, log_security_event, get_logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses"""
    
    def __init__(self, app, log_level: str = "INFO"):
        super().__init__(app)
        self.logger = get_logger("middleware")
        self.log_level = getattr(logging, log_level.upper())
        
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Extract request info
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Log request start
        self.logger.info(
            f"Request started: {method} {path}",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "client_ip": client_ip,
                "user_agent": user_agent,
                "event": "request_start"
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Extract user ID if available
            user_id = getattr(request.state, 'user_id', None)
            
            # Log request completion
            log_request(
                method=method,
                path=path,
                status_code=response.status_code,
                response_time=response_time,
                user_id=user_id,
                request_id=request_id
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate response time for failed requests
            response_time = time.time() - start_time
            
            # Log failed request
            self.logger.error(
                f"Request failed: {method} {path} - {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "client_ip": client_ip,
                    "response_time": response_time,
                    "event": "request_error"
                },
                exc_info=True
            )
            
            # Re-raise the exception
            raise


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for security monitoring and headers"""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = get_logger("security")
        
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        # Security checks
        await self._check_suspicious_requests(request)
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        self._add_security_headers(response)
        
        return response
    
    async def _check_suspicious_requests(self, request: Request) -> None:
        """Check for suspicious request patterns"""
        
        # Check for common attack patterns in URL
        suspicious_patterns = [
            "../", "..\\", "<script", "javascript:", "vbscript:",
            "onload=", "onerror=", "eval(", "alert(", "confirm(",
            "prompt(", "document.cookie", "document.write"
        ]
        
        url_path = request.url.path.lower()
        query_string = str(request.url.query).lower()
        
        for pattern in suspicious_patterns:
            if pattern in url_path or pattern in query_string:
                log_security_event(
                    event_type="SUSPICIOUS_REQUEST",
                    details={
                        "pattern": pattern,
                        "url": str(request.url),
                        "method": request.method,
                        "client_ip": request.client.host if request.client else "unknown",
                        "user_agent": request.headers.get("user-agent", "unknown")
                    },
                    severity="WARNING"
                )
                break
        
        # Check for excessive header size (potential attack)
        total_header_size = sum(len(k) + len(v) for k, v in request.headers.items())
        if total_header_size > 8192:  # 8KB limit
            log_security_event(
                event_type="LARGE_HEADERS",
                details={
                    "header_size": total_header_size,
                    "url": str(request.url),
                    "client_ip": request.client.host if request.client else "unknown"
                },
                severity="WARNING"
            )
    
    def _add_security_headers(self, response: Response) -> None:
        """Add security headers to response"""
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy (basic)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        # HSTS (only in production)
        if not response.headers.get("debug", False):
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.client_requests = {}  # In production, use Redis
        self.logger = get_logger("rate_limit")
        
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean old entries (older than 1 minute)
        self._cleanup_old_entries(current_time)
        
        # Check rate limit
        if client_ip in self.client_requests:
            request_times = self.client_requests[client_ip]
            recent_requests = [t for t in request_times if current_time - t < 60]
            
            if len(recent_requests) >= self.requests_per_minute:
                # Rate limit exceeded
                log_security_event(
                    event_type="RATE_LIMIT_EXCEEDED",
                    details={
                        "client_ip": client_ip,
                        "requests_in_minute": len(recent_requests),
                        "limit": self.requests_per_minute,
                        "url": str(request.url)
                    },
                    severity="WARNING"
                )
                
                from error_handling import RateLimitError
                raise RateLimitError("Rate limit exceeded. Please try again later.", retry_after=60)
            
            # Update request times
            recent_requests.append(current_time)
            self.client_requests[client_ip] = recent_requests
        else:
            # First request from this IP
            self.client_requests[client_ip] = [current_time]
        
        return await call_next(request)
    
    def _cleanup_old_entries(self, current_time: float) -> None:
        """Remove old entries to prevent memory leaks"""
        clients_to_remove = []
        
        for client_ip, request_times in self.client_requests.items():
            # Keep only requests from the last minute
            recent_requests = [t for t in request_times if current_time - t < 60]
            
            if recent_requests:
                self.client_requests[client_ip] = recent_requests
            else:
                clients_to_remove.append(client_ip)
        
        for client_ip in clients_to_remove:
            del self.client_requests[client_ip]


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """Middleware for health monitoring"""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = get_logger("health")
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        self.request_count += 1
        
        try:
            response = await call_next(request)
            
            # Count errors
            if response.status_code >= 500:
                self.error_count += 1
                
            return response
            
        except Exception as e:
            self.error_count += 1
            raise
    
    def get_health_stats(self) -> dict:
        """Get current health statistics"""
        uptime = time.time() - self.start_time
        error_rate = (self.error_count / max(self.request_count, 1)) * 100
        
        return {
            "uptime_seconds": round(uptime, 2),
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "error_rate_percent": round(error_rate, 2),
            "status": "healthy" if error_rate < 5 else "degraded" if error_rate < 20 else "unhealthy"
        }