from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes.products import router as products_router
from app.api.routes.users import router as users_router
from app.core.config import settings
from app.database.session import init_db

# Static files directory path
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup: initialize database tables
    try:
        init_db()
    except Exception as exc:
        print(f"Warning during DB init on startup: {exc}")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Interactive UI & Production API for tracking e-commerce prices with automated scraping and price drop alerts.",
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files (CSS, JS, assets)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Include API Routers under /api/v1
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(products_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Frontend"])
def serve_frontend_ui():
    """Serve the interactive web UI dashboard."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "health_check": "/health",
    }


@app.get("/health", tags=["Health"], status_code=status.HTTP_200_OK)
def health_check():
    """Service health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


@app.get("/info", tags=["General"])
def api_info():
    """API metadata and documentation endpoints."""
    return {
        "title": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "api_v1_prefix": settings.API_V1_STR,
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "openapi_url": app.openapi_url,
    }