#!/usr/bin/env python3
"""
Template Provider MCP Server
Provides HTML templates for report generation to avoid LLM token limits
"""

import os
from typing import Dict, Any, List
from pathlib import Path
import uuid
import httpx
import asyncio
from datetime import datetime
import logging
from jinja2 import Environment, Template

from fastmcp import FastMCP
from supabase import create_client, Client

# Initialize MCP server
mcp = FastMCP("TemplateProvider")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the directory where this server.py file is located
SERVER_DIR = Path(__file__).parent
TEMPLATES_DIR = SERVER_DIR / "templates"

# Storage configuration
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
# Always use the correct bucket name
BUCKET_NAME = "bespaarplan-reports"

# Fallback values if environment variables are not passed
if not SUPABASE_URL:
    SUPABASE_URL = "https://dlxxgvpebaeqmmqdiqtp.supabase.co"
if not SUPABASE_SERVICE_KEY:
    SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRseHhndnBlYmFlcW1tcWRpcXRwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0Mzg3MjMzMiwiZXhwIjoyMDU5NDQ4MzMyfQ.73Hk_UQRvH08LSh6YlsFgtHnZkh0tA3X23wCuJCGrG0"

# Debug logging
logger.info(f"Environment variables received:")
logger.info(f"DEMO_MODE: {DEMO_MODE}")
logger.info(f"SUPABASE_URL present: {bool(SUPABASE_URL)} (length: {len(SUPABASE_URL)})")
logger.info(f"SUPABASE_SERVICE_KEY present: {bool(SUPABASE_SERVICE_KEY)} (length: {len(SUPABASE_SERVICE_KEY)})")
logger.info(f"BUCKET_NAME: {BUCKET_NAME}")

# Initialize Supabase client
supabase: Client = None
if not DEMO_MODE and SUPABASE_URL and SUPABASE_SERVICE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    logger.info(f"Supabase client initialized. URL: {SUPABASE_URL[:30]}...")
    logger.info(f"Bucket name: {BUCKET_NAME}")
else:
    logger.warning(f"Supabase client NOT initialized. DEMO_MODE={DEMO_MODE}, URL={bool(SUPABASE_URL)}, SERVICE_KEY={bool(SUPABASE_SERVICE_KEY)}")


def load_template(template_name: str) -> str:
    """Load a template file from the templates directory"""
    template_path = TEMPLATES_DIR / template_name
    
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_name}")
    
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


@mcp.tool()
def get_bespaarplan_template() -> Dict[str, Any]:
    """
    Get the Bespaarplan magazine-style HTML template.
    
    This template contains:
    - Hero section with key metrics
    - Customer introduction and wishes
    - Current energy situation analysis
    - Proposed sustainability measures
    - Financial calculations and ROI
    - Property value increase
    - Environmental impact
    - Next steps and contact info
    
    The template uses Jinja2-style placeholders ({{ variable }}) that should be
    replaced with actual values from the energy and calculation data.
    
    Returns:
        Dict containing the template HTML and metadata
    """
    try:
        template_html = load_template("bespaarplan_magazine.html")
        
        return {
            "success": True,
            "template": template_html,
            "template_type": "bespaarplan_magazine",
            "placeholders": {
                "customer_data": [
                    "customer_name", "customer_salutation", "customer_lastname",
                    "property_address", "property_city", "property_size", "property_year"
                ],
                "energy_data": [
                    "gas_usage_current", "electricity_usage_current", "current_energy_costs",
                    "gas_usage_after", "electricity_usage_gross_after", "electricity_usage_net_after",
                    "solar_production", "energy_costs_after", "gas_savings_pct", 
                    "electricity_savings_pct", "energy_label_current", "energy_label_after"
                ],
                "financial_data": [
                    "annual_savings", "monthly_savings", "total_investment", "total_subsidies",
                    "net_investment", "monthly_payment", "monthly_cashflow", "loan_interest",
                    "payback_years", "roi_20_years", "total_profit_20_years"
                ],
                "environmental_data": [
                    "co2_reduction", "co2_reduction_pct", "co2_trees", "co2_car_km", "co2_flights"
                ],
                "property_value": [
                    "property_value_current", "property_value_increase", "property_value_after"
                ],
                "advisor_data": [
                    "advisor_name", "advisor_email", "advisor_phone"
                ],
                "lists": [
                    "customer_wishes", "products"
                ]
            }
        }
    except FileNotFoundError as e:
        return {
            "success": False,
            "error": str(e),
            "available_templates": [f.name for f in TEMPLATES_DIR.glob("*.html")]
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to load template: {str(e)}"
        }


