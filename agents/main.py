"""
Main Fast-Agent Implementation for Bespaarplan Generation
Replicates the proven workflow from .claude/prompts/generate-bespaarplan-streamlined.md
"""

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from mcp_agent import FastAgent, Prompt

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAgent
fast = FastAgent("wattzo-bespaarplan-generator")

# ===============================================
# AGENT DEFINITIONS WITH HYBRID MODEL STRATEGY
# ===============================================

@fast.agent(
    name="bespaarplan_orchestrator",
    instruction="""You are the main orchestrator for bespaarplan generation. 
    
    Your job is to coordinate the complete workflow to generate a personalized energy savings plan (Bespaarplan) for the given deal ID, following the proven streamlined process.
    
    The process is:
    1. Get comprehensive deal data using energy-data MCP
    2. Calculate all metrics using calculation-engine MCP  
    3. Fill template using template-provider MCP
    4. Store result in Supabase bucket and update database
    
    Always ensure data quality and completeness at each step.""",
    servers=["energy-data", "calculation-engine", "template-provider"],
    model="claude-sonnet-4-20250514",
    use_history=True
)

@fast.agent(
    name="data_collector", 
    instruction="""You are responsible for fetching comprehensive deal data efficiently.
    
    Use the energy-data MCP server to get all deal information including:
    - Customer information and contact details
    - Property profile and energy assessment  
    - Current energy usage, costs, and CO2 emissions
    - Current systems (heating, insulation, solar)
    - Complete quote with products and pricing
    - Subsidies and regulations
    
    Validate that all required data is present and complete.""",
    servers=["energy-data"],
    model="openrouter.google/gemini-2.5-flash"
)

@fast.agent(
    name="metrics_calculator",
    instruction="""You are responsible for calculating all financial and environmental metrics with precision.
    
    Use the calculation-engine MCP server to calculate:
    - Energy savings (gas, electricity, solar production)
    - Financial metrics (investment, subsidies, payback, ROI)
    - Per-product metrics (individual savings and payback)
    - Financing/loan calculations
    - Energy label improvements
    - CO2 reduction and equivalents
    
    Ensure all calculations are accurate and complete.""",
    servers=["calculation-engine"],
    model="claude-sonnet-4-20250514"
)

@fast.agent(
    name="template_processor",
    instruction="""You are responsible for filling HTML templates with calculated data efficiently.
    
    Use the template-provider MCP server to:
    - Get the bespaarplan template
    - Fill all placeholders with provided data
    - Apply Dutch number formatting (1000+ numbers get dots: 1.200, 45.500)
    - Generate dynamic narratives based on verified data
    - Apply emphasis based on customer motivation
    
    Follow the proven streamlined process for template filling.""",
    servers=["template-provider"],
    model="openrouter.google/gemini-2.5-flash"
)

@fast.agent(
    name="storage_manager",
    instruction="""You are responsible for storing the generated bespaarplan in Supabase.
    
    Your tasks:
    1. Upload the HTML file to Supabase storage bucket 'bespaarplan-reports'
    2. Get the public CDN URL for the uploaded file
    3. Update the deals table with the URL, timestamp, and status
    4. Return the storage details
    
    Use proper file naming: deal-{deal_id}/bespaarplan-{timestamp}.html""",
    servers=[],
    model="openrouter.google/gemini-2.5-flash"
)

@fast.agent(
    name="quality_validator",
    instruction="""You are responsible for validating bespaarplan completeness, accuracy, and narrative quality.
    
    Check for:
    - Data completeness (all required fields filled)
    - Calculation accuracy (numbers make sense)
    - Narrative quality (personalized, coherent)
    - Template completeness (no missing placeholders)
    - Dutch language quality
    
    Rate the overall quality and provide specific feedback for improvements.""",
    model="claude-sonnet-4-20250514"
)

# ===============================================
# WORKFLOW DEFINITIONS
# ===============================================

@fast.chain(
    name="bespaarplan_generation",
    sequence=["data_collector", "metrics_calculator", "template_processor", "storage_manager"]
)

@fast.evaluator_optimizer(
    name="quality_assured_bespaarplan",
    generator="bespaarplan_generation",
    evaluator="quality_validator", 
    min_rating="EXCELLENT",
    max_refinements=2
)

# ===============================================
# MAIN GENERATION FUNCTION
# ===============================================

async def generate_bespaarplan_for_deal_simple(deal_id: str) -> Dict[str, Any]:
    """Simple version for testing - direct orchestrator call"""
    logger.info(f"Starting simple bespaarplan generation for deal: {deal_id}")
    
    try:
        async with fast.run() as agent:
            # Direct orchestrator call
            result = await agent.bespaarplan_orchestrator.send(
                f"Generate complete bespaarplan for deal_id: {deal_id}"
            )
            
            logger.info(f"Successfully generated bespaarplan for deal: {deal_id}")
            return {
                "success": True,
                "deal_id": deal_id,
                "result": result,
                "generated_at": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to generate bespaarplan for deal {deal_id}: {str(e)}")
        return {
            "success": False,
            "deal_id": deal_id,
            "error": str(e),
            "generated_at": datetime.now().isoformat()
        }


async def generate_bespaarplan_for_deal(deal_id: str) -> Dict[str, Any]:
    """
    Generate a complete bespaarplan for the given deal ID.
    
    This function replicates the proven workflow from the streamlined prompt.
    """
    logger.info(f"Starting bespaarplan generation for deal: {deal_id}")
    
    try:
        async with fast.run() as agent:
            # Use the quality-assured workflow
            result = await agent.quality_assured_bespaarplan.send(
                f"Generate complete bespaarplan for deal_id: {deal_id}"
            )
            
            logger.info(f"Successfully generated bespaarplan for deal: {deal_id}")
            return {
                "success": True,
                "deal_id": deal_id,
                "result": result,
                "generated_at": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to generate bespaarplan for deal {deal_id}: {str(e)}")
        return {
            "success": False,
            "deal_id": deal_id,
            "error": str(e),
            "generated_at": datetime.now().isoformat()
        }

# ===============================================
# CLI INTERFACE
# ===============================================

async def main():
    """CLI interface for testing bespaarplan generation."""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python agents/main.py <deal_id>")
        print("Example: python agents/main.py 2b3ddc42-72e8-4d92-85fb-6b1d5440f405")
        sys.exit(1)
    
    deal_id = sys.argv[1]
    print(f"Generating bespaarplan for deal: {deal_id}")
    
    result = await generate_bespaarplan_for_deal(deal_id)
    
    if result["success"]:
        print("✅ Bespaarplan generated successfully!")
        print(f"📄 Details: {result}")
    else:
        print("❌ Failed to generate bespaarplan!")
        print(f"🔥 Error: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main())