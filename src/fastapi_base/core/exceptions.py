from enum import StrEnum


class ErrorCode(StrEnum):
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    COLUMN_NOT_FOUND = "COLUMN_NOT_FOUND"
    NOT_FOUND = "NOT_FOUND"
    DB_ERROR = "DB_ERROR"
    PASSWORD_POLICY_VIOLATION = "PASSWORD_POLICY_VIOLATION"
    UNAUTHORIZED = "UNAUTHORIZED"
    EMAIL_NOT_VERIFIED = "EMAIL_NOT_VERIFIED"
    INVALID_TOKEN = "INVALID_TOKEN"
    WEAK_PASSWORD = "WEAK_PASSWORD"
    USER_LOCKED = "USER_LOCKED"
    PASSWORD_NOT_MATCH = "PASSWORD_NOT_MATCH"
    FORBIDDEN = "FORBIDDEN"
    RATE_LIMITED = "RATE_LIMITED"
    VALIDATION_ERROR = "VALIDATION_ERROR"


class BusinessLogicError(Exception):
    """Exception raised for business logic errors."""

    def __init__(self, message: str, error_code: ErrorCode):
        self.message = message
        self.error_code = error_code
        super().__init__(message)