@mcp.tool()
def list_available_templates() -> Dict[str, Any]:
    """
    List all available templates in the templates directory.
    
    Returns:
        Dict containing list of available template files
    """
    try:
        templates = [f.name for f in TEMPLATES_DIR.glob("*.html")]
        
        return {
            "success": True,
            "templates": templates,
            "templates_dir": str(TEMPLATES_DIR)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list templates: {str(e)}"
        }


@mcp.tool()
def save_filled_template(html_content: str, filename: str = None) -> Dict[str, Any]:
    """
    Save a filled HTML template to the outputs directory.
    
    This tool helps avoid streaming timeouts by saving the large HTML output
    to a file instead of returning it through the LLM response.
    
    Args:
        html_content: The filled HTML content
        filename: Optional filename (without extension). If not provided, 
                  a unique filename will be generated.
    
    Returns:
        Dict containing the file path and success status
    """
    try:
        # Create outputs directory if it doesn't exist
        outputs_dir = SERVER_DIR / "outputs"
        outputs_dir.mkdir(exist_ok=True)
        
        # Generate filename if not provided
        if not filename:
            filename = f"bespaarplan_{uuid.uuid4().hex[:8]}"
        
        # Ensure .html extension
        if not filename.endswith('.html'):
            filename += '.html'
        
        # Save the file
        file_path = outputs_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return {
            "success": True,
            "file_path": str(file_path),
            "filename": filename,
            "size_kb": len(html_content) / 1024
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to save template: {str(e)}"
        }


@mcp.tool()
def get_template_section(section_name: str) -> Dict[str, Any]:
    """
    Get a specific section of the Bespaarplan template.
    
    This allows processing the template in smaller chunks to avoid timeouts.
    
    Available sections:
    - hero: Hero section with main metrics
    - customer: Customer introduction and wishes
    - current_situation: Current energy analysis
    - products: Proposed measures section
    - financial: Financial calculations
    - environmental: Environmental impact
    - footer: Contact and next steps
    
    Args:
        section_name: Name of the section to retrieve
        
    Returns:
        Dict containing the section HTML and placeholders
    """
    try:
        # Load full template
        template_html = load_template("bespaarplan_magazine.html")
        
        # Define section markers
        sections = {
            "hero": {
                "start": "<!-- SECTION: HERO -->",
                "end": "<!-- END SECTION: HERO -->"
            },
            "customer": {
                "start": "<!-- SECTION: CUSTOMER -->",
                "end": "<!-- END SECTION: CUSTOMER -->"
            },
            "current_situation": {
                "start": "<!-- SECTION: CURRENT SITUATION -->",
                "end": "<!-- END SECTION: CURRENT SITUATION -->"
            },
            "products": {
                "start": "<!-- SECTION: PRODUCTS -->",
                "end": "<!-- END SECTION: PRODUCTS -->"
            },
            "financial": {
                "start": "<!-- SECTION: FINANCIAL -->",
                "end": "<!-- END SECTION: FINANCIAL -->"
            },
            "environmental": {
                "start": "<!-- SECTION: ENVIRONMENTAL -->",
                "end": "<!-- END SECTION: ENVIRONMENTAL -->"
            },
            "footer": {
                "start": "<!-- SECTION: FOOTER -->",
                "end": "<!-- END SECTION: FOOTER -->"
            }
        }
        
        if section_name not in sections:
            return {
                "success": False,
                "error": f"Unknown section: {section_name}",
                "available_sections": list(sections.keys())
            }
        
        # Extract section
        markers = sections[section_name]
        start_idx = template_html.find(markers["start"])
        end_idx = template_html.find(markers["end"])
        
        if start_idx == -1 or end_idx == -1:
            # Fallback: return smaller chunks based on line count
            lines = template_html.split('\n')
            chunk_size = 200
            
            section_ranges = {
                "hero": (0, 200),
                "customer": (200, 400),
                "current_situation": (400, 600),
                "products": (600, 900),
                "financial": (900, 1100),
                "environmental": (1100, 1300),
                "footer": (1300, None)
            }
            
            start, end = section_ranges.get(section_name, (0, chunk_size))
            section_html = '\n'.join(lines[start:end])
        else:
            section_html = template_html[start_idx:end_idx + len(markers["end"])]
        
        return {
            "success": True,
            "section": section_name,
            "html": section_html,
            "size_kb": len(section_html) / 1024
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get section: {str(e)}"
        }


