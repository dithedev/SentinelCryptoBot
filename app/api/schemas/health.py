"""Pydantic schemas for health check endpoints."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Simple liveness response."""

    status: str


class ReadinessResponse(BaseModel):
    """Readiness response with dependency statuses."""

    status: str
    database: str
