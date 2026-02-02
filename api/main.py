"""FastAPI application for E*TRADE Local API."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.config import settings

# Configure logging
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="E*TRADE Local API",
    description="Local REST API wrapper for E*TRADE with MCP integration",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "etrade-local-api",
        "version": "0.1.0",
    }


@app.get("/config")
async def config_status():
    """Get current configuration status."""
    return {
        "sandbox_mode": settings.etrade_sandbox,
        "api_host": settings.api_host,
        "api_port": settings.api_port,
        "mcp_enabled": settings.mcp_enabled,
        "etrade_base_url": settings.etrade_base_url,
    }


@app.get("/docs")
async def documentation():
    """API documentation endpoint."""
    return {
        "swagger_ui": "/docs",
        "openapi_schema": "/openapi.json",
        "redoc": "/redoc",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,
    )