@mcp.tool()
def save_template_section(section_name: str, filled_html: str, session_id: str) -> Dict[str, Any]:
    """
    Save a filled template section.
    
    Used for chunked processing - saves individual sections that can be combined later.
    
    Args:
        section_name: Name of the section
        filled_html: The filled HTML for this section
        session_id: Unique session ID to group sections together
        
    Returns:
        Dict with success status
    """
    try:
        # Create session directory
        session_dir = SERVER_DIR / "outputs" / f"session_{session_id}"
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Save section
        section_file = session_dir / f"{section_name}.html"
        with open(section_file, 'w', encoding='utf-8') as f:
            f.write(filled_html)
        
        return {
            "success": True,
            "section": section_name,
            "file_path": str(section_file),
            "session_id": session_id
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to save section: {str(e)}"
        }


@mcp.tool()
def get_narrative_templates() -> Dict[str, Any]:
    """
    Get narrative templates for dynamic personalization.
    
    This tool provides pre-written narrative snippets that can be used
    to create more engaging and personalized bespaarplan reports.
    
    Returns:
        Dict containing narrative templates organized by category
    """
    return {
        "success": True,
        "energy_label_narratives": {
            "major_jump": "Van energieslurper naar absolute toppresteerder - uw woning maakt een transformatie door die hem bij de top 15% meest efficiënte woningen in Nederland plaatst. Dit is een prestatie waar u trots op mag zijn.",
            "significant_jump": "Een indrukwekkende sprong vooruit - deze verbetering is direct merkbaar in uw comfort én op uw energierekening. Uw woning wordt significant energiezuiniger.",
            "good_improvement": "Een solide verbetering die uw woning klaarstoomt voor de toekomst. U zet belangrijke stappen richting duurzaam wonen.",
            "step_forward": "Elke stap telt - deze verbetering brengt u dichter bij een duurzaam en comfortabel huis."
        },
        "savings_contexts": {
            "high": {
                "young_family": "Dat extra gezinsuitje wordt nu werkelijkheid - elk jaar opnieuw",
                "empty_nesters": "Meer ruimte voor die lang gewenste hobby's en reizen",
                "single_professional": "Investeren in uw toekomst wordt een stuk makkelijker",
                "multi_generational": "Extra budget voor het hele gezin om van te genieten"
            },
            "medium": {
                "young_family": "De sportclub voor de kinderen is nu geen probleem meer",
                "empty_nesters": "Extra comfort zonder zich zorgen te maken over de kosten",
                "single_professional": "Slim besparen voor betere investeringen",
                "multi_generational": "Iedereen in huis profiteert van de besparingen"
            },
            "low": {
                "young_family": "Elke euro telt in een groeiend gezin",
                "empty_nesters": "Een welkome aanvulling op het pensioen",
                "single_professional": "Klein maar fijn voordeel dat optelt",
                "multi_generational": "Samen besparen voor de toekomst"
            }
        },
        "property_narratives": {
            "high_increase": "Uw investering in duurzaamheid wordt dubbel beloond - niet alleen lagere energiekosten, maar ook een substantiële waardestijging van uw woning.",
            "medium_increase": "Een slimme investering die zichzelf terugverdient én uw woning aantrekkelijker maakt voor toekomstige kopers.",
            "modest_increase": "Naast alle comfort- en besparingsvoordelen, stijgt ook nog eens de waarde van uw woning."
        },
        "urgency_messages": {
            "high_energy_prices": "Met de huidige energieprijzen is dit hét moment om te investeren in energiebesparing.",
            "subsidies_available": "Profiteer nu van de beschikbare ISDE-subsidies voordat de regels mogelijk wijzigen.",
            "property_market": "De woningmarkt beloont energiezuinige huizen steeds meer - wees er op tijd bij.",
            "comfort_season": "Begin het nieuwe seizoen met optimaal comfort en lagere energiekosten."
        },
        "comfort_narratives": {
            "winter": "Geen koude voeten meer in de winter, geen tocht meer bij de ramen - eindelijk het comfort dat u verdient.",
            "summer": "Een aangenaam koel huis in de zomer zonder torenhoge energierekeningen.",
            "year_round": "Het hele jaar door een constant, aangenaam binnenklimaat zonder zorgen over de energierekening."
        },
        "environmental_stories": {
            "high_impact": "Uw bijdrage aan een duurzame toekomst is substantieel - vergelijkbaar met het dagelijks uit het verkeer halen van een auto.",
            "family_legacy": "Een belangrijke stap voor de toekomst van uw kinderen en kleinkinderen.",
            "community_leader": "U geeft het goede voorbeeld in uw buurt en draagt bij aan de Nederlandse klimaatdoelen."
        }
    }


