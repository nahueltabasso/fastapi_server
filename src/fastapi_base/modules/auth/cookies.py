from datetime import UTC, datetime

from fastapi import Request, Response

from fastapi_base.core.config import get_settings
from fastapi_base.core.exceptions import BusinessLogicError, ErrorCode
from fastapi_base.modules.auth.schemas import RefreshDTO, TokenResponseDTO
from fastapi_base.modules.auth.sessions import TokenPair

settings = get_settings()
REFRESH_COOKIE_PATH = f"{settings.api_prefix}/auth/"
CSRF_HEADER_VALUE = "fetch"


def deliver_tokens(pair: TokenPair, response: Response) -> TokenResponseDTO:
    """Delivers the access and refresh tokens to the client.

    For mobile clients, the tokens are returned in the response body.
    For web clients, the refresh token is set as an HTTP-only cookie.

    Args:
        pair (TokenPair): The token pair containing access and refresh tokens.
        response (Response): The FastAPI response object.

    Returns:
        TokenResponseDTO: The response DTO containing the access token and expiration info.
    """
    if pair.client_type == "mobile":
        return TokenResponseDTO(
            access_token=pair.access_token,
            expires_in=pair.expires_in,
            refresh_token=pair.refresh_token,
        )
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=pair.refresh_token,
        max_age=int((pair.refresh_expires_at - datetime.now(UTC)).total_seconds()),
        httponly=True,
        secure=settings.env != "local",
        samesite="strict",
        path=REFRESH_COOKIE_PATH,
    )
    return TokenResponseDTO(
        access_token=pair.access_token,
        expires_in=pair.expires_in,
    )


def clear_refresh_cookie(response: Response) -> None:
    """Delete a refresh token cookie."""
    response.delete_cookie(
        settings.refresh_cookie_name,
        path=REFRESH_COOKIE_PATH,
    )


def read_refresh_token(request: Request, body: RefreshDTO | None) -> str:
    """Read a refresh token from the request."""
    cookie = request.cookies.get(settings.refresh_cookie_name)
    if cookie is not None:
        if request.headers.get("x-requested-with") != CSRF_HEADER_VALUE:
            raise BusinessLogicError(
                message="Missing CSRF header", error_code=ErrorCode.UNAUTHORIZED
            )
        return cookie
    if body is not None:
        return body.refresh_token.get_secret_value()
    raise BusinessLogicError(
        message="Missing refresh token", error_code=ErrorCode.UNAUTHORIZED
    )
