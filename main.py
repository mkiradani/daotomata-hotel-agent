"""
Daotomata Hotel Bot API

A sophisticated AI concierge system for hotels using OpenAI Agents SDK.
Provides specialized agents for booking, concierge services, guest services, and activities.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from app.config import settings
from app.api.chat import router as chat_router
# from app.api.chat_mcp import router as chat_mcp_router  # Disabled due to import issues
from app.api.hotel import router as hotel_router
from app.api.webhook import router as webhook_router

# Import PMS webhooks if available
try:
    import sys
    from pathlib import Path

    pms_path = Path(__file__).parent.parent / "pms"
    sys.path.append(str(pms_path))
    from api.webhooks import router as webhooks_router

    PMS_WEBHOOKS_AVAILABLE = True
except ImportError:
    PMS_WEBHOOKS_AVAILABLE = False
    webhooks_router = None

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    from app.services.chatwoot_service import initialize_chatwoot_configs, chatwoot_service
    
    # Startup
    print(f"🏨 Starting {settings.app_name} v{settings.app_version}")
    print(f"🤖 OpenAI Model: {settings.openai_model}")
    print(f"🏢 Current Domain: {settings.current_domain or 'Not set'}")

    # Validate MCP requirements
    import subprocess
    try:
        result = subprocess.run(["npx", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ MCP requirements available: npx {result.stdout.strip()}")
        else:
            print("⚠️ Warning: npx not available, MCP will use fallback")
    except Exception as e:
        print(f"⚠️ Warning: Could not validate MCP requirements: {e}")

    # Initialize Chatwoot configurations for all hotels
    try:
        await initialize_chatwoot_configs()
        print("✅ Chatwoot configurations initialized")
    except Exception as e:
        print(f"⚠️ Warning: Could not initialize Chatwoot configs: {e}")

    yield

    # Shutdown
    print("🛑 Shutting down Hotel Bot API")
    
    # Close Chatwoot service
    try:
        await chatwoot_service.close()
        print("✅ Chatwoot service closed")
    except Exception as e:
        print(f"⚠️ Warning: Error closing Chatwoot service: {e}")


app = FastAPI(
    title=settings.app_name,
    description="""
    ## 🏨 Daotomata Hotel Bot API

    A sophisticated AI concierge system powered by OpenAI Agents SDK.

    ### 🤖 Specialized Agents

    - **Booking Specialist**: Room reservations, availability checks, rate inquiries
    - **Hotel Concierge**: Local recommendations, directions, area information
    - **Guest Services**: Hotel services, maintenance requests, complaint resolution
    - **Activities Coordinator**: Hotel activities, entertainment, spa services

    ### 🛠️ Features

    - Multi-agent conversation routing
    - Hotel-specific context awareness
    - Real-time PMS integration (Cloudbeds)
    - Live availability and booking management
    - Service request management
    - Conversation history tracking
    - Webhook-based real-time updates

    ### 🔧 Integration

    - Directus CMS database integration
    - Multi-tenant hotel support
    - Cloudbeds PMS integration
    - Real-time webhook processing
    - RESTful API endpoints
    """,
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router)
# app.include_router(chat_mcp_router)  # Disabled due to import issues
app.include_router(hotel_router)
app.include_router(webhook_router)

# Include PMS webhooks if available
if PMS_WEBHOOKS_AVAILABLE and webhooks_router:
    app.include_router(webhooks_router)
    print("✅ PMS Webhooks enabled")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": f"🏨 {settings.app_name}",
        "version": settings.app_version,
        "status": "operational",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "chat": "/api/chat",
            "hotel_info": "/api/hotel/info",
            "availability": "/api/hotel/availability",
            "activities": "/api/hotel/activities",
            "facilities": "/api/hotel/facilities",
            "chatwoot_webhook": "/webhook/chatwoot/{hotel_id}",
            "pms_webhooks": "/webhooks" if PMS_WEBHOOKS_AVAILABLE else "Not available",
        },
        "pms_integration": {
            "enabled": PMS_WEBHOOKS_AVAILABLE,
            "provider": "Cloudbeds" if PMS_WEBHOOKS_AVAILABLE else None,
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "hotel-bot",
        "version": settings.app_version,
        "openai_model": settings.openai_model,
        "current_domain": settings.current_domain,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app", host="0.0.0.0", port=8000, reload=settings.debug, log_level="info"
    )