@mcp.tool()
def combine_template_sections(session_id: str, deal_id: str) -> Dict[str, Any]:
    """
    Combine all saved template sections into a complete HTML file.
    
    Args:
        session_id: Session ID used when saving sections
        deal_id: Deal ID for the final filename
        
    Returns:
        Dict with the final file path
    """
    try:
        session_dir = SERVER_DIR / "outputs" / f"session_{session_id}"
        if not session_dir.exists():
            return {
                "success": False,
                "error": f"Session directory not found: {session_id}"
            }
        
        # Define section order
        section_order = [
            "hero",
            "customer", 
            "current_situation",
            "products",
            "financial",
            "environmental",
            "footer"
        ]
        
        # Load base template structure
        template_html = load_template("bespaarplan_magazine.html")
        
        # Get the HTML structure before the first section
        first_section_marker = "<!-- SECTION: HERO -->"
        header_idx = template_html.find(first_section_marker)
        html_header = template_html[:header_idx] if header_idx > -1 else '<!DOCTYPE html>\n<html lang="nl">\n<head>\n'
        
        # Get the HTML structure after the last section
        last_section_marker = "<!-- END SECTION: FOOTER -->"
        footer_idx = template_html.find(last_section_marker)
        html_footer = template_html[footer_idx + len(last_section_marker):] if footer_idx > -1 else '\n</body>\n</html>'
        
        # Combine sections
        combined_html = html_header
        
        for section in section_order:
            section_file = session_dir / f"{section}.html"
            if section_file.exists():
                with open(section_file, 'r', encoding='utf-8') as f:
                    combined_html += f.read() + "\n"
        
        combined_html += html_footer
        
        # Save combined file
        outputs_dir = SERVER_DIR / "outputs"
        final_file = outputs_dir / f"bespaarplan_{deal_id}.html"
        with open(final_file, 'w', encoding='utf-8') as f:
            f.write(combined_html)
        
        # Clean up session directory
        import shutil
        shutil.rmtree(session_dir)
        
        return {
            "success": True,
            "file_path": str(final_file),
            "size_kb": len(combined_html) / 1024
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to combine sections: {str(e)}"
        }


