from enum import StrEnum


class ErrorCode(StrEnum):
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"


class BusinessLogicError(Exception):
    """Exception raised for business logic errors."""

    def __init__(self, message: str, error_code: ErrorCode):
        self.message = message
        self.error_code = error_code
        super().__init__(message)
