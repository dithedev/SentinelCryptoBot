"""Deprecated public alert routes.

User alert management must not be exposed through public endpoints that accept
telegram_id as query or body input.

Alerts are managed only through protected Telegram Mini App endpoints in
app.api.routes.miniapp, where the backend derives the current user from signed
Telegram WebApp initData.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/alerts", tags=["alerts"])

__all__ = ("router",)