@mcp.tool()
async def generate_and_upload_template(template_data: Dict[str, Any], deal_id: str, customer_last_name: str) -> Dict[str, Any]:
    """
    Generate a filled bespaarplan template and upload it directly to Supabase storage.
    
    This combined tool eliminates the need to pass large HTML content through multiple agents,
    significantly reducing token usage and improving performance.
    
    Args:
        template_data: Complete data structure with all placeholders to fill
        deal_id: The deal ID for file naming and database update
        customer_last_name: Customer's last name for folder structure
    
    Returns:
        Dict containing:
        - success: bool
        - public_url: The CDN URL for the uploaded file
        - file_path: The storage path ({last_name}-{deal_id}/bespaarplan-{deal_id}.html)
        - size_kb: File size in KB
        - uploaded_at: Upload timestamp
        - database_updated: Whether the database was updated successfully
    """
    try:
        logger.info(f"Starting generate_and_upload_template for deal {deal_id}")
        logger.info(f"Customer last name: {customer_last_name}")
        logger.info(f"Template data keys: {list(template_data.keys())[:20]}...")  # Log first 20 keys
        
        # Load the template
        template_html = load_template("bespaarplan_magazine.html")
        logger.info(f"Template loaded, size: {len(template_html)} bytes")
        
        # Pass raw data to Jinja2 - keep numeric values for calculations
        processed_data = dict(template_data)
        
        # Use Jinja2 to properly render the template
        try:
            # Create custom filter for Dutch number formatting
            def dutch_format(value):
                """Format numbers with Dutch thousand separators (dots)"""
                if isinstance(value, (int, float)):
                    return f"{int(value):,}".replace(',', '.')
                return value
            
            # Create Jinja2 environment with custom filter
            env = Environment()
            env.filters['dutch_format'] = dutch_format
            
            # Create template from environment
            jinja_template = env.from_string(template_html)
            filled_html = jinja_template.render(**processed_data)
            logger.info("Template rendered successfully with Jinja2")
        
            # Log unfilled placeholders for debugging
            import re
            remaining_placeholders = re.findall(r'\{\{([^}]+)\}\}', filled_html)
            if remaining_placeholders:
                logger.warning(f"Unfilled placeholders found ({len(remaining_placeholders)}): {remaining_placeholders[:10]}")
        except Exception as e:
            logger.error(f"Jinja2 template rendering failed: {str(e)}")
            return {
                "success": False,
                "error": f"Template rendering failed: {str(e)}"
            }
        
        # Prepare file path
        folder_name = f"{customer_last_name.lower().replace(' ', '-')}-{deal_id}"
        filename = f"bespaarplan-{deal_id}.html"
        file_path = f"{folder_name}/{filename}"
        
        # Convert HTML to bytes
        html_bytes = filled_html.encode('utf-8')
        
        if DEMO_MODE:
            # Demo mode: save locally
            logger.info("Running in DEMO_MODE - saving locally")
            outputs_dir = SERVER_DIR / "outputs"
            outputs_dir.mkdir(exist_ok=True)
            demo_file = outputs_dir / f"demo_{filename}"
            with open(demo_file, 'w', encoding='utf-8') as f:
                f.write(filled_html)
            
            return {
                "success": True,
                "public_url": f"demo://storage/{file_path}",
                "file_path": file_path,
                "size_kb": len(html_bytes) / 1024,
                "uploaded_at": datetime.now().isoformat(),
                "database_updated": True
            }
        
        # Check if we have required credentials
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            logger.error(f"Missing credentials: URL={bool(SUPABASE_URL)}, SERVICE_KEY={bool(SUPABASE_SERVICE_KEY)}")
            return {
                "success": False,
                "error": f"Missing Supabase credentials"
            }
        
        # Upload to Supabase storage
        upload_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{file_path}"
        logger.info(f"Upload URL: {upload_url}")
        logger.info(f"File size: {len(html_bytes)} bytes")
        logger.info(f"Auth header length: {len(SUPABASE_SERVICE_KEY)}")
        logger.info(f"SUPABASE_URL: {SUPABASE_URL}")
        logger.info(f"BUCKET_NAME: {BUCKET_NAME}")
        
        headers = {
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "text/html",  # Simplified mime type
            "x-upsert": "true"  # Create folders if they don't exist
        }
        
        logger.info("Uploading to Supabase storage...")
        logger.info(f"Full upload URL: {upload_url}")
        logger.info(f"Headers (excluding auth): Content-Type={headers.get('Content-Type')}, x-upsert={headers.get('x-upsert')}")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    upload_url,
                    content=html_bytes,
                    headers=headers,
                    timeout=30.0
                )
            
            logger.info(f"Upload response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            if response.status_code not in [200, 201]:
                logger.error(f"Upload failed: {response.status_code} - {response.text}")
                logger.error(f"Failed URL was: {upload_url}")
                return {
                    "success": False,
                    "error": f"Upload failed with status {response.status_code}: {response.text}"
                }
        except Exception as e:
            logger.error(f"Upload exception: {type(e).__name__}: {str(e)}")
            return {
                "success": False,
                "error": f"Upload exception: {str(e)}"
            }
        
        # Generate public URL
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{file_path}"
        logger.info(f"Upload successful! Public URL: {public_url}")
        
        # Update database with bespaarplan info
        database_updated = False
        try:
            if supabase:
                update_data = {
                    "bespaarplan_url": public_url,
                    "bespaarplan_generated_at": datetime.now().isoformat(),
                    "bespaarplan_status": "completed"
                }
                
                logger.info(f"Updating database for deal {deal_id}")
                response = supabase.table('deals') \
                    .update(update_data) \
                    .eq('id', deal_id) \
                    .execute()
                
                database_updated = True
                logger.info(f"Database updated successfully for deal {deal_id}")
            else:
                logger.warning("Supabase client not available for database update")
        except Exception as db_error:
            logger.error(f"Database update failed for deal {deal_id}: {str(db_error)}")
            # Continue - upload succeeded even if DB update failed
        
        # Also save locally for reference
        outputs_dir = SERVER_DIR / "outputs"
        outputs_dir.mkdir(exist_ok=True)
        local_file = outputs_dir / f"{filename}"
        with open(local_file, 'w', encoding='utf-8') as f:
            f.write(filled_html)
        
        logger.info(f"Template generation complete for deal {deal_id}")
        result = {
            "success": True,
            "deal_id": deal_id,
            "public_url": public_url,
            "file_path": file_path,
            "filename": filename,
            "size_kb": len(html_bytes) / 1024,
            "uploaded_at": datetime.now().isoformat(),
            "database_updated": database_updated
        }
        logger.info(f"Returning result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate and upload template: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to generate and upload template: {str(e)}"
        }


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()