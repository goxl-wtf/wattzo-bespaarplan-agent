"""
Main agents for the Wattzo Bespaarplan system.

This module implements a single powerful agent that handles the complete
bespaarplan generation workflow using MCP servers.
"""

import logging
from typing import Dict, Any, Optional
from mcp_agent.core.fastagent import FastAgent
from mcp_agent import RequestParams

logger = logging.getLogger(__name__)

def create_fast_agent() -> FastAgent:
    """
    Create and configure the FastAgent instance.
    This should be called once during application startup.
    """
    # Initialize FastAgent instance with parse_cli_args=False for API integration
    fast = FastAgent("wattzo-bespaarplan-generator", parse_cli_args=False)
    
    # Define the agent on the instance before returning
    _define_bespaarplan_agent(fast)
    
    return fast

def _define_bespaarplan_agent(fast: FastAgent):
    """Define the bespaarplan generator agent on the FastAgent instance."""
    
    # Single agent approach: One powerful agent that does everything
    @fast.agent(
        name="bespaarplan_generator",
    instruction="""YOU MUST COMPLETE ALL 3 STEPS BELOW. DO NOT STOP UNTIL ALL STEPS ARE DONE.

    === STEP 1 OF 3: FETCH DATA ===
    1. Call get_comprehensive_deal_data(deal_id) from energy-data MCP
    2. Extract customer data including customer.last_name for file naming
    3. Report: "STEP 1 COMPLETE - Data fetched for [customer_name]"
    
    === STEP 2 OF 3: CALCULATE METRICS ===  
    1. Call calculate_from_deal_data(comprehensive_data) from calculation-engine MCP
    2. Verify calculations include monthly_payment (loan payment €X/month)
    3. Report: "STEP 2 COMPLETE - Metrics calculated"
    
    === STEP 3 OF 3: GENERATE & UPLOAD BESPAARPLAN ===
    1. Create template_data dict with ALL mappings (use exact keys as shown):
       
       **Customer & Property Data**:
       - customer_name: comprehensive_data.customer.name
       - customer_salutation: Extract only title from salutation (e.g., "Geachte mevrouw" → "mevrouw", "Geachte heer" → "meneer")
       - customer_lastname: comprehensive_data.customer.last_name
       - customer_email: comprehensive_data.customer.email
       - property_address: comprehensive_data.customer.address (NOT customer_address!)
       - property_city: comprehensive_data.customer.city
       - property_size: comprehensive_data.property.area
       - property_year: comprehensive_data.property.year
       - property_value: 780000
       - property_value_current: metrics.property_value_impact.current_value
       - property_value_after: metrics.property_value_impact.projected_value
       - property_value_increase: metrics.property_value_impact.value_increase
       - advisor_name: comprehensive_data.advisor.name or "uw WattZo adviseur"
       
       **Energy Usage Data** (from comprehensive_data.energy.usage):
       - gas_usage_current: comprehensive_data.energy.usage.gas_m3
       - electricity_usage_current: comprehensive_data.energy.usage.electricity_kwh
       - gas_usage_after: gas_usage_current - metrics.basic_metrics.energy_savings.gas_m3
       - electricity_usage_gross_after: electricity_usage_current + metrics.basic_metrics.energy_savings.electricity_kwh
       - electricity_usage_net_after: metrics.basic_metrics.financial_impact.net_electricity_usage_kwh
       - solar_production: metrics.basic_metrics.energy_savings.solar_production_kwh
       - gas_savings_pct: round((metrics.basic_metrics.energy_savings.gas_m3 / gas_usage_current) * 100)
       - electricity_savings_pct: Calculate net savings percentage
       
       **Energy Costs & Labels**:
       - current_energy_costs: comprehensive_data.energy.costs.total_yearly
       - energy_costs_after: current_energy_costs - metrics.basic_metrics.financial_impact.annual_savings
       - energy_label_current: comprehensive_data.property.energy_label (NOT current_energy_label!)
       - energy_label_after: metrics.energy_label.new (NOT new_energy_label!)
       
       **Financial Metrics** (from metrics):
       - total_investment: metrics.summary.total_investment
       - total_subsidies: metrics.summary.total_subsidies
       - net_investment: metrics.summary.net_investment
       - annual_savings: metrics.summary.annual_savings
       - monthly_savings: metrics.summary.monthly_savings
       - monthly_payment: metrics.financing_metrics.monthly_payment or (net_investment / 180)
       - monthly_cashflow: monthly_savings - monthly_payment
       - loan_interest: 0 (Warmtefonds is always 0%)
       - payback_years: metrics.summary.payback_period
       - roi_20_years: metrics.summary.roi_20_years
       - total_profit_20_years: metrics.basic_metrics.financial_impact.total_profit_20_years
       
       **CO2 & Environmental** (from metrics.co2_equivalents):
       - co2_reduction: metrics.summary.co2_reduction_annual
       - co2_reduction_pct: metrics.summary.co2_reduction_percentage
       - co2_trees: metrics.co2_equivalents.trees_equivalent
       - co2_car_km: metrics.co2_equivalents.car_km_equivalent
       - co2_flights: str(metrics.co2_equivalents.flights) + " vluchten"
       
       **Products**: Map each product from metrics.products_with_metrics:
       - products: [
           {
             "name": product.name,
             "description": product.description,
             "cost": product.total_price,
             "subsidy": product.subsidy,
             "impact": product.environmental_impact or "Vermindert CO₂ uitstoot",
             "benefit": product.comfort_benefit or "Verhoogt comfort en bespaart energie"
           }
           for product in metrics.products_with_metrics
         ]
       
       **Customer Wishes**: Convert to full sentences
       - customer_wishes: Transform each wish into a sentence:
         - "Energiebesparing" → "U wilt graag besparen op uw energiekosten"
         - "Comfort verbetering" → "Een comfortabeler binnenklimaat is belangrijk voor u"
         - "Milieuvriendelijk wonen" → "U hecht waarde aan duurzaam en milieuvriendelijk wonen"
         - "Waardestijging woning" → "U ziet verduurzaming als investering in uw woning"
         - "cost_savings" → "U wilt graag besparen op uw energiekosten"
         - "comfort" → "Een comfortabeler binnenklimaat is belangrijk voor u"
         - "environmental" → "U hecht waarde aan duurzaam en milieuvriendelijk wonen"
         - Default: Keep original wish text if not in mapping
       
       **Narratives**: Generate these four rich narratives based on ACTUAL data:
       CRITICAL: Generate COMPLETE narrative text with actual values. NO template syntax like {value} or {{value}}!
       
       1. **energy_situation_narrative** (2-3 paragraphs):
          Generate ACTUAL narrative text with real values embedded (NO template syntax):
          Example: "Uw woning verbruikt momenteel 1301 m³ gas per jaar, wat redelijk in lijn ligt met vergelijkbare woningen uit 1927. Door over te stappen op een hybride warmtepomp wordt uw gasverbruik teruggebracht naar slechts 370 m³ - een besparing van 72%. Het stroomverbruik stijgt weliswaar van 818 naar 3069 kWh, maar het netto resultaat is een energiebesparing van €686 per jaar. Uw woning maakt de sprong van energielabel D naar C - een prestatie waar u trots op mag zijn!"
       
       2. **personal_savings_story** (3-4 paragraphs):
          Generate COMPLETE story with actual calculated values (NO curly braces):
          Example: "Stel u voor: elke maand houdt u €57 over in uw portemonnee. Dit is geen toekomstdroom, maar realiteit zodra uw nieuwe installaties zijn geplaatst. Met de Warmtefonds-lening betaalt u slechts €46 per maand tegen 0% rente, terwijl u €57 bespaart op uw energierekening. U houdt dus direct €11 per maand over! En na 15 jaar, wanneer de lening is afbetaald, profiteert u van de volledige €57 besparing elke maand. Over 20 jaar heeft u maar liefst €5.395 verdiend met deze investering."
       
       3. **property_value_narrative** (2 paragraphs):
          Generate COMPLETE narrative with calculated values (NO template syntax):
          Example: "In 's-Gravenhage zien we dat kopers steeds vaker bereid zijn extra te betalen voor energiezuinige woningen. Uw woning heeft momenteel een waarde van €780.000. Volgens de laatste cijfers van Brainbay levert de sprong van label D naar C een waardestijging van 3,5% op. Dit betekent dat uw woning na de verduurzaming €807.300 waard wordt. De waardestijging van €27.300 is maar liefst 3,3x hoger dan uw netto investering van €8.325."
       
       4. **customer_emphasis_class**: Based on primary customer wish:
          - If "cost_savings" in wishes → "emphasis-savings"
          - If "comfort" in wishes → "emphasis-comfort"  
          - If "environment" in wishes → "emphasis-green"
          - Default → "emphasis-savings"
       
       **Narrative Guidelines**:
       - Write for any household type - avoid demographic assumptions
       - Focus on universal benefits: comfort, savings, sustainability
       - Use property characteristics (year, size, location) rather than assumed lifestyle
       - Keep language inclusive and professional
       - Each narrative should be substantial and engaging, not one-liners
    
    2. Keep all values as raw numbers - formatting will be handled by the template
       - Do NOT format numbers to strings
       - Pass numeric values as-is (integers or floats)
       - The template will handle Dutch number formatting for display
       
    3. Call generate_and_upload_template(template_data, deal_id, customer_last_name) from template-provider MCP
       - template_data: The complete dict with all mappings above
       - deal_id: The deal ID from input
       - customer_last_name: comprehensive_data.customer.last_name
       IMPORTANT: The upload will use bucket "bespaarplan-reports" - this is configured in the MCP server
       
    4. Report: "STEP 3 COMPLETE - Bespaarplan uploaded"
    
    **Data Usage Rules**:
    - Only use information explicitly provided in the deal data
    - Do NOT infer age, family composition, or lifestyle from limited data
    - When demographic data is missing, use neutral language ("u", "uw huishouden")
    - Trust MCP calculations - don't recalculate values
    
    === FINAL VERIFICATION ===
    Confirm you have:
    ✓ Fetched data (Step 1)
    ✓ Calculated metrics (Step 2) 
    ✓ Generated and uploaded bespaarplan (Step 3)
    
    Return the final result with public_url from Step 3.
    
    CRITICAL: YOU MUST EXECUTE ALL 3 STEPS. DO NOT STOP EARLY.""",
    servers=["energy-data", "calculation-engine", "template-provider"],
    model="claude-sonnet-4-20250514",
    request_params=RequestParams(
        maxTokens=64000,   # Maximum for Claude Sonnet 4
        temperature=0.1,   # Low temperature for consistency
        max_iterations=20  # Allow multiple turns to complete all steps
    ),
    use_history=False  # Prevent data contamination between runs
)
    async def _agent_function():
        # This function is needed for the decorator but not used directly
        pass


async def generate_bespaarplan_with_agent(agent_app, deal_id: str) -> Dict[str, Any]:
    """
    Generate a complete bespaarplan for a specific deal using the provided agent instance.
    
    Args:
        agent_app: The initialized AgentApp instance from FastAgent
        deal_id: The unique identifier of the deal
        
    Returns:
        Dict containing the result of the bespaarplan generation
    """
    logger.info(f"Starting bespaarplan generation for deal: {deal_id}")
    
    try:
        # Use the provided agent instance (already initialized)
        result = await agent_app.bespaarplan_generator.send(
            f"Generate complete bespaarplan for deal_id: {deal_id}"
        )
        
        # Extract the public URL from the result if it's a string response
        if isinstance(result, str):
            # Try to parse the URL from the response
            import re
            url_match = re.search(r'https://[^\s]+\.html', result)
            bespaarplan_url = url_match.group(0) if url_match else ""
        else:
            bespaarplan_url = result.get("public_url", "") if isinstance(result, dict) else ""
        
        logger.info(f"Bespaarplan generation completed for deal: {deal_id}")
        return {
            "success": True,
            "deal_id": deal_id,
            "bespaarplan_url": bespaarplan_url,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Failed to generate bespaarplan for deal {deal_id}: {str(e)}", exc_info=True)
        return {
            "success": False,
            "deal_id": deal_id,
            "error": str(e)
        }

# Note: The old synchronous wrapper and standalone generation functions have been removed.
# The API now uses a single FastAgent instance initialized at startup.