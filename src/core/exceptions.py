from typing import Any, Dict, Optional


class B2BMemoryException(Exception):
    """Base exception for B2B Memory system"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class ValidationError(B2BMemoryException):
    """Raised when input validation fails"""
    pass


class StorageError(B2BMemoryException):
    """Raised when storage operations fail"""
    pass


class ProcessingError(B2BMemoryException):
    """Raised when data processing fails"""
    pass


class ExternalServiceError(B2BMemoryException):
    """Raised when external service calls fail"""
    pass


class AuthenticationError(B2BMemoryException):
    """Raised when authentication fails"""
    pass


class RateLimitError(B2BMemoryException):
    """Raised when rate limit is exceeded"""
    pass
