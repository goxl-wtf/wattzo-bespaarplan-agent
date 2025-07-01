"""
FastAPI implementation for CRM integration with Bespaarplan generation
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import our agent system
from agents.main import create_fast_agent, generate_bespaarplan_with_agent

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global agent instance
agent_app = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage the lifecycle of the FastAgent instance.
    This ensures MCP servers are initialized once and kept alive.
    """
    global agent_app
    logger.info("Starting FastAgent lifecycle...")
    
    try:
        # Create and initialize the FastAgent
        fast_agent = create_fast_agent()
        
        # Run the agent and keep it alive
        async with fast_agent.run() as agent:
            agent_app = agent
            logger.info("FastAgent initialized successfully with MCP servers")
            
            # Yield control back to FastAPI
            yield
            
    except Exception as e:
        logger.error(f"Failed to initialize FastAgent: {str(e)}")
        raise
    finally:
        logger.info("Shutting down FastAgent...")
        agent_app = None

# FastAPI app with lifespan
app = FastAPI(
    title="Wattzo Bespaarplan Generation API",
    description="API for generating personalized energy savings plans (Bespaarplan) for customers",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===============================================
# PYDANTIC MODELS
# ===============================================

class BespaarplanRequest(BaseModel):
    deal_id: str = Field(..., description="Unique identifier for the deal")
    priority: str = Field(default="normal", description="Priority level: normal, urgent")
    notify_customer: bool = Field(default=True, description="Whether to notify customer when complete")
    
    class Config:
        json_schema_extra = {
            "example": {
                "deal_id": "2b3ddc42-72e8-4d92-85fb-6b1d5440f405",
                "priority": "normal",
                "notify_customer": True
            }
        }

class BespaarplanResponse(BaseModel):
    success: bool = Field(..., description="Whether the generation was successful")
    deal_id: str = Field(..., description="The deal ID that was processed")
    bespaarplan_url: Optional[str] = Field(None, description="Public URL to the generated bespaarplan")
    status: str = Field(..., description="Current status of the generation")
    generated_at: str = Field(..., description="ISO timestamp of when generation completed")
    processing_time_seconds: Optional[float] = Field(None, description="Time taken to generate")
    error: Optional[str] = Field(None, description="Error message if generation failed")

class StatusResponse(BaseModel):
    deal_id: str
    status: str
    bespaarplan_url: Optional[str] = None
    generated_at: Optional[str] = None
    error: Optional[str] = None

# ===============================================
# API ENDPOINTS
# ===============================================

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "service": "Wattzo Bespaarplan Generation API",
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    agent_status = "available" if agent_app is not None else "not_initialized"
    mcp_status = "connected" if agent_app is not None else "disconnected"
    
    return {
        "status": "healthy" if agent_app is not None else "degraded",
        "services": {
            "fast_agent": agent_status,
            "mcp_servers": mcp_status,
            "database": "connected"  # TODO: Implement actual DB check
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post(
    "/api/v1/generate-bespaarplan",
    response_model=BespaarplanResponse,
    tags=["Bespaarplan"],
    summary="Generate a new bespaarplan",
    description="Generate a personalized energy savings plan for a customer deal"
)
async def generate_bespaarplan(
    request: BespaarplanRequest, 
    background_tasks: BackgroundTasks
) -> BespaarplanResponse:
    """
    Generate a bespaarplan for the specified deal ID.
    
    This endpoint triggers the complete workflow:
    1. Fetch deal data from energy-data MCP
    2. Calculate metrics using calculation-engine MCP  
    3. Fill template using template-provider MCP
    4. Store in Supabase bucket and update database
    """
    start_time = datetime.now()
    logger.info(f"Received bespaarplan generation request for deal: {request.deal_id}")
    
    if agent_app is None:
        logger.error("FastAgent not initialized - cannot generate bespaarplan")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable - agent not initialized"
        )
    
    try:
        # Generate the bespaarplan using our agent system
        result = await generate_bespaarplan_with_agent(agent_app, request.deal_id)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        if result["success"]:
            # Extract the bespaarplan URL from the result
            bespaarplan_url = result.get("bespaarplan_url", "")
            
            # Background task for customer notification if requested
            if request.notify_customer:
                background_tasks.add_task(
                    notify_customer_portal, 
                    request.deal_id, 
                    bespaarplan_url
                )
            
            logger.info(f"Successfully generated bespaarplan for deal: {request.deal_id}")
            
            return BespaarplanResponse(
                success=True,
                deal_id=request.deal_id,
                bespaarplan_url=bespaarplan_url,
                status="completed",
                generated_at=datetime.now().isoformat(),
                processing_time_seconds=processing_time
            )
        else:
            logger.error(f"Generation failed for deal {request.deal_id}: {result.get('error', 'Unknown error')}")
            
            return BespaarplanResponse(
                success=False,
                deal_id=request.deal_id,
                status="failed",
                generated_at=datetime.now().isoformat(),
                processing_time_seconds=processing_time,
                error=result.get("error", "Unknown error occurred")
            )
            
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        error_msg = f"Unexpected error during generation: {str(e)}"
        logger.error(f"Generation failed for deal {request.deal_id}: {error_msg}", exc_info=True)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )

@app.get(
    "/api/v1/bespaarplan-status/{deal_id}",
    response_model=StatusResponse,
    tags=["Bespaarplan"],
    summary="Get bespaarplan status",
    description="Check the status of a bespaarplan generation for a specific deal"
)
async def get_bespaarplan_status(deal_id: str) -> StatusResponse:
    """
    Get the current status of bespaarplan generation for a deal.
    
    This endpoint queries the database to check if a bespaarplan has been generated
    and returns the current status and URL if available.
    """
    try:
        # TODO: Implement database query through Supabase MCP
        # For now, return a placeholder response
        logger.info(f"Checking bespaarplan status for deal: {deal_id}")
        
        # This would be replaced with actual database query
        return StatusResponse(
            deal_id=deal_id,
            status="pending",  # pending, completed, failed
            bespaarplan_url=None,
            generated_at=None,
            error=None
        )
        
    except Exception as e:
        logger.error(f"Failed to get status for deal {deal_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )

@app.get(
    "/api/v1/customer-bespaarplan/{deal_id}",
    tags=["Customer Portal"],
    summary="Get bespaarplan for customer portal",
    description="Retrieve the bespaarplan URL for display in customer portal"
)
async def get_customer_bespaarplan(deal_id: str):
    """
    Get the bespaarplan for customer portal display.
    
    This endpoint is used by the customer portal to retrieve the bespaarplan URL
    for displaying to the customer.
    """
    try:
        logger.info(f"Customer portal requesting bespaarplan for deal: {deal_id}")
        
        # TODO: Implement database query to get bespaarplan_url
        # TODO: Add authentication to ensure customer can only access their own reports
        
        # Placeholder response
        return {
            "deal_id": deal_id,
            "bespaarplan_url": "https://your-supabase-project.supabase.co/storage/v1/object/public/bespaarplan-reports/deal-123/bespaarplan-2025-06-27.html",
            "status": "available",
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get customer bespaarplan for deal {deal_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve bespaarplan: {str(e)}"
        )

# ===============================================
# BACKGROUND TASKS
# ===============================================

async def notify_customer_portal(deal_id: str, bespaarplan_url: str):
    """
    Background task to notify customer portal when bespaarplan is ready.
    
    This could send emails, push notifications, or update customer portal status.
    """
    try:
        logger.info(f"Notifying customer portal for deal: {deal_id}")
        # TODO: Implement notification logic
        # - Send email to customer
        # - Update customer portal status
        # - Send push notification
        
        await asyncio.sleep(1)  # Simulate notification processing
        logger.info(f"Customer notification sent for deal: {deal_id}")
        
    except Exception as e:
        logger.error(f"Failed to notify customer for deal {deal_id}: {str(e)}")

# ===============================================
# ERROR HANDLERS
# ===============================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler for unexpected errors."""
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": "Internal server error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )

# Note: Startup/shutdown logic is now handled by the lifespan context manager

# ===============================================
# MAIN ENTRY POINT
# ===============================================

if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )