from fastapi import FastAPI, Depends
from app.db import db_ok
from app.routes.users import router as users_router
from app.routes.applications import router as applications_router
from app.routes.api_keys import router as apikeys_router
from app.config import settings
from fastapi_limiter import FastAPILimiter
import redis.asyncio as aioredis
from app.auth import SignatureCaptureMiddleware, require_api_key, verify_signature_if_present
from fastapi_limiter.depends import RateLimiter
from contextlib import asynccontextmanager
import logging
import os

# Set up logging
logger = logging.getLogger(__name__)

# Create FastAPI app instance with metadata
app = FastAPI(
    title="LIJOA API",
    version="0.3.0",
    description="Job Application Tracking API with Authentication and Rate Limiting"
)

# Add middleware for signature capture (placeholder for future use)
app.add_middleware(SignatureCaptureMiddleware)

# Initialize FastAPILimiter with None for test environment
# This will be properly initialized in the lifespan event handler
@app.on_event("startup")
async def startup_event():
    """Initialize rate limiter on startup"""
    try:
        # Check if we're in test environment
        if os.getenv("APP_ENV") == "test":
            # Initialize with None to disable rate limiting in tests
            await FastAPILimiter.init(None)
            logger.info("Rate limiter disabled for test environment")
        else:
            # Try to connect to Redis
            redis_client = aioredis.from_url(
                settings.REDIS_URL, 
                encoding="utf-8", 
                decode_responses=True
            )
            # Test the connection
            await redis_client.ping()
            await FastAPILimiter.init(redis_client)
            logger.info("Redis connection established and rate limiter initialized")
    except Exception as e:
        logger.warning(f"Failed to connect to Redis: {e}. Rate limiting will be disabled.")
        # Initialize with None to disable rate limiting
        await FastAPILimiter.init(None)

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    await FastAPILimiter.close()
    logger.info("Rate limiter closed")

@app.get("/healthz")
def healthz():
    """Health check endpoint that verifies database connectivity"""
    try:
        db_ok()
        return {"status": "ok", "db": "ok"}
    except Exception as e:
        return {
            "status": "degraded", 
            "db": f"error: {e.__class__.__name__}"
        }

# Include all routers
app.include_router(users_router, tags=["users"])
app.include_router(apikeys_router, tags=["api-keys"])

# Create secured router for applications endpoints
from fastapi import APIRouter, Request, Response

async def conditional_rate_limit(request: Request, response: Response):
    """Apply rate limiting only if FastAPILimiter is initialized (i.e., Redis available)."""
    if FastAPILimiter.redis:
        limiter = RateLimiter(times=60, seconds=60)
        return await limiter(request, response)
    return None

secured = APIRouter(
    dependencies=[
        Depends(require_api_key),
        Depends(verify_signature_if_present),
        Depends(conditional_rate_limit),
    ]
)

# Mount all applications endpoints behind the security layer
for route in applications_router.routes:
    secured.add_api_route(
        path=route.path,
        endpoint=route.endpoint,
        methods=list(route.methods - {"HEAD", "OPTIONS"}),  # Exclude HEAD and OPTIONS
        response_model=getattr(route, "response_model", None),
        status_code=getattr(route, "status_code", None),
        name=route.name,
        tags=getattr(route, "tags", []),
    )

# Include the secured applications router with /api prefix to avoid conflicts
app.include_router(secured, prefix="/api", tags=["applications"])

# Custom OpenAPI documentation
@app.get("/", include_in_schema=False)
def root():
    """Redirect to API documentation"""
    return {
        "message": "LIJOA API",
        "version": "0.3.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

# Custom exception handlers
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    # Preserve specific detail if provided by the raised HTTPException
    detail = getattr(exc, "detail", None)
    if isinstance(detail, dict):
        content = detail
    else:
        content = {"detail": detail or "Resource not found"}
    return JSONResponse(
        status_code=404,
        content=content
    )

@app.exception_handler(429)
async def rate_limit_handler(request: Request, exc):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again later."}
    )