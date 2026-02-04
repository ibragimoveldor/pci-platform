"""
PCI Platform - Main FastAPI Application
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.config import settings
from app.core.database import engine, Base
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Runs on startup and shutdown.
    """
    # Startup
    print(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    print(f"📊 Environment: {settings.environment}")
    
    # Create tables (in production, use Alembic migrations instead)
    if settings.environment == "development":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created")
    
    yield
    
    # Shutdown
    print("👋 Shutting down...")
    await engine.dispose()


def create_application() -> FastAPI:
    """Application factory."""
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Pavement Condition Index (PCI) Analysis Platform",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )
    
    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    
    return app


app = create_application()


# =============================================================================
# Health Check Endpoints
# =============================================================================
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "version": settings.app_version}


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """
    Readiness check - verifies all dependencies are available.
    Used by Kubernetes for readiness probes.
    """
    from app.core.database import get_db
    from app.core.redis import get_redis
    from app.core.storage import storage
    
    checks = {
        "database": False,
        "redis": False,
        "storage": False,
    }
    
    # Check database
    try:
        async for db in get_db():
            await db.execute("SELECT 1")
            checks["database"] = True
            break
    except Exception:
        pass
    
    # Check Redis
    try:
        redis = await get_redis()
        await redis.ping()
        checks["redis"] = True
    except Exception:
        pass
    
    # Check MinIO/S3
    try:
        checks["storage"] = await storage.health_check()
    except Exception:
        pass
    
    all_healthy = all(checks.values())
    
    return {
        "status": "ready" if all_healthy else "degraded",
        "checks": checks,
    }
