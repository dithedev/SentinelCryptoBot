"""FastAPI application lifespan hooks."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI


@asynccontextmanager
async def app_lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Manage shared HTTP resources for the API process."""
    async with httpx.AsyncClient() as http_client:
        application.state.http_client = http_client
        yield
