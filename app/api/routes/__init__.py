"""API routes package."""

from app.api.routes.products import router as products_router
from app.api.routes.users import router as users_router

__all__ = ["products_router", "users_router"]
