"""HTTP client dependencies for API routes."""

from typing import Annotated, cast

import httpx
from fastapi import Depends, Request


def get_http_client(request: Request) -> httpx.AsyncClient:
    """Return the shared AsyncClient created during app startup."""
    state = request.app.state

    if not hasattr(state, "http_client"):
        state.http_client = httpx.AsyncClient()

    return cast(httpx.AsyncClient, state.http_client)


HttpClient = Annotated[httpx.AsyncClient, Depends(get_http_client)]
