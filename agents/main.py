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
from mcp_agent.core.request_params import RequestParams

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
    name="bespaarplan_generator",
    instruction="""You generate a complete bespaarplan for the given deal ID by executing these steps IN ORDER:
    
    STEP 1: FETCH DATA
    - Call get_comprehensive_deal_data(deal_id) from energy-data MCP
    - Extract the complete deal data structure
    - VERIFY customer data is present (name, address, email)
    
    STEP 2: CALCULATE METRICS
    - Call calculate_from_deal_data(comprehensive_data) from calculation-engine MCP
    - Pass the EXACT comprehensive_data from step 1
    - Receive complete calculation results
    
    STEP 3: GENERATE & UPLOAD BESPAARPLAN
    - Extract customer's last name from deal_data.customer.name (last word)
    - Format ALL numbers ≥1000 to Dutch style: 1200→"1.200" (except years/percentages)
    - Build template_data dict containing ALL values from both deal_data and metrics
    - Call generate_and_upload_template(template_data, deal_id, customer_last_name) from template-provider MCP
    - Return the complete response with public_url
    
    CRITICAL RULES:
    - Use ONLY data from MCP tool responses - NEVER make up data
    - If customer name is missing, STOP and report error
    - All three steps MUST complete successfully
    - Return the final result with public_url for the bespaarplan
    
    DATA STRUCTURE AWARENESS:
    The comprehensive_data contains:
    - customer: {name, email, phone, address, city, postal_code}
    - property: {type, year_built, size_m2, energy_label, etc.}
    - energy: {gas_usage, electricity_usage, solar_panels, etc.}
    - quote: {products with prices and subsidies}
    
    The metrics contain:
    - financial_impact: {annual_savings, monthly_savings, roi, payback, etc.}
    - energy_savings: {gas_reduction, electricity_change, co2_reduction}
    - property_value_impact: {value_increase, new_value}
    - products_with_metrics: [individual product calculations]
    
    Execute all steps sequentially and return the final result.""",
    servers=["energy-data", "calculation-engine", "template-provider"],
    model="openrouter.google/gemini-2.5-flash",
    request_params=RequestParams(
        maxTokens=100000,  # 100K tokens for comprehensive processing
        temperature=0.1    # Low temperature for consistency
    ),
    use_history=False  # Prevent data contamination between runs
)

# NOTE: Individual agents below are DEPRECATED as of the single-agent update.
# The bespaarplan_generator agent now handles the complete workflow.
# These are kept for backwards compatibility but are no longer used.

# DEPRECATED - Now part of bespaarplan_generator
@fast.agent(
    name="data_collector", 
    instruction="""DEPRECATED - Use bespaarplan_generator instead.""",
    servers=["energy-data"],
    model="openrouter.google/gemini-2.5-flash",
    request_params=RequestParams(
        maxTokens=8192,
        temperature=0.1
    )
)

# DEPRECATED - Now part of bespaarplan_generator
@fast.agent(
    name="metrics_calculator",
    instruction="""DEPRECATED - Use bespaarplan_generator instead.""",
    servers=["calculation-engine"],
    model="claude-sonnet-4-20250514",
    request_params=RequestParams(
        maxTokens=32768,
        temperature=0.2
    ),
    use_history=True
)

# DEPRECATED - Now part of bespaarplan_generator
@fast.agent(
    name="template_processor",
    instruction="""DEPRECATED - Use bespaarplan_generator instead.""",
    servers=["template-provider"],
    model="claude-sonnet-4-20250514",
    request_params=RequestParams(
        maxTokens=32768,
        temperature=0.1
    ),
    use_history=True
)

# DEPRECATED - No longer needed
@fast.agent(
    name="storage_manager",
    instruction="""You are the Storage Operations Specialist responsible for persisting the generated bespaarplan to Supabase storage.
    
    CONTEXT:
    You receive:
    - File path from template_processor's save_filled_template result
    - Deal data from data_collector (to extract customer last name)
    - Deal ID from the workflow
    
    MCP TOOLS AVAILABLE:
    Use the supabase-storage server which provides:
    1. `upload_html_file(deal_id, html_content, customer_last_name)` - Upload to storage
    2. `update_deal_bespaarplan(deal_id, bespaarplan_url)` - Update database
    3. `get_deal_bespaarplan_status(deal_id)` - Check existing status
    
    STORAGE WORKFLOW:
    1. Read the HTML file content from the local file path
    2. Extract customer last name from deal_data.customer.name (last word)
    3. Call upload_html_file with deal_id, content, and last_name
    4. Get the public_url from the response
    5. Update database with update_deal_bespaarplan
    
    FILE ORGANIZATION:
    - Bucket: 'bespaarplan-reports'
    - Path structure: {last_name}-{deal_id}/bespaarplan-{deal_id}.html
    - Example: jodhabier-12345/bespaarplan-12345.html
    
    EXTRACTING LAST NAME:
    From deal_data.customer.name, take the last word:
    - "John Jodhabier" → "jodhabier"
    - "Jan van der Berg" → "berg"
    - Single name "Ahmed" → "ahmed"
    
    ERROR HANDLING:
    - File not found: Check template_processor output
    - Upload fails: Report specific error from MCP tool
    - Database update fails: Log but still return success if upload worked
    - Missing customer name: Use "unknown" as fallback
    
    RESPONSE STRUCTURE:
    Return the complete result including:
    - success: boolean
    - deal_id: string
    - public_url: CDN URL for access
    - file_path: Storage path ({last_name}-{deal_id}/bespaarplan-{deal_id}.html)
    - uploaded_at: Timestamp
    - database_updated: boolean
    
    SUCCESS CRITERIA:
    - HTML content successfully uploaded to Supabase storage
    - Public URL returned and functional
    - Database updated with bespaarplan metadata
    - Customer can access their report via the public URL""",
    servers=["supabase-storage"],
    model="openrouter.google/gemini-2.5-flash",
    request_params=RequestParams(
        maxTokens=8192,
        temperature=0.1
    )
)

