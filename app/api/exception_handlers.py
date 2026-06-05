"""FastAPI exception handlers for domain and integration errors."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.api.texts import (
    ALERT_NOT_FOUND_MESSAGE,
    AUTHENTICATION_FAILED_MESSAGE,
    RISK_CHECK_PROVIDER_ERROR_MESSAGE,
    VALIDATION_ERROR_MESSAGE,
)
from app.core.exceptions import (
    AlertNotFoundError,
    AuthenticationError,
    NotFoundError,
    PriceProviderError,
    SecurityProviderError,
    UserNotFoundError,
    ValidationError,
)


def register_exception_handlers(application: FastAPI) -> None:
    """Attach shared exception handlers to the FastAPI app."""
    application.add_exception_handler(
        ValidationError,
        _validation_error_handler,
    )
    application.add_exception_handler(
        AuthenticationError,
        _authentication_error_handler,
    )
    application.add_exception_handler(
        AlertNotFoundError,
        _alert_not_found_handler,
    )
    application.add_exception_handler(
        UserNotFoundError,
        _not_found_handler,
    )
    application.add_exception_handler(
        NotFoundError,
        _not_found_handler,
    )
    application.add_exception_handler(
        PriceProviderError,
        _price_provider_error_handler,
    )
    application.add_exception_handler(
        SecurityProviderError,
        _security_provider_error_handler,
    )


async def _validation_error_handler(
    _request: Request,
    exc: Exception,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc) or VALIDATION_ERROR_MESSAGE},
    )


async def _authentication_error_handler(
    _request: Request,
    exc: Exception,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": str(exc) or AUTHENTICATION_FAILED_MESSAGE},
    )


async def _alert_not_found_handler(
    _request: Request,
    _exc: Exception,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": ALERT_NOT_FOUND_MESSAGE},
    )


async def _not_found_handler(
    _request: Request,
    exc: Exception,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc) or "Resource not found."},
    )


async def _price_provider_error_handler(
    _request: Request,
    _exc: Exception,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": "Price provider is temporarily unavailable."},
    )


async def _security_provider_error_handler(
    _request: Request,
    _exc: Exception,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": RISK_CHECK_PROVIDER_ERROR_MESSAGE},
    )
