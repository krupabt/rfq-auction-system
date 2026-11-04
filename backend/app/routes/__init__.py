from fastapi import APIRouter
from .auth import router as auth_router
from .rfq import router as rfq_router
from .auction import router as auction_router
from .bid import router as bid_router
from .dashboard import router as dashboard_router
from .reports import router as reports_router
from .websocket import router as websocket_router

__all__ = [
    "auth_router",
    "rfq_router",
    "auction_router",
    "bid_router",
    "dashboard_router",
    "reports_router",
    "websocket_router",
]