@fast.agent(
    name="quality_validator",
    instruction="""You are the Quality Assurance Specialist ensuring the bespaarplan meets all standards before delivery.
    
    VALIDATION SCOPE (OPTIMIZED WORKFLOW):
    You receive the output from the 3-agent chain and must validate:
    1. MCP tool usage correctness
    2. Data flow integrity
    3. Calculation accuracy
    4. Template generation and upload success
    5. Overall quality
    
    MCP VALIDATION CHECKS:
    1. Data Collection:
       - Was get_comprehensive_deal_data called with valid deal_id?
       - Did it return all required sections?
       - Are critical fields populated?
    
    2. Calculations:
       - Was calculate_from_deal_data called with complete data?
       - Are all metric categories present?
       - Do values pass sanity checks?
    
    3. Template Processing & Storage (COMBINED):
       - Was generate_and_upload_template called?
       - Did it return a public_url?
       - Was database_updated = true?
       - Is file_path in correct format: {last_name}-{deal_id}/bespaarplan-{deal_id}.html?
    
    DATA INTEGRITY VALIDATION:
    - Customer data matches between sections
    - Products in quote match calculation results
    - Energy savings align with system changes
    - Financial metrics are internally consistent
    
    CALCULATION SANITY CHECKS:
    - Payback period: 5-20 years typical
    - ROI: Positive and realistic (10-30% typical)
    - Energy savings: Match installed products
    - CO2 reduction: Proportional to energy saved
    - Monthly savings: Annual / 12 (roughly)
    
    STORAGE & ACCESS VALIDATION:
    - Public URL is returned and valid
    - Database was updated (database_updated = true)
    - File naming follows convention
    - Customer can access the bespaarplan
    
    NARRATIVE QUALITY ASSESSMENT:
    - Factual: Based only on provided data
    - Personalized: Uses customer's actual situation
    - Motivating: Highlights relevant benefits
    - Professional: Clear Dutch language
    - Complete: All required narratives present
    
    RATING SYSTEM:
    - EXCELLENT: All checks pass, high quality
    - GOOD: Minor issues, still acceptable
    - NEEDS_IMPROVEMENT: Major issues to fix
    - FAILED: Critical errors, cannot proceed
    
    FEEDBACK FORMAT:
    Provide specific, actionable feedback:
    - What passed validation ✓
    - What needs attention ⚠
    - What must be fixed ✗
    - Suggested improvements
    
    SUCCESS CRITERIA:
    Rating of EXCELLENT or GOOD with:
    - All MCP tools used correctly
    - Data flows intact through 3-agent pipeline
    - Calculations mathematically sound
    - Template generated and uploaded successfully
    - Public URL available for customer access
    - Database updated with bespaarplan info""",
    model="claude-sonnet-4-20250514",
    request_params=RequestParams(
        maxTokens=32768,
        temperature=0.2
    ),
    use_history=True
)

# ===============================================
# WORKFLOW DEFINITIONS
# ===============================================

# NOTE: Chain and evaluator-optimizer workflows are DEPRECATED
# The single bespaarplan_generator agent handles the complete workflow

# ===============================================
# MAIN GENERATION FUNCTION
# ===============================================

async def generate_bespaarplan_for_deal_simple(deal_id: str) -> Dict[str, Any]:
    """Generate bespaarplan using single agent approach"""
    logger.info(f"Starting bespaarplan generation for deal: {deal_id}")
    
    try:
        async with fast.run() as agent:
            # Direct call to single agent
            result = await agent.bespaarplan_generator.send(
                f"Generate complete bespaarplan for deal_id: {deal_id}"
            )
            
            logger.info(f"Successfully generated bespaarplan for deal: {deal_id}")
            
            # Extract the public_url from the result
            # The agent should return the generate_and_upload_template response
            bespaarplan_url = ""
            if isinstance(result, str):
                # Try to extract URL from string response
                import re
                url_match = re.search(r'https://[^\s"]+bespaarplan[^\s"]+', result)
                if url_match:
                    bespaarplan_url = url_match.group(0)
            elif isinstance(result, dict):
                bespaarplan_url = result.get("public_url", "")
            
            return {
                "success": True,
                "deal_id": deal_id,
                "result": result,
                "bespaarplan_url": bespaarplan_url,
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
    
    This now uses the single agent approach for better reliability.
    """
    # Just call the simple version - they're now the same
    return await generate_bespaarplan_for_deal_simple(deal_id)

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