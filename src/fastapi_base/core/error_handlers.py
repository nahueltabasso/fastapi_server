from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from fastapi_base.core.exceptions import BusinessLogicError, ErrorCode

ERROR_STATUS: dict[ErrorCode, int] = {
    ErrorCode.INVALID_CREDENTIALS: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.COLUMN_NOT_FOUND: status.HTTP_400_BAD_REQUEST,
    ErrorCode.DB_ERROR: status.HTTP_409_CONFLICT,
    ErrorCode.NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.PASSWORD_POLICY_VIOLATION: status.HTTP_400_BAD_REQUEST,
    ErrorCode.UNAUTHORIZED: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.EMAIL_NOT_VERIFIED: status.HTTP_403_FORBIDDEN,
    ErrorCode.INVALID_TOKEN: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.WEAK_PASSWORD: status.HTTP_422_UNPROCESSABLE_ENTITY,
    ErrorCode.PASSWORD_NOT_MATCH: status.HTTP_400_BAD_REQUEST,
}


def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exceptions handlers for the FastAPI Application."""

    @app.exception_handler(BusinessLogicError)
    async def business_exception_handler(
        request: Request, exc: BusinessLogicError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=ERROR_STATUS.get(exc.error_code, status.HTTP_400_BAD_REQUEST),
            content={
                "status": ERROR_STATUS.get(exc.error_code, status.HTTP_400_BAD_REQUEST),
                "message": exc.message,
                "error_code": exc.error_code,
                "method": request.method,
                "url": str(request.url.path),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal server error",
                "error_code": "INTERNAL_SERVER_ERROR",
                "method": request.method,
                "url": str(request.url.path),
            },
        )
