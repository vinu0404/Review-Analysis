from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
import logging
import sys
from pathlib import Path
import uvicorn
from app.config import get_settings
from app.database import connect_to_mongodb, close_mongodb_connection
from app.routes import user_router, admin_router
from app.utils.error_handlers import setup_exception_handlers
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting AI Feedback System...")
    await connect_to_mongodb()
    logger.info("Application started successfully")
    
    yield
    logger.info("Shutting down...")
    await close_mongodb_connection()
    logger.info("Application shutdown complete")

app = FastAPI(
    title="AI Feedback System",
    description="Two-Dashboard AI Feedback System with User and Admin interfaces",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

setup_exception_handlers(app)
app.include_router(user_router)
app.include_router(admin_router)
frontend_path = Path(__file__).parent.parent.parent / "frontend" / "public"

if frontend_path.exists():
    user_path = frontend_path / "user"
    if user_path.exists():
        app.mount("/user", StaticFiles(directory=str(user_path), html=True), name="user-dashboard")
    
    admin_path = frontend_path / "admin"
    if admin_path.exists():
        app.mount("/admin", StaticFiles(directory=str(admin_path), html=True), name="admin-dashboard")
    
    assets_path = frontend_path.parent / "assets"
    if assets_path.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")


@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to user dashboard"""
    return RedirectResponse(url="/user/")


@app.get("/api/health")
async def health_check():
    """Global health check endpoint"""
    return {
        "status": "healthy",
        "service": "ai-feedback-system",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True
    )
