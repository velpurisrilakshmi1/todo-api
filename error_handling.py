"""
Error handling and custom exceptions for Todo API
Provides consistent error responses and proper HTTP status codes
"""
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
from typing import Any, Dict, Optional
import traceback
import uuid

from logging_config import log_error, log_security_event


class TodoAPIException(Exception):
    """Base exception for Todo API"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(TodoAPIException):
    """Authentication related errors"""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_FAILED",
            details=details
        )


class AuthorizationError(TodoAPIException):
    """Authorization related errors"""
    
    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="ACCESS_DENIED",
            details=details
        )


class ValidationError(TodoAPIException):
    """Input validation errors (custom business logic validation)"""
    
    def __init__(self, message: str, field: str = None, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        if field:
            error_details["field"] = field
            
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="VALIDATION_ERROR",
            details=error_details
        )


class SchemaValidationError(TodoAPIException):
    """Schema validation errors (Pydantic/FastAPI automatic validation)"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="SCHEMA_VALIDATION_ERROR",
            details=details or {}
        )


class NotFoundError(TodoAPIException):
    """Resource not found errors"""
    
    def __init__(self, resource: str, resource_id: str = None, details: Optional[Dict[str, Any]] = None):
        message = f"{resource} not found"
        if resource_id:
            message += f" with ID: {resource_id}"
            
        error_details = details or {}
        error_details["resource"] = resource
        if resource_id:
            error_details["resource_id"] = resource_id
            
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
            details=error_details
        )


class ConflictError(TodoAPIException):
    """Resource conflict errors"""
    
    def __init__(self, message: str, resource: str = None, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        if resource:
            error_details["resource"] = resource
            
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="RESOURCE_CONFLICT",
            details=error_details
        )


class RateLimitError(TodoAPIException):
    """Rate limiting errors"""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
            
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details
        )


class DatabaseError(TodoAPIException):
    """Database related errors"""
    
    def __init__(self, message: str = "Database operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR",
            details=details
        )


def create_error_response(
    error: TodoAPIException,
    request: Request = None,
    include_details: bool = True
) -> JSONResponse:
    """Create standardized error response"""
    
    # Generate request ID for tracking
    request_id = str(uuid.uuid4())
    
    # Basic error response
    # Use FastAPI compatible format for client compatibility
    error_response = {
        "detail": error.message,
        "error": {
            "code": error.error_code,
            "message": error.message,
            "request_id": request_id
        }
    }
    
    # Add details in development or for client errors (4xx)
    if include_details and (error.status_code < 500 or include_details):
        if error.details:
            error_response["error"]["details"] = error.details
    
    # Log error with context
    context = {
        "error_code": error.error_code,
        "status_code": error.status_code,
        "request_id": request_id
    }
    
    if request:
        context.update({
            "method": request.method,
            "url": str(request.url),
            "user_agent": request.headers.get("user-agent"),
            "client_ip": request.client.host if request.client else None
        })
    
    # Log based on severity
    if error.status_code >= 500:
        log_error(error, context, request_id=request_id)
    elif error.status_code == 401 or error.status_code == 403:
        log_security_event(
            event_type=error.error_code,
            details=context,
            severity="WARNING"
        )
    else:
        logging.getLogger("todo_api").warning(
            f"Client error: {error.message}",
            extra=context
        )
    
    return JSONResponse(
        status_code=error.status_code,
        content=error_response
    )


async def todo_api_exception_handler(request: Request, exc: TodoAPIException) -> JSONResponse:
    """Handle TodoAPI custom exceptions"""
    return create_error_response(exc, request)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions"""
    
    # Convert to TodoAPI exception
    if exc.status_code == 401:
        todo_exc = AuthenticationError(exc.detail)
    elif exc.status_code == 403:
        todo_exc = AuthorizationError(exc.detail)
    elif exc.status_code == 404:
        todo_exc = NotFoundError("Resource", details={"original_detail": exc.detail})
    elif exc.status_code == 409:
        todo_exc = ConflictError(exc.detail)
    elif 400 <= exc.status_code < 500:
        todo_exc = ValidationError(exc.detail)
    else:
        todo_exc = TodoAPIException(
            message="Internal server error",
            status_code=exc.status_code,
            error_code="HTTP_ERROR",
            details={"original_detail": exc.detail}
        )
    
    return create_error_response(todo_exc, request)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors"""
    
    # Extract validation details
    validation_errors = []
    for error in exc.errors():
        field_path = " -> ".join([str(loc) for loc in error["loc"]])
        validation_errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"]
        })
    
    todo_exc = SchemaValidationError(
        message="Request validation failed",
        details={
            "validation_errors": validation_errors,
            "invalid_fields": len(validation_errors)
        }
    )
    
    return create_error_response(todo_exc, request)


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    
    # Generate request ID for tracking
    request_id = str(uuid.uuid4())
    
    # Log the full exception
    context = {
        "request_id": request_id,
        "method": request.method,
        "url": str(request.url),
        "exception_type": type(exc).__name__,
        "user_agent": request.headers.get("user-agent"),
        "client_ip": request.client.host if request.client else None
    }
    
    log_error(exc, context, request_id=request_id)
    
    # Create generic error response (don't expose internal details)
    error_response = {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
            "request_id": request_id
        }
    }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )


def setup_error_handlers(app) -> None:
    """Setup all error handlers for the FastAPI app"""
    
    # Custom exception handlers
    app.add_exception_handler(TodoAPIException, todo_api_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)


# Utility functions for raising common errors
def raise_not_found(resource: str, resource_id: str = None) -> None:
    """Raise a not found error"""
    raise NotFoundError(resource, resource_id)


def raise_validation_error(message: str, field: str = None) -> None:
    """Raise a validation error"""
    raise ValidationError(message, field)


def raise_conflict_error(message: str, resource: str = None) -> None:
    """Raise a conflict error"""
    raise ConflictError(message, resource)


def raise_auth_error(message: str = "Authentication required") -> None:
    """Raise an authentication error"""
    raise AuthenticationError(message)


def raise_permission_error(message: str = "Permission denied") -> None:
    """Raise an authorization error"""
    raise AuthorizationError(message)