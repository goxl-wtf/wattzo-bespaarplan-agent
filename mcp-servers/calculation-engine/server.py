#!/usr/bin/env python3
"""
Calculation Engine MCP Server
Provides tools for energy savings calculations and financial projections
Based on actual products in quotes and real Dutch energy calculations
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import math
from supabase import create_client, Client

from fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("CalculationEngine")

# Demo mode flag
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not DEMO_MODE and (not SUPABASE_URL or not SUPABASE_KEY):
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set when DEMO_MODE=false")

supabase: Optional[Client] = None
if not DEMO_MODE:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Constants for calculations
GAS_CO2_FACTOR = 1.78  # kg CO2 per m³ gas (CBS official figure)
ELECTRICITY_CO2_FACTOR = 0.4  # kg CO2 per kWh (Dutch grid average)
SOLAR_PRODUCTION_FACTOR = 900  # kWh per kWp per year in Netherlands
ENERGY_PRICE_INFLATION = 0.04  # 4% annual energy price increase (Dutch historical average)
DISCOUNT_RATE = 0.03  # 3% discount rate for NPV calculations
DEFAULT_WOZ_VALUE = 450000  # Average Dutch home value (CBS 2024)

# Property value increase matrix based on energy label improvement (Brainbay Q3 2024)
# Format: {(from_label, to_label): percentage_increase}
WOZ_INCREASE_MATRIX = {
    # From A
    ('A', 'A+'): 0.031,  # 3.1%
    # From B
    ('B', 'A+'): 0.058,  # 5.8%
    ('B', 'A'): 0.026,   # 2.6%
    # From C
    ('C', 'A+'): 0.084,  # 8.4%
    ('C', 'A'): 0.051,   # 5.1%
    ('C', 'B'): 0.024,   # 2.4%
    # From D
    ('D', 'A+'): 0.110,  # 11.0%
    ('D', 'A'): 0.110,   # 11.0% (same as A+)
    ('D', 'B'): 0.049,   # 4.9%
    ('D', 'C'): 0.025,   # 2.5%
    # From E
    ('E', 'A+'): 0.102,  # 10.2% (marked with * - steps >4 removed)
    ('E', 'A'): 0.102,   # 10.2%
    ('E', 'B'): 0.073,   # 7.3%
    ('E', 'C'): 0.049,   # 4.9%
    ('E', 'D'): 0.023,   # 2.3%
    # From F
    ('F', 'A+'): 0.099,  # 9.9% (marked with * - steps >4 removed)
    ('F', 'A'): 0.099,   # 9.9%
    ('F', 'B'): 0.099,   # 9.9% (marked with *)
    ('F', 'C'): 0.073,   # 7.3%
    ('F', 'D'): 0.047,   # 4.7%
    ('F', 'E'): 0.023,   # 2.3%
    # From G
    ('G', 'A+'): 0.097,  # 9.7% (marked with * - steps >4 removed)
    ('G', 'A'): 0.097,   # 9.7%
    ('G', 'B'): 0.097,   # 9.7% (marked with *)
    ('G', 'C'): 0.097,   # 9.7% (marked with *)
    ('G', 'D'): 0.070,   # 7.0%
    ('G', 'E'): 0.045,   # 4.5%
    ('G', 'F'): 0.022,   # 2.2%
}

# Dutch energy conversion constants
DUTCH_GAS_CONSTANTS = {
    "ENERGY_CONTENT_KWH_PER_M3": 9.77,  # CBS official figure for Netherlands
    "BOILER_EFFICIENCY": 0.85,  # Real-world efficiency of gas boilers (85%)
    "USEFUL_HEAT_PER_M3": 8.3,  # 9.77 × 0.85
}

# Heat pump COP values for different scenarios
HEAT_PUMP_COP = {
    "HYBRID_CONSERVATIVE": 3.5,
    "HYBRID_OPTIMAL": 4.0,
    "ALL_ELECTRIC_OLD_HOUSE": 3.0,  # Pre-2000 houses
    "ALL_ELECTRIC_MEDIUM_HOUSE": 3.5,  # 2000-2010 houses
    "ALL_ELECTRIC_NEW_HOUSE": 4.0,  # Post-2010 houses
    "DEFAULT": 3.5,  # Conservative default
}


def calculate_savings_impl(
    deal_id: str,
    energy_profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate energy and financial savings for products in the deal's quote
    Based on actual products selected and current energy usage
    """
    if DEMO_MODE:
        # Demo calculations
        current_gas = energy_profile['current_usage']['gas']
        current_electricity = energy_profile['current_usage']['electricity']
        
        # Simulate savings based on typical product impacts
        gas_savings = current_gas * 0.45  # 45% reduction from insulation + hybrid heat pump
        electricity_increase = 800  # kWh increase from hybrid heat pump
        solar_production = 3600  # kWh from solar panels
        
        # Financial calculations
        gas_cost_savings = gas_savings * energy_profile['tariffs']['gas']
        electricity_cost_change = -electricity_increase * energy_profile['tariffs']['electricity']
        solar_income = solar_production * energy_profile['tariffs']['return']
        total_annual_savings = gas_cost_savings + electricity_cost_change + solar_income
        
        # CO2 calculations
        co2_gas_reduction = gas_savings * GAS_CO2_FACTOR
        co2_electricity_change = -electricity_increase * ELECTRICITY_CO2_FACTOR
        co2_solar_offset = solar_production * ELECTRICITY_CO2_FACTOR
        total_co2_reduction = co2_gas_reduction + co2_electricity_change + co2_solar_offset
        
        return {
            'energy_savings': {
                'gas_m3': round(gas_savings),
                'electricity_kwh': round(-electricity_increase),  # Negative means increase
                'electricity_increase_kwh': round(electricity_increase),
                'solar_production_kwh': round(solar_production),
                'co2_reduction_kg': round(total_co2_reduction)
            },
            'financial_impact': {
                'annual_savings': round(total_annual_savings, 2),
                'monthly_savings': round(total_annual_savings / 12, 2),
                'gas_cost_reduction': round(gas_cost_savings, 2),
                'electricity_cost_change': round(electricity_cost_change, 2),
                'solar_income': round(solar_income, 2),
                'total_investment': 8070,  # Demo value
                'total_subsidies': 3500,  # Demo value
                'net_investment': 4570,  # Demo value
                'payback_years': 12.5,  # Demo value
                'roi_20_years': 1.8,  # 180% return
                'npv_20_years': 15000  # Net present value
            },
            'products_analyzed': 3,
            'calculation_details': {
                'based_on_quote': 'quote-123',
                'includes_actual_products': True,
                'calculation_date': datetime.now().isoformat()
            }
        }
    
    # Real mode - fetch from Supabase and calculate
    try:
        # 1. Get quote items with products and quote data
        deal_response = supabase.table('deals') \
            .select('final_quote_id, quote_id') \
            .eq('id', deal_id) \
            .single() \
            .execute()
        
        if not deal_response.data:
            return {"error": "Deal not found", "deal_id": deal_id}
        
        deal = deal_response.data
        quote_id = deal['final_quote_id'] or deal['quote_id']
        
        # Get quote data for totals
        quote_response = supabase.table('quotes') \
            .select('*') \
            .eq('id', quote_id) \
            .single() \
            .execute()
        
        quote_data = quote_response.data if quote_response.data else {}
        
        quote_items_response = supabase.table('quote_items') \
            .select('*, products!inner(*)') \
            .eq('quote_id', quote_id) \
            .execute()
        
        if not quote_items_response.data:
            return {"error": "No products found in quote"}
        
        # 2. Calculate savings per product
        total_savings = {
            'gas_m3': 0,
            'electricity_kwh': 0,
            'electricity_increase_kwh': 0,
            'solar_production_kwh': 0,
            'co2_reduction_kg': 0
        }
        
        total_investment = 0
        total_subsidies = 0
        
        for item in quote_items_response.data:
            product = item['products']
            quantity = item['quantity']
            
            # Get savings from product calculation
            savings = calculate_product_savings(
                product=product,
                quantity=quantity,
                current_usage=energy_profile['current_usage'],
                house_data=energy_profile['house_profile']
            )
            
            # Aggregate savings
            total_savings['gas_m3'] += savings.get('gas_m3', 0)
            total_savings['electricity_kwh'] += savings.get('electricity_kwh', 0)
            if savings.get('electricity_kwh', 0) < 0:
                total_savings['electricity_increase_kwh'] += abs(savings['electricity_kwh'])
            total_savings['solar_production_kwh'] += savings.get('solar_production_kwh', 0)
            total_savings['co2_reduction_kg'] += savings.get('co2_reduction_kg', 0)
            
            # Track financials
            total_investment += item['total_item_price_incl_vat']
            # Note: item subsidies are accumulated but we'll use quote total
        
        # Use actual subsidy total from quote
        total_subsidies = float(quote_data.get('total_subsidy_estimate', 0))
        
        # Check if we have a hybrid heat pump - needed for corrections
        has_hybrid_heat_pump = any(
            'hybride' in item['products'].get('name', '').lower() and 
            'warmtepomp' in item['products'].get('name', '').lower() 
            for item in quote_items_response.data
        )
        
        # Use actual CO2 savings from quote if available
        # BUT: Check if we have a hybrid heat pump - quotes often incorrectly show too high CO2 reduction
        if quote_data.get('estimated_co2_savings_kg'):
            quote_co2_savings = float(quote_data.get('estimated_co2_savings_kg', 0))
            quote_gas_savings = float(quote_data.get('estimated_gas_savings_m3', 0))
            # If we corrected gas savings for hybrid heat pump, recalculate CO2
            if has_hybrid_heat_pump and quote_gas_savings >= energy_profile['current_usage']['gas']:
                # Recalculate CO2 based on corrected gas savings
                corrected_gas_co2 = total_savings['gas_m3'] * GAS_CO2_FACTOR
                electricity_co2 = abs(total_savings['electricity_kwh']) * ELECTRICITY_CO2_FACTOR
                solar_co2 = total_savings['solar_production_kwh'] * ELECTRICITY_CO2_FACTOR
                total_savings['co2_reduction_kg'] = corrected_gas_co2 - electricity_co2 + solar_co2
            else:
                total_savings['co2_reduction_kg'] = quote_co2_savings
        
        # Use actual gas/electricity savings from quote if available
        # BUT: Check if we have a hybrid heat pump - quotes often incorrectly show 100% gas reduction
        if quote_data.get('estimated_gas_savings_m3'):
            quote_gas_savings = float(quote_data.get('estimated_gas_savings_m3', 0))
            # If quote shows 100% gas reduction but we have hybrid heat pump, cap at 70%
            if has_hybrid_heat_pump and quote_gas_savings >= energy_profile['current_usage']['gas']:
                # Hybrid heat pumps typically save 60-70% of gas usage
                total_savings['gas_m3'] = energy_profile['current_usage']['gas'] * 0.70
            else:
                total_savings['gas_m3'] = quote_gas_savings
                
        if quote_data.get('estimated_electricity_savings_kwh'):
            # This might include solar production, so we need to be careful
            electricity_from_quote = float(quote_data.get('estimated_electricity_savings_kwh', 0))
            # If we have solar, the quote value includes production
            if total_savings['solar_production_kwh'] > 0:
                total_savings['electricity_kwh'] = electricity_from_quote
            
        # 3. Calculate financial impact
        tariffs = energy_profile['tariffs']
        
        gas_cost_savings = total_savings['gas_m3'] * tariffs['gas']
        electricity_cost_change = total_savings['electricity_kwh'] * tariffs['electricity']
        solar_income = total_savings['solar_production_kwh'] * tariffs['return']
        total_annual_savings = gas_cost_savings + electricity_cost_change + solar_income
        
        # Payback and ROI calculations
        net_investment = total_investment - total_subsidies
        payback_years = net_investment / total_annual_savings if total_annual_savings > 0 else 999
        
        # NPV calculation (simplified, 3% discount rate)
        discount_rate = 0.03
        npv = 0
        for year in range(1, 21):
            # Assume 2% energy price increase per year
            savings_in_year = total_annual_savings * (1.02 ** year)
            discounted_value = savings_in_year / ((1 + discount_rate) ** year)
            npv += discounted_value
        npv -= net_investment
        
        roi_20_years = (npv + net_investment) / net_investment if net_investment > 0 else 0
        
        return {
            'energy_savings': {
                'gas_m3': round(total_savings['gas_m3']),
                'electricity_kwh': round(total_savings['electricity_kwh']),
                'electricity_increase_kwh': round(total_savings['electricity_increase_kwh']),
                'solar_production_kwh': round(total_savings['solar_production_kwh']),
                'co2_reduction_kg': round(total_savings['co2_reduction_kg'])
            },
            'financial_impact': {
                'annual_savings': round(total_annual_savings, 2),
                'monthly_savings': round(total_annual_savings / 12, 2),
                'gas_cost_reduction': round(gas_cost_savings, 2),
                'electricity_cost_change': round(electricity_cost_change, 2),
                'solar_income': round(solar_income, 2),
                'total_investment': round(total_investment, 2),
                'total_subsidies': round(total_subsidies, 2),
                'net_investment': round(net_investment, 2),
                'payback_years': round(payback_years, 1),
                'roi_20_years': round(roi_20_years, 2),
                'npv_20_years': round(npv, 2)
            },
            'products_analyzed': len(quote_items_response.data),
            'calculation_details': {
                'based_on_quote': quote_id,
                'includes_actual_products': True,
                'calculation_date': datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        return {
            "error": f"Failed to calculate savings: {str(e)}",
            "deal_id": deal_id
        }


def calculate_product_savings(
    product: Dict[str, Any],
    quantity: float,
    current_usage: Dict[str, float],
    house_data: Dict[str, Any]
) -> Dict[str, float]:
    """
    Calculate savings for a specific product based on its category and specifications
    """
    savings = {
        'gas_m3': 0,
        'electricity_kwh': 0,
        'solar_production_kwh': 0,
        'co2_reduction_kg': 0
    }
    
    category = product.get('category', '')
    name = product.get('name', '').lower()
    
    if category == 'Insulation':
        # Default savings percentages by insulation type
        savings_map = {
            'spouwmuurisolatie': 0.20,  # 20% gas reduction
            'dakisolatie': 0.25,        # 25% gas reduction
            'vloerisolatie': 0.15,      # 15% gas reduction
            'bodemisolatie': 0.15       # 15% gas reduction
        }
        
        # Find matching percentage
        base_percentage = 0.10  # Default 10%
        for key, percentage in savings_map.items():
            if key in name:
                base_percentage = percentage
                break
        
        # Calculate gas savings (percentage applies once, not per m²)
        gas_savings = current_usage['gas'] * base_percentage
        co2_savings = gas_savings * GAS_CO2_FACTOR
        
        savings['gas_m3'] = gas_savings
        savings['co2_reduction_kg'] = co2_savings
        
    elif category == 'Heating':
        if 'hybride' in name and 'warmtepomp' in name:
            # Hybrid heat pump: 60% gas reduction
            gas_reduction = current_usage['gas'] * 0.60
            
            # Get actual COP from technical specs
            technical_specs = product.get('technical_specs', {})
            cop = technical_specs.get('cop_heating', technical_specs.get('scop', None))
            
            # If no COP in specs, use building year based defaults
            if not cop:
                building_year = house_data.get('year', 2000)
                if building_year > 2010:
                    cop = HEAT_PUMP_COP['HYBRID_OPTIMAL']
                else:
                    cop = HEAT_PUMP_COP['HYBRID_CONSERVATIVE']
            
            # Electricity needed = Gas replaced × useful heat per m³ ÷ COP
            electricity_increase = (gas_reduction * DUTCH_GAS_CONSTANTS['USEFUL_HEAT_PER_M3']) / cop
            
            savings['gas_m3'] = gas_reduction
            savings['electricity_kwh'] = -electricity_increase  # Negative = increase
            
            # Net CO2 reduction (gas reduction - electricity increase)
            co2_reduction = (gas_reduction * GAS_CO2_FACTOR) - (electricity_increase * ELECTRICITY_CO2_FACTOR)
            savings['co2_reduction_kg'] = co2_reduction
            
        elif 'warmtepomp' in name and 'hybride' not in name:
            # All-electric heat pump: 100% gas reduction
            gas_reduction = current_usage['gas']
            
            # Determine COP based on house age
            building_year = house_data.get('year', 2000)
            if building_year > 2010:
                cop = HEAT_PUMP_COP['ALL_ELECTRIC_NEW_HOUSE']
            elif building_year > 2000:
                cop = HEAT_PUMP_COP['ALL_ELECTRIC_MEDIUM_HOUSE']
            else:
                cop = HEAT_PUMP_COP['ALL_ELECTRIC_OLD_HOUSE']
            
            electricity_increase = (gas_reduction * DUTCH_GAS_CONSTANTS['USEFUL_HEAT_PER_M3']) / cop
            
            savings['gas_m3'] = gas_reduction
            savings['electricity_kwh'] = -electricity_increase
            
            co2_reduction = (gas_reduction * GAS_CO2_FACTOR) - (electricity_increase * ELECTRICITY_CO2_FACTOR)
            savings['co2_reduction_kg'] = co2_reduction
    
    elif category == 'Solar':
        if 'zonnepanelen' in name or 'solar' in name:
            # Get kWp from technical specs or calculate from quantity
            technical_specs = product.get('technical_specs', {})
            # Check for power_wp or kwp_per_unit
            power_wp = technical_specs.get('power_wp', technical_specs.get('kwp_per_unit', 455))
            # Convert Wp to kWp
            kwp_per_panel = power_wp / 1000.0
            total_kwp = kwp_per_panel * quantity
            
            # Calculate production: 900 kWh per kWp in Netherlands
            annual_production = total_kwp * SOLAR_PRODUCTION_FACTOR
            
            savings['solar_production_kwh'] = annual_production
            savings['electricity_kwh'] = annual_production  # Positive = generation
            savings['co2_reduction_kg'] = annual_production * ELECTRICITY_CO2_FACTOR
    
    elif category == 'Glass':
        if 'hr++' in name:
            # HR++ glass: 8% gas reduction
            gas_reduction = current_usage['gas'] * 0.08
            savings['gas_m3'] = gas_reduction
            savings['co2_reduction_kg'] = gas_reduction * GAS_CO2_FACTOR
        elif 'triple' in name or 'hr+++' in name:
            # Triple glass: 12% gas reduction
            gas_reduction = current_usage['gas'] * 0.12
            savings['gas_m3'] = gas_reduction
            savings['co2_reduction_kg'] = gas_reduction * GAS_CO2_FACTOR
    
    return savings


def calculate_energy_price_scenarios_impl(
    annual_savings: Dict[str, float],
    projection_years: int = 20
) -> Dict[str, Any]:
    """
    Calculate savings under different energy price scenarios
    """
    scenarios = {}
    
    # Define scenarios
    price_scenarios = [
        ('conservative', 0.02, 'Conservatief (2% stijging/jaar)'),
        ('moderate', 0.04, 'Gematigd (4% stijging/jaar)'),
        ('high', 0.06, 'Hoog (6% stijging/jaar)')
    ]
    
    for scenario_id, annual_increase, description in price_scenarios:
        total_savings = 0
        yearly_savings = []
        
        # Base annual savings (year 1)
        base_savings = annual_savings.get('total', 0)
        
        for year in range(1, projection_years + 1):
            # Calculate savings with price increase
            year_savings = base_savings * ((1 + annual_increase) ** (year - 1))
            yearly_savings.append({
                'year': year,
                'savings': round(year_savings, 2)
            })
            total_savings += year_savings
        
        scenarios[scenario_id] = {
            'description': description,
            'annual_increase': annual_increase,
            'total_savings': round(total_savings, 2),
            'average_annual_savings': round(total_savings / projection_years, 2),
            'year_10_savings': round(base_savings * ((1 + annual_increase) ** 9), 2),
            'year_20_savings': round(base_savings * ((1 + annual_increase) ** 19), 2)
        }
    
    return {
        'base_annual_savings': round(annual_savings.get('total', 0), 2),
        'scenarios': scenarios,
        'projection_years': projection_years,
        'calculation_date': datetime.now().isoformat()
    }


def calculate_property_value_impact_impl(
    property_value: float,
    energy_label_improvement: str,
    products: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calculate expected property value increase from sustainability measures
    Based on Brainbay Q3 2024 Dutch market research data
    """
    # Parse label improvement (e.g., "D → B" or "D->B")
    if '→' in energy_label_improvement:
        current_label, new_label = energy_label_improvement.split(' → ')
    elif '->' in energy_label_improvement:
        current_label, new_label = energy_label_improvement.split('->')
    else:
        # Default if no clear improvement
        current_label = 'D'
        new_label = 'C'
    
    # Clean up label names (remove extra + signs for lookup)
    current_label_clean = current_label.strip().replace('+++', '').replace('++', '+')
    new_label_clean = new_label.strip().replace('+++', '').replace('++', '+')
    
    # Look up value increase from Brainbay matrix
    label_pair = (current_label_clean, new_label_clean)
    if label_pair in WOZ_INCREASE_MATRIX:
        value_increase_percentage = WOZ_INCREASE_MATRIX[label_pair] * 100  # Convert to percentage
    else:
        # Try to find a close match (e.g., A++ might be stored as A+)
        # Default to conservative 3% if no match found
        value_increase_percentage = 3.0
        print(f"Warning: No exact match for label improvement {current_label} → {new_label}, using default 3%")
    
    # Additional factors based on products (optional market premiums)
    has_heat_pump = any('warmtepomp' in p.get('name', '').lower() for p in products)
    has_solar = any('zonnepanelen' in p.get('name', '').lower() for p in products)
    has_insulation = any(p.get('category') == 'Insulation' for p in products)
    
    # Market demand factors (conservative additional premiums)
    sustainability_premium = 0
    if has_heat_pump:
        sustainability_premium += 1.0  # Gas-free ready premium
    if has_solar:
        sustainability_premium += 0.5  # Energy generation premium
    if has_insulation:
        sustainability_premium += 0.5  # Comfort premium
    
    # Total value increase
    total_increase_percentage = value_increase_percentage + sustainability_premium
    value_increase_amount = property_value * (total_increase_percentage / 100)
    
    return {
        'current_value': round(property_value, 2),
        'current_energy_label': current_label,
        'projected_energy_label': new_label,
        'brainbay_value_increase_percentage': round(value_increase_percentage, 1),
        'sustainability_premium_percentage': round(sustainability_premium, 1),
        'total_value_increase_amount': round(value_increase_amount, 2),
        'total_value_increase_percentage': round(total_increase_percentage, 1),
        'projected_property_value': round(property_value + value_increase_amount, 2),
        'market_factors': {
            'gas_free_ready': has_heat_pump,
            'energy_neutral_potential': has_heat_pump and has_solar,
            'improved_marketability': total_increase_percentage > 3
        },
        'data_source': 'Brainbay Q3 2024',
        'calculation_date': datetime.now().isoformat()
    }


def calculate_comfort_improvements_impl(
    current_complaints: List[str],
    products: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calculate expected comfort improvements from installed products
    """
    improvements = {
        'temperature_stability': 0,
        'draft_reduction': 0,
        'noise_reduction': 0,
        'humidity_control': 0,
        'air_quality': 0
    }
    
    specific_benefits = []
    
    for product in products:
        category = product.get('category', '')
        name = product.get('name', '').lower()
        
        if category == 'Insulation':
            improvements['temperature_stability'] += 2
            improvements['draft_reduction'] += 1.5
            
            if 'spouwmuur' in name:
                specific_benefits.append("Geen koude straling meer van buitenmuren")
            elif 'dak' in name:
                specific_benefits.append("Warmere zolderverdieping in winter")
            elif 'vloer' in name:
                specific_benefits.append("Geen koude voeten meer op begane grond")
                
        elif category == 'Glass':
            improvements['draft_reduction'] += 2
            improvements['noise_reduction'] += 1.5
            specific_benefits.append("Geen kouval meer bij ramen")
            specific_benefits.append("Betere geluidsisolatie van buiten")
            
        elif category == 'Heating':
            if 'warmtepomp' in name:
                improvements['temperature_stability'] += 1.5
                improvements['air_quality'] += 1
                specific_benefits.append("Constantere temperatuur door het hele huis")
                if 'hybride' not in name:
                    specific_benefits.append("Mogelijkheid tot koeling in warme zomers")
    
    # Address specific complaints
    addressed_complaints = []
    if 'cold_floors' in current_complaints and any('vloer' in p.get('name', '').lower() for p in products):
        addressed_complaints.append("Koude vloeren worden aangepakt")
    if 'draft' in current_complaints and (improvements['draft_reduction'] > 0):
        addressed_complaints.append("Tocht wordt verminderd")
    if 'noise' in current_complaints and improvements['noise_reduction'] > 0:
        addressed_complaints.append("Geluidsoverlast wordt verminderd")
    
    # Calculate overall comfort score (0-10 scale)
    base_comfort = 5  # Average starting point
    total_improvement = sum(improvements.values()) / 5  # Average improvement
    new_comfort_score = min(10, base_comfort + total_improvement)
    
    return {
        'comfort_scores': {
            'current': base_comfort,
            'projected': round(new_comfort_score, 1),
            'improvement': round(new_comfort_score - base_comfort, 1)
        },
        'specific_improvements': improvements,
        'benefits': specific_benefits,
        'addressed_complaints': addressed_complaints,
        'health_benefits': [
            "Betere luchtkwaliteit vermindert luchtwegklachten",
            "Stabiele temperatuur verbetert nachtrust",
            "Minder vocht voorkomt schimmelvorming"
        ] if total_improvement > 2 else [],
        'calculation_date': datetime.now().isoformat()
    }


def calculate_environmental_impact_impl(co2_reduction_kg: float) -> Dict[str, Any]:
    """
    Calculate environmental impact equivalents for CO2 reduction
    Makes the impact tangible and relatable for homeowners
    """
    if co2_reduction_kg <= 0:
        return {
            "co2_reduction_kg": 0,
            "trees_equivalent": 0,
            "car_km_equivalent": 0,
            "flights_equivalent": 0,
            "dutch_household_months": 0,
            "energy_independence_percentage": 0,
            "contribution_to_climate_goals": "0% van uw deel voor Parijs akkoord",
            "calculation_timestamp": datetime.now().isoformat()
        }
    
    # Environmental equivalents
    trees_equivalent = co2_reduction_kg / 20  # 1 tree absorbs ~20kg CO2/year
    car_km_equivalent = co2_reduction_kg / 0.12  # Average car emits 120g/km
    flights_equivalent = co2_reduction_kg / 250  # Short-haul flight ~250kg CO2
    dutch_household_months = co2_reduction_kg / 416  # Average Dutch home ~5000kg/year = 416kg/month
    
    # Energy independence calculation (simplified)
    # Based on typical Dutch household energy consumption
    typical_annual_co2 = 5000  # kg for average Dutch household
    independence_percentage = min(100, (co2_reduction_kg / typical_annual_co2) * 100)
    
    # Paris Agreement contribution
    # Dutch target: 49% reduction by 2030 from 1990 levels
    # Average Dutch person: 8.8 tons CO2/year
    personal_target_reduction = 8800 * 0.49  # kg per person
    paris_contribution = (co2_reduction_kg / personal_target_reduction) * 100
    
    # Local air quality impact
    # Based on NO2 and PM2.5 reduction from gas heating elimination
    local_air_quality = {
        "no2_reduction_percentage": 15 if co2_reduction_kg > 2000 else 8,
        "pm25_reduction_percentage": 10 if co2_reduction_kg > 2000 else 5,
        "health_impact": "Significant" if co2_reduction_kg > 3000 else "Moderate"
    }
    
    return {
        "co2_reduction_kg": round(co2_reduction_kg),
        "trees_equivalent": round(trees_equivalent),
        "car_km_equivalent": round(car_km_equivalent),
        "flights_equivalent": round(flights_equivalent),
        "dutch_household_months": round(dutch_household_months, 1),
        "energy_independence_percentage": round(independence_percentage),
        "contribution_to_climate_goals": f"{round(paris_contribution)}% van uw deel voor Parijs akkoord",
        "local_air_quality_impact": local_air_quality,
        "visual_comparisons": {
            "trees": {
                "amount": round(trees_equivalent),
                "description": f"{round(trees_equivalent)} volwassen bomen die een jaar lang CO₂ opnemen",
                "icon": "🌳"
            },
            "car": {
                "amount": round(car_km_equivalent),
                "description": f"{round(car_km_equivalent):,} kilometer niet rijden met een benzineauto",
                "icon": "🚗"
            },
            "flights": {
                "amount": round(flights_equivalent),
                "description": f"{round(flights_equivalent)} retourvluchten naar Barcelona vermijden",
                "icon": "✈️"
            },
            "households": {
                "amount": round(dutch_household_months, 1),
                "description": f"{round(dutch_household_months, 1)} maanden gemiddeld Nederlands huishouden",
                "icon": "🏠"
            }
        },
        "neighborhood_impact": {
            "description": "Uw bijdrage aan schonere lucht in de wijk",
            "no2_reduction": f"{local_air_quality['no2_reduction_percentage']}% minder stikstofdioxide",
            "pm25_reduction": f"{local_air_quality['pm25_reduction_percentage']}% minder fijnstof",
            "health_benefits": [
                "Verminderde luchtwegklachten bij kinderen",
                "Betere luchtkwaliteit voor ouderen",
                "Gezondere leefomgeving voor iedereen"
            ] if co2_reduction_kg > 2000 else ["Merkbare verbetering luchtkwaliteit"]
        },
        "climate_leadership": {
            "status": "Klimaatkoploper" if paris_contribution > 100 else "Klimaatbewust" if paris_contribution > 50 else "Goede start",
            "message": get_climate_message(paris_contribution)
        },
        "calculation_timestamp": datetime.now().isoformat()
    }


def get_climate_message(paris_contribution: float) -> str:
    """Get personalized climate message based on contribution level"""
    if paris_contribution >= 100:
        return "U doet meer dan uw deel voor het klimaat! Een inspiratie voor anderen."
    elif paris_contribution >= 75:
        return "Uitstekend! U bent goed op weg om uw klimaatdoelen te halen."
    elif paris_contribution >= 50:
        return "Goed bezig! Elke stap telt in de strijd tegen klimaatverandering."
    elif paris_contribution >= 25:
        return "Een mooie start! Met deze maatregelen zet u belangrijke stappen."
    else:
        return "Een begin is gemaakt. Overweeg extra maatregelen voor meer impact."


def calculate_product_specific_savings(
    product: Dict[str, Any],
    current_gas: float,
    current_electricity: float,
    tariffs: Dict[str, float]
) -> Dict[str, Any]:
    """
    Calculate savings for each product type based on its specific characteristics
    """
    name_lower = product.get('name', '').lower()
    category = product.get('category', '')
    
    # Initialize result
    result = {
        'gas_savings_m3': 0,
        'electricity_change_kwh': 0,
        'solar_production_kwh': 0,
        'annual_cost_savings': 0,
        'co2_reduction_kg': 0
    }
    
    # Hybrid heat pump
    if 'hybride' in name_lower and 'warmtepomp' in name_lower:
        # More accurate split: 90% of gas for space heating, 10% for hot water
        # Hybrid pumps only replace space heating, not hot water
        heating_gas = current_gas * 0.90  # 90% of gas is for space heating
        result['gas_savings_m3'] = heating_gas * 0.70  # 70% reduction in heating gas
        
        # Calculate electricity increase based on actual heat energy replaced
        # Gas energy saved: m³ × kWh/m³ × boiler efficiency
        gas_energy_saved = result['gas_savings_m3'] * DUTCH_GAS_CONSTANTS["ENERGY_CONTENT_KWH_PER_M3"] * DUTCH_GAS_CONSTANTS["BOILER_EFFICIENCY"]
        
        # Electricity needed = heat energy / COP
        cop = HEAT_PUMP_COP["HYBRID_CONSERVATIVE"]  # 3.5
        result['electricity_change_kwh'] = -(gas_energy_saved / cop)  # Negative = increase
        
        # Financial impact
        gas_cost_savings = result['gas_savings_m3'] * tariffs['gas']
        electricity_cost_increase = abs(result['electricity_change_kwh']) * tariffs['electricity']
        result['annual_cost_savings'] = gas_cost_savings - electricity_cost_increase
        
        # CO2 impact
        co2_gas_reduction = result['gas_savings_m3'] * GAS_CO2_FACTOR
        co2_electricity_increase = abs(result['electricity_change_kwh']) * ELECTRICITY_CO2_FACTOR
        result['co2_reduction_kg'] = co2_gas_reduction - co2_electricity_increase
    
    # All-electric heat pump (100% gas replacement)
    elif (('warmtepomp' in name_lower and 
           'hybride' not in name_lower and 
           'boiler' not in name_lower) or 
          'all-electric' in name_lower or 
          'all electric' in name_lower):
        # All-electric heat pump replaces ALL gas usage (heating, hot water, and cooking)
        result['gas_savings_m3'] = current_gas  # 100% gas reduction
        
        # Calculate total heat energy to replace from gas
        total_heat_energy = current_gas * DUTCH_GAS_CONSTANTS["ENERGY_CONTENT_KWH_PER_M3"] * DUTCH_GAS_CONSTANTS["BOILER_EFFICIENCY"]
        
        # Determine COP based on house age/insulation (could be refined with actual data)
        # For now, use medium house COP as default
        cop = HEAT_PUMP_COP.get("ALL_ELECTRIC_MEDIUM_HOUSE", 3.5)
        
        # Electricity needed for heating and hot water
        heating_electricity = total_heat_energy / cop
        
        # Additional electricity for induction cooking (typical Dutch household)
        cooking_electricity = 600  # kWh/year
        
        # Total electricity increase (negative = increase in consumption)
        result['electricity_change_kwh'] = -(heating_electricity + cooking_electricity)
        
        # Financial impact
        gas_cost_savings = result['gas_savings_m3'] * tariffs['gas']
        electricity_cost_increase = abs(result['electricity_change_kwh']) * tariffs['electricity']
        result['annual_cost_savings'] = gas_cost_savings - electricity_cost_increase
        
        # CO2 impact
        co2_gas_reduction = result['gas_savings_m3'] * GAS_CO2_FACTOR
        co2_electricity_increase = abs(result['electricity_change_kwh']) * ELECTRICITY_CO2_FACTOR
        result['co2_reduction_kg'] = co2_gas_reduction - co2_electricity_increase
    
    # CV-ketel (gas boiler replacement - no savings)
    elif 'cv' in name_lower and 'ketel' in name_lower:
        # No savings - just replacement
        result['annual_cost_savings'] = 0
    
    # Heat pump boiler
    elif 'warmtepompboiler' in name_lower or ('boiler' in name_lower and 'warmtepomp' in name_lower):
        # 10% of gas usage is for hot water (more accurate for Dutch homes)
        hot_water_gas = current_gas * 0.10
        result['gas_savings_m3'] = hot_water_gas * 0.85  # 85% reduction (some backup still needed)
        
        # Calculate electricity based on actual heat energy for hot water
        # Gas energy saved: m³ × kWh/m³ × boiler efficiency
        hot_water_energy_saved = result['gas_savings_m3'] * DUTCH_GAS_CONSTANTS["ENERGY_CONTENT_KWH_PER_M3"] * DUTCH_GAS_CONSTANTS["BOILER_EFFICIENCY"]
        
        # Heat pump boilers have lower COP for water heating (around 3.0)
        water_heating_cop = 3.0
        result['electricity_change_kwh'] = -(hot_water_energy_saved / water_heating_cop)  # Negative = increase
        
        # Financial impact
        gas_cost_savings = result['gas_savings_m3'] * tariffs['gas']
        electricity_cost_increase = abs(result['electricity_change_kwh']) * tariffs['electricity']
        result['annual_cost_savings'] = gas_cost_savings - electricity_cost_increase
        
        # CO2 impact
        co2_gas_reduction = result['gas_savings_m3'] * GAS_CO2_FACTOR
        co2_electricity_increase = abs(result['electricity_change_kwh']) * ELECTRICITY_CO2_FACTOR
        result['co2_reduction_kg'] = co2_gas_reduction - co2_electricity_increase
    
    # Solar panels
    elif 'zonnepanelen' in name_lower or 'solar' in name_lower:
        # Get capacity from technical specs or estimate
        capacity_kwp = product.get('technical_specs', {}).get('capacity_kwp', 0.41)  # 410Wp default
        result['solar_production_kwh'] = capacity_kwp * SOLAR_PRODUCTION_FACTOR * product.get('quantity', 1)
        
        # Financial impact (return tariff)
        result['annual_cost_savings'] = result['solar_production_kwh'] * tariffs['return']
        
        # CO2 impact
        result['co2_reduction_kg'] = result['solar_production_kwh'] * ELECTRICITY_CO2_FACTOR
    
    # Insulation
    elif category == 'Insulation':
        # Different savings for different insulation types
        if 'spouwmuur' in name_lower:
            gas_reduction_pct = 0.20
        elif 'dak' in name_lower:
            gas_reduction_pct = 0.25
        elif 'vloer' in name_lower or 'bodem' in name_lower:
            gas_reduction_pct = 0.15
        else:
            gas_reduction_pct = 0.10
        
        result['gas_savings_m3'] = current_gas * gas_reduction_pct
        result['annual_cost_savings'] = result['gas_savings_m3'] * tariffs['gas']
        result['co2_reduction_kg'] = result['gas_savings_m3'] * GAS_CO2_FACTOR
    
    return result


def calculate_energy_label_improvement(
    current_label: str,
    current_gas_usage: float,
    gas_savings: float,
    electricity_change: float,
    solar_production: float,
    building_year: int,
    products: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calculate realistic energy label improvement based on multiple factors.
    
    Validation examples (based on real-world data):
    - C + hybrid pump + full insulation + solar → A (2 steps)
    - D + all-electric + partial insulation → B (2 steps)
    - E + hybrid pump + minimal insulation → D (1 step)
    - F + insulation only → E (1 step)
    - D + all-electric + full insulation + solar → A+ (3 steps)
    
    Returns:
        Dict with new_label, improvement_steps, and detailed scoring breakdown
    """
    # Label hierarchy
    label_map = ['G', 'F', 'E', 'D', 'C', 'B', 'A', 'A+', 'A++', 'A+++', 'A++++']
    
    # Handle missing or empty labels
    if not current_label or current_label == '':
        current_label = 'D'  # Default assumption for missing labels
    
    current_idx = label_map.index(current_label) if current_label in label_map else 3
    
    # Initialize scoring components
    scores = {
        'energy_impact': 0,      # 40% weight
        'building_transformation': 0,  # 30% weight
        'future_readiness': 0,   # 30% weight
        'total': 0
    }
    
    # 1. ENERGY IMPACT SCORE (0-40 points)
    # Calculate total energy reduction percentage
    if current_gas_usage > 0:
        # Convert to primary energy
        current_primary = current_gas_usage * 9.77  # Gas to kWh
        # Add current electricity (assuming 3500 kWh average if not provided)
        current_primary += 3500 * 2.5  # Electricity with primary factor
        
        # After improvements
        new_gas = (current_gas_usage - gas_savings) * 9.77
        new_electricity = (3500 + abs(electricity_change) - solar_production) * 2.5
        new_primary = new_gas + new_electricity
        
        # Primary energy reduction percentage
        primary_reduction = ((current_primary - new_primary) / current_primary) * 100
        
        # CO2 reduction percentage (alternative metric)
        co2_before = current_gas_usage * 1.78 + 3500 * 0.4
        co2_after = (current_gas_usage - gas_savings) * 1.78 + (3500 + abs(electricity_change) - solar_production) * 0.4
        co2_reduction = ((co2_before - co2_after) / co2_before) * 100
        
        # Use the better of the two metrics
        reduction_pct = max(primary_reduction, co2_reduction)
    else:
        reduction_pct = 0
    
    # Score based on reduction achieved
    if reduction_pct >= 60:
        scores['energy_impact'] = 40
    elif reduction_pct >= 45:
        scores['energy_impact'] = 35
    elif reduction_pct >= 30:
        scores['energy_impact'] = 30
    elif reduction_pct >= 20:
        scores['energy_impact'] = 25
    elif reduction_pct >= 15:
        scores['energy_impact'] = 20
    elif reduction_pct >= 10:
        scores['energy_impact'] = 15
    elif reduction_pct >= 5:
        scores['energy_impact'] = 10
    else:
        scores['energy_impact'] = 5
    
    # 2. BUILDING TRANSFORMATION SCORE (0-30 points)
    transformation_score = 0
    
    # Check what products are installed
    has_hybrid_heat_pump = any('hybride' in p.get('name', '').lower() and 'warmtepomp' in p.get('name', '').lower() for p in products)
    has_all_electric_heat_pump = any(
        'warmtepomp' in p.get('name', '').lower() and 
        'hybride' not in p.get('name', '').lower() and 
        'boiler' not in p.get('name', '').lower() 
        for p in products
    )
    has_solar = any('zonnepanelen' in p.get('name', '').lower() or 'solar' in p.get('name', '').lower() for p in products)
    has_warmtepompboiler = any('warmtepompboiler' in p.get('name', '').lower() for p in products)
    
    # Count insulation measures
    insulation_products = [p for p in products if p.get('category') == 'Insulation']
    insulation_types = set()
    for p in insulation_products:
        name_lower = p.get('name', '').lower()
        if 'spouwmuur' in name_lower:
            insulation_types.add('wall')
        elif 'dak' in name_lower:
            insulation_types.add('roof')
        elif 'vloer' in name_lower or 'bodem' in name_lower:
            insulation_types.add('floor')
    
    # Insulation scoring (max 15 points)
    insulation_count = len(insulation_types)
    if insulation_count >= 3:
        transformation_score += 15  # Comprehensive
    elif insulation_count == 2:
        transformation_score += 10  # Good
    elif insulation_count == 1:
        transformation_score += 5   # Basic
    
    # Heating system scoring (max 10 points)
    if has_all_electric_heat_pump:
        transformation_score += 10
    elif has_hybrid_heat_pump:
        transformation_score += 7
    elif has_warmtepompboiler:
        transformation_score += 3
    
    # Windows/glass scoring (max 5 points)
    has_glass = any(p.get('category') == 'Glass' or 'beglazing' in p.get('name', '').lower() for p in products)
    if has_glass:
        transformation_score += 5
    
    scores['building_transformation'] = min(30, transformation_score)
    
    # 3. FUTURE-READINESS SCORE (0-30 points)
    future_score = 0
    
    # All-electric bonus (15 points)
    if has_all_electric_heat_pump and gas_savings >= current_gas_usage * 0.95:
        future_score += 15
    elif has_hybrid_heat_pump:
        future_score += 8  # Partial credit
    
    # Renewable energy (10 points)
    if has_solar:
        if solar_production >= 3000:  # Substantial solar
            future_score += 10
        elif solar_production >= 1500:
            future_score += 7
        else:
            future_score += 5
    
    # Energy independence factor (5 points)
    if reduction_pct >= 50 and has_solar:
        future_score += 5
    
    scores['future_readiness'] = min(30, future_score)
    
    # TOTAL SCORE
    scores['total'] = scores['energy_impact'] + scores['building_transformation'] + scores['future_readiness']
    
    # 4. CALCULATE IMPROVEMENT STEPS
    # Base steps from score
    if scores['total'] >= 90:
        base_steps = 3.5
    elif scores['total'] >= 80:
        base_steps = 3.0
    elif scores['total'] >= 70:
        base_steps = 2.5
    elif scores['total'] >= 60:
        base_steps = 2.0
    elif scores['total'] >= 45:
        base_steps = 1.5
    elif scores['total'] >= 30:
        base_steps = 1.0
    elif scores['total'] >= 20:
        base_steps = 0.5
    else:
        base_steps = 0
    
    # 5. APPLY CONSTRAINTS AND MODIFIERS
    
    # Building age modifier
    if building_year < 1960:
        age_modifier = 1.1  # 10% bonus for very old buildings
    elif building_year < 1980:
        age_modifier = 1.05  # 5% bonus
    elif building_year < 2000:
        age_modifier = 1.0   # No change
    elif building_year < 2010:
        age_modifier = 0.9   # 10% penalty for newer buildings
    else:
        age_modifier = 0.8   # 20% penalty for very new buildings
    
    # Apply age modifier
    adjusted_steps = base_steps * age_modifier
    
    # Maximum achievable label constraints
    max_achievable_label = 'A++++'  # Default maximum
    
    # Hybrid heat pump constraint - can't achieve highest labels with gas usage
    if has_hybrid_heat_pump and not has_all_electric_heat_pump:
        if gas_savings < current_gas_usage * 0.8:  # Less than 80% reduction
            max_achievable_label = 'A'
        else:
            max_achievable_label = 'A+'  # Very efficient hybrid might reach A+
    
    # Starting position constraints
    max_realistic_steps = {
        'G': 4,  # G can improve up to C (sometimes B with perfect execution)
        'F': 4,  # F can improve up to B (sometimes A with perfect execution)
        'E': 3,  # E can improve up to B (sometimes A)
        'D': 4,  # D can improve up to A+ with comprehensive measures
        'C': 3,  # C can improve up to A+ (sometimes A++)
        'B': 2,  # B can improve up to A+
        'A': 2,  # A can improve up to A++
    }.get(current_label, 1)
    
    # Energy reduction validation
    # Require minimum energy reduction per step
    min_reduction_per_step = 15  # 15% reduction per label step
    max_steps_by_reduction = reduction_pct / min_reduction_per_step
    
    # Final steps calculation
    improvement_steps = min(
        round(adjusted_steps),
        max_realistic_steps,
        int(max_steps_by_reduction)
    )
    
    # Ensure minimum improvement for significant investments
    total_investment = sum(p.get('total_price', 0) for p in products)
    if total_investment > 25000 and improvement_steps < 1 and reduction_pct >= 10:
        improvement_steps = 1
    
    # Calculate new label
    max_achievable_idx = label_map.index(max_achievable_label)
    new_idx = min(
        current_idx + improvement_steps,
        max_achievable_idx,
        len(label_map) - 1
    )
    
    new_label = label_map[new_idx]
    
    # Validation warnings
    warnings = []
    if improvement_steps >= 3:
        warnings.append("Large label improvement - verify with professional energy assessment")
    if improvement_steps == 0 and reduction_pct >= 15:
        warnings.append("Significant energy reduction but no label improvement - current label may be incorrect")
    if has_hybrid_heat_pump and new_idx > label_map.index('A'):
        warnings.append("Hybrid systems typically cannot achieve labels beyond A")
    
    return {
        'current_label': current_label,
        'new_label': new_label,
        'improvement_steps': improvement_steps,
        'improvement_description': f"{current_label} → {new_label}",
        'scores': scores,
        'energy_reduction_pct': round(reduction_pct, 1),
        'calculation_factors': {
            'building_year': building_year,
            'age_modifier': age_modifier,
            'max_achievable_label': max_achievable_label,
            'insulation_measures': insulation_count,
            'has_heat_pump': has_hybrid_heat_pump or has_all_electric_heat_pump,
            'has_solar': has_solar,
            'total_score': scores['total']
        },
        'warnings': warnings
    }


def calculate_comprehensive_metrics_impl(
    deal_id: str,
    energy_profile: Dict[str, Any],
    products: List[Dict[str, Any]],
    loan_terms: Optional[Dict[str, Any]] = None,
    skip_db_lookup: bool = False
) -> Dict[str, Any]:
    """
    Calculate ALL metrics needed for the report in one comprehensive call.
    This prevents the report-composer from doing any calculations.
    Uses actual database values for accuracy.
    """
    # First get basic savings calculation
    basic_savings = calculate_savings_impl(deal_id, energy_profile)
    
    if 'error' in basic_savings:
        return basic_savings
    
    # For non-demo mode, fetch actual database values (unless skipped)
    if not DEMO_MODE and supabase and not skip_db_lookup:
        try:
            # Get quote data with actual values
            deal_response = supabase.table('deals') \
                .select('final_quote_id, quote_id') \
                .eq('id', deal_id) \
                .single() \
                .execute()
            
            if deal_response.data:
                quote_id = deal_response.data['final_quote_id'] or deal_response.data['quote_id']
                
                # Get quote with loan data
                quote_response = supabase.table('quotes') \
                    .select('*') \
                    .eq('id', quote_id) \
                    .single() \
                    .execute()
                
                if quote_response.data:
                    quote_data = quote_response.data
                    
                    # Get quote items for per-product subsidies
                    quote_items_response = supabase.table('quote_items') \
                        .select('*, products!inner(*)') \
                        .eq('quote_id', quote_id) \
                        .execute()
                    
                    # Use actual database values
                    if quote_data.get('total_subsidy_estimate') is not None:
                        basic_savings['financial_impact']['total_subsidies'] = float(quote_data['total_subsidy_estimate'])
                    
                    if quote_data.get('loan_monthly_payment') is not None and loan_terms:
                        # Update loan terms with actual database values, preserving other fields
                        loan_terms.update({
                            'interest_rate': float(quote_data.get('loan_interest_rate', 0)) / 100,  # Convert to decimal
                            'term_years': quote_data.get('loan_term_years', loan_terms.get('term_years', 15)),
                            'monthly_payment': float(quote_data.get('loan_monthly_payment', 0))
                        })
                    
                    # Update products with actual subsidy values
                    if quote_items_response.data:
                        products_by_id = {p['id']: p for p in products}
                        for item in quote_items_response.data:
                            product_id = item['product_id']
                            if product_id in products_by_id:
                                products_by_id[product_id]['subsidy_amount'] = float(item.get('item_subsidy_estimate', 0))
        except Exception as e:
            # Log but continue with calculated values
            print(f"Warning: Could not fetch database values: {e}")
    
    # Extract key values
    total_investment = basic_savings['financial_impact']['total_investment']
    annual_savings = basic_savings['financial_impact']['annual_savings']
    monthly_savings = basic_savings['financial_impact']['monthly_savings']
    
    # Recalculate total subsidies from products (may have been corrected)
    total_subsidies = 0
    for product in products:
        if 'subsidy' in product and isinstance(product['subsidy'], dict):
            total_subsidies += product['subsidy'].get('amount', 0)
        else:
            total_subsidies += product.get('subsidy_amount', 0)
    
    # Recalculate net investment with corrected subsidies
    net_investment = total_investment - total_subsidies
    
    # Calculate per-product metrics using product-specific calculations
    products_with_metrics = []
    current_gas = energy_profile['current_usage']['gas']
    current_electricity = energy_profile['current_usage']['electricity']
    tariffs = energy_profile['tariffs']
    
    for product in products:
        # Get product investment from total_price field (as set by energy-data MCP)
        product_investment = product.get('total_price', 0)
        # If not available, try unit_price * quantity
        if product_investment == 0:
            product_investment = product.get('unit_price', 0) * product.get('quantity', 1)
        
        # Get subsidy from the subsidy object
        product_subsidy = 0
        if 'subsidy' in product and isinstance(product['subsidy'], dict):
            product_subsidy = product['subsidy'].get('amount', 0)
        else:
            product_subsidy = product.get('subsidy_amount', 0)
        
        # Calculate product-specific savings
        product_savings = calculate_product_specific_savings(product, current_gas, current_electricity, tariffs)
        
        # Calculate payback
        net_cost = product_investment - product_subsidy
        product_payback = net_cost / product_savings['annual_cost_savings'] if product_savings['annual_cost_savings'] > 0 else 999
        
        # For financed products with negative/low savings, use loan term as payback
        if loan_terms and product_savings['annual_cost_savings'] <= 10:
            product_payback = loan_terms.get('term_years', 15)
        
        products_with_metrics.append({
            'name': product.get('name', ''),
            'category': product.get('category', ''),
            'quantity': product.get('quantity', 1),
            'unit_price': product.get('unit_price', 0),
            'total_investment': product_investment,
            'subsidy_amount': product_subsidy,
            'net_cost': net_cost,
            'annual_savings': round(product_savings['annual_cost_savings'], 2),
            'monthly_savings': round(product_savings['annual_cost_savings'] / 12, 2),
            'payback_period': round(product_payback, 1),
            'co2_reduction': round(product_savings['co2_reduction_kg'], 0),
            'gas_reduction_m3': round(product_savings['gas_savings_m3'], 0),
            'electricity_change_kwh': round(product_savings['electricity_change_kwh'], 0),
            'solar_production_kwh': round(product_savings['solar_production_kwh'], 0)
        })
    
    # Recalculate total energy savings from individual products (more accurate)
    total_gas_savings = sum(p['gas_reduction_m3'] for p in products_with_metrics)
    total_electricity_change = sum(p['electricity_change_kwh'] for p in products_with_metrics)
    total_solar_production = sum(p['solar_production_kwh'] for p in products_with_metrics)
    total_co2_reduction = sum(p['co2_reduction'] for p in products_with_metrics)
    
    # Recalculate financial impact based on corrected energy values
    # Gas savings calculation remains the same
    gas_cost_savings = total_gas_savings * tariffs['gas']
    
    # Net metering calculation (salderingsregeling)
    # Current consumption + heat pump increase - solar production = net usage
    current_electricity = energy_profile['current_usage'].get('electricity', 0)
    net_electricity_usage = current_electricity + abs(total_electricity_change) - total_solar_production
    
    # Under net metering, you only pay for net usage (can be negative)
    if net_electricity_usage > 0:
        # Net consumer - pay for excess consumption
        electricity_cost = net_electricity_usage * tariffs['electricity']
    else:
        # Net producer - receive credit at full electricity rate (1:1 saldering)
        electricity_cost = net_electricity_usage * tariffs['electricity']  # Negative cost = income
    
    # Calculate savings compared to current costs
    current_electricity_cost = current_electricity * tariffs['electricity']
    electricity_cost_savings = current_electricity_cost - electricity_cost
    
    # Total annual savings
    total_annual_savings = gas_cost_savings + electricity_cost_savings
    
    # Update basic_metrics with corrected values
    basic_savings['energy_savings'] = {
        'gas_m3': round(total_gas_savings),
        'electricity_kwh': round(total_electricity_change),  # Negative = increase
        'electricity_increase_kwh': round(abs(total_electricity_change)) if total_electricity_change < 0 else 0,
        'solar_production_kwh': round(total_solar_production),
        'co2_reduction_kg': round(total_co2_reduction)
    }
    
    # Recalculate payback and ROI with corrected savings
    payback_years = net_investment / total_annual_savings if total_annual_savings > 0 else 999
    
    # Calculate inflation-adjusted payback (more realistic)
    inflation_adjusted_payback = 999
    if total_annual_savings > 0:
        cumulative_savings = 0
        for year in range(1, 31):  # Check up to 30 years
            annual_savings_with_inflation = total_annual_savings * ((1 + ENERGY_PRICE_INFLATION) ** (year - 1))
            cumulative_savings += annual_savings_with_inflation
            if cumulative_savings >= net_investment:
                inflation_adjusted_payback = year
                break
    
    # NPV calculation with realistic energy price inflation
    npv = 0
    for year in range(1, 21):
        # Use 4% energy price increase per year
        savings_in_year = total_annual_savings * ((1 + ENERGY_PRICE_INFLATION) ** year)
        discounted_value = savings_in_year / ((1 + DISCOUNT_RATE) ** year)
        npv += discounted_value
    npv -= net_investment
    
    roi_20_years = (npv + net_investment) / net_investment if net_investment > 0 else 0
    
    basic_savings['financial_impact'] = {
        'annual_savings': round(total_annual_savings, 2),
        'monthly_savings': round(total_annual_savings / 12, 2),
        'gas_cost_reduction': round(gas_cost_savings, 2),
        'electricity_cost_savings': round(electricity_cost_savings, 2),
        'net_electricity_usage_kwh': round(net_electricity_usage),
        'net_electricity_cost': round(electricity_cost, 2),
        'net_metering_applied': True,
        'total_investment': round(total_investment, 2),
        'total_subsidies': round(total_subsidies, 2),
        'net_investment': round(net_investment, 2),
        'payback_years': round(payback_years, 1),
        'payback_years_with_inflation': round(inflation_adjusted_payback, 1),
        'roi_20_years': round(roi_20_years, 2),
        'npv_20_years': round(npv, 2),
        'energy_price_inflation_used': round(ENERGY_PRICE_INFLATION * 100, 1)  # As percentage
    }
    
    # Update annual and monthly savings with corrected values
    annual_savings = total_annual_savings
    monthly_savings = total_annual_savings / 12
    
    # Calculate loan/financing metrics
    financing_metrics = {}
    if loan_terms and net_investment > 0:
        interest_rate = loan_terms.get('interest_rate', 0)  # Default 0% if not specified
        term_years = loan_terms.get('term_years', 15)  # Default 15 years
        
        # Initial loan is for full investment amount
        initial_loan_amount = total_investment
        # Subsidy is used to pay down the loan immediately
        effective_loan_amount = net_investment  # After subsidy payment
        
        # Use pre-calculated monthly payment from database if available
        if loan_terms.get('monthly_payment', 0) > 0:
            # Trust the database calculation (from closer's assessment)
            monthly_payment = loan_terms['monthly_payment']
        else:
            # Fallback: Calculate monthly payment based on effective loan (after subsidy paydown)
            if interest_rate > 0:
                monthly_rate = interest_rate / 12
                n_payments = term_years * 12
                monthly_payment = effective_loan_amount * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)
            else:
                # 0% interest - simple division
                monthly_payment = effective_loan_amount / (term_years * 12)
        
        # Calculate total interest paid over loan term (on the effective amount)
        total_payments = monthly_payment * term_years * 12
        total_interest = total_payments - effective_loan_amount
        
        financing_metrics = {
            'initial_loan_amount': round(initial_loan_amount, 2),
            'subsidy_loan_reduction': round(total_subsidies, 2),  # Uses corrected total subsidies
            'effective_loan_amount': round(effective_loan_amount, 2),  # Actual amount being financed
            'interest_rate': round(interest_rate * 100, 1),  # Convert to percentage
            'term_years': term_years,
            'monthly_payment': round(monthly_payment, 2),
            'total_interest': round(total_interest, 2),
            'total_payments': round(total_payments, 2),
            'monthly_net_benefit': round(monthly_savings - monthly_payment, 2),
            'income_category': loan_terms.get('income_category', '<60k'),
            'loan_type': 'Warmtefonds',
            'calculation_note': 'Assumes ISDE subsidy is used to immediately reduce loan principal'
        }
    
    # Calculate energy label improvement using new realistic function
    current_label = energy_profile.get('house_profile', {}).get('energy_label', 'D')
    building_year = energy_profile.get('house_profile', {}).get('year', 1985)
    
    # Use the new comprehensive label calculation
    label_result = calculate_energy_label_improvement(
        current_label=current_label,
        current_gas_usage=current_gas,
        gas_savings=total_gas_savings,
        electricity_change=total_electricity_change,
        solar_production=total_solar_production,
        building_year=building_year,
        products=products
    )
    
    # Extract results
    new_label = label_result['new_label']
    improvement_steps = label_result['improvement_steps']
    
    # Log detailed calculation results
    print(f"Energy Label Calculation Results:")
    print(f"  - Current → New: {label_result['improvement_description']}")
    print(f"  - Energy reduction: {label_result['energy_reduction_pct']}%")
    print(f"  - Scoring breakdown:")
    print(f"    • Energy impact: {label_result['scores']['energy_impact']}/40")
    print(f"    • Building transformation: {label_result['scores']['building_transformation']}/30")
    print(f"    • Future readiness: {label_result['scores']['future_readiness']}/30")
    print(f"    • Total score: {label_result['scores']['total']}/100")
    print(f"  - Calculation factors:")
    for key, value in label_result['calculation_factors'].items():
        print(f"    • {key}: {value}")
    if label_result['warnings']:
        print(f"  - Warnings:")
        for warning in label_result['warnings']:
            print(f"    ⚠️  {warning}")
    
    # Calculate CO2 equivalents (moved from report-composer)
    co2_reduction = basic_savings['energy_savings']['co2_reduction_kg']
    co2_equivalents = {
        'trees': int(co2_reduction / 20) if co2_reduction > 0 else 0,  # 1 tree = 20kg CO2/year
        'car_km': int(co2_reduction / 0.12) if co2_reduction > 0 else 0,  # 120g CO2/km
        'flights': int(co2_reduction / 250) if co2_reduction > 0 else 0,  # Short flight = 250kg CO2
        'months_household': round(co2_reduction / 416, 1) if co2_reduction > 0 else 0  # Average Dutch home = 5000kg/year
    }
    
    # Calculate customer's baseline CO2 emissions for accurate percentage
    current_gas_co2 = energy_profile['current_usage']['gas'] * GAS_CO2_FACTOR
    current_electricity_co2 = energy_profile['current_usage']['electricity'] * ELECTRICITY_CO2_FACTOR
    baseline_co2 = current_gas_co2 + current_electricity_co2
    
    # Determine effective payback period
    # Use inflation-adjusted payback for more realistic view
    effective_payback = basic_savings['financial_impact']['payback_years_with_inflation']
    payback_note = f"Berekend met {ENERGY_PRICE_INFLATION * 100:.0f}% jaarlijkse energieprijsstijging"
    
    # For Warmtefonds loans with negative/low savings, use loan term as minimum
    if loan_terms and annual_savings <= 50:  # If savings are negative or very low
        if effective_payback > loan_terms.get('term_years', 15):
            effective_payback = loan_terms.get('term_years', 15)
            if annual_savings < 0:
                payback_note = "Met Warmtefonds financiering is de terugverdientijd gelijk aan de looptijd"
            else:
                payback_note = "Door lage besparingen is de effectieve terugverdientijd de looptijd van de lening"
    
    # Calculate property value increase
    property_value = energy_profile.get('house_profile', {}).get('woz_value', DEFAULT_WOZ_VALUE)
    if property_value is None or property_value == 0:
        property_value = DEFAULT_WOZ_VALUE
    
    label_improvement = label_result['improvement_description']
    property_value_impact = calculate_property_value_impact_impl(
        property_value=property_value,
        energy_label_improvement=label_improvement,
        products=products
    )
    
    # Comprehensive response with ALL calculations done
    response = {
        'success': True,
        'deal_id': deal_id,
        'basic_metrics': basic_savings,
        'products_with_metrics': products_with_metrics,
        'financing_metrics': financing_metrics,
        'energy_label': {
            'current': current_label,
            'new': new_label,
            'improvement': label_result['improvement_description'],
            'improvement_steps': improvement_steps,
            'calculation': {
                'energy_reduction_pct': label_result['energy_reduction_pct'],
                'scores': label_result['scores'],
                'factors': label_result['calculation_factors'],
                'warnings': label_result['warnings']
            }
        },
        'property_value_impact': property_value_impact,
        'co2_equivalents': co2_equivalents,
        'summary': {
            'total_investment': round(total_investment, 2),
            'total_subsidies': round(total_subsidies, 2),
            'net_investment': round(net_investment, 2),
            'annual_savings': round(annual_savings, 2),
            'monthly_savings': round(monthly_savings, 2),
            'payback_period': round(effective_payback, 1),
            'roi_20_years': round(basic_savings['financial_impact']['roi_20_years'] * 100, 0),  # As percentage
            'co2_reduction_annual': round(co2_reduction, 0),
            'co2_reduction_percentage': round(co2_reduction / baseline_co2 * 100, 0) if baseline_co2 > 0 else 0,  # % of customer baseline
            'net_electricity_usage_kwh': basic_savings['financial_impact']['net_electricity_usage_kwh'],
            'net_metering_applied': True
        },
        'calculated_at': datetime.now().isoformat()
    }
    
    if payback_note:
        response['summary']['payback_note'] = payback_note
    
    return response


def calculate_from_comprehensive_data(comprehensive_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate all savings metrics from comprehensive deal data.
    This function works with the data structure returned by energy-data MCP's get_comprehensive_deal_data.
    """
    # Extract required data from comprehensive structure
    deal_id = comprehensive_data['deal_id']
    
    # Build energy profile from comprehensive data
    energy_profile = {
        'current_usage': {
            'gas': comprehensive_data['energy']['usage']['gas_m3'],
            'electricity': comprehensive_data['energy']['usage']['electricity_kwh'],
            'solar_return': comprehensive_data['energy']['usage']['solar_return_kwh']
        },
        'tariffs': comprehensive_data['energy']['tariffs'],
        'current_costs': comprehensive_data['energy']['costs'],
        'co2_emissions': comprehensive_data['energy']['co2_emissions'],
        'house_profile': {
            'type': comprehensive_data['property']['type'],
            'year': comprehensive_data['property']['year'],
            'area': comprehensive_data['property']['area'],
            'residents': comprehensive_data['property']['residents'],
            'energy_label': comprehensive_data['property']['energy_label'],
            'woz_value': comprehensive_data['property']['woz_value']
        }
    }
    
    # Extract products from quote
    products = comprehensive_data['quote']['products'] if 'quote' in comprehensive_data else []
    
    # Extract loan terms if using warmtefonds
    loan_terms = None
    payment_method = comprehensive_data.get('quote', {}).get('payment_method', '')
    
    # Check if using Warmtefonds (could be 'warmtefonds' or 'loan')
    if payment_method in ['warmtefonds', 'loan']:
        financing = comprehensive_data.get('quote', {}).get('financing', {})
        loan_info = financing.get('loan', {})
        
        loan_terms = {
            'amount': comprehensive_data['quote']['totals']['net_investment'],
            'interest_rate': loan_info.get('interest_rate') if loan_info.get('interest_rate') is not None else 0,  # Keep as-is from database (already decimal)
            'term_years': loan_info.get('term_years') if loan_info.get('term_years') is not None else 15,  # Default 15 years
            'monthly_payment': loan_info.get('monthly_payment') if loan_info.get('monthly_payment') is not None else 0,  # Use pre-calculated if available
            'income_category': loan_info.get('income_category') if loan_info.get('income_category') is not None else '>=60k'  # Default to higher income if not specified
        }
    
    # Calculate comprehensive metrics (skip DB lookup since we have all data)
    return calculate_comprehensive_metrics_impl(
        deal_id=deal_id,
        energy_profile=energy_profile,
        products=products,
        loan_terms=loan_terms,
        skip_db_lookup=True  # We already have all data from comprehensive_data
    )


# MCP tool wrappers for future FastAgent integration
@mcp.tool()
def calculate_savings(deal_id: str, energy_profile: Dict[str, Any]) -> Dict[str, Any]:
    """MCP wrapper for calculate_savings_impl"""
    return calculate_savings_impl(deal_id, energy_profile)

@mcp.tool()
def calculate_energy_price_scenarios(annual_savings: Dict[str, float], projection_years: int = 20) -> Dict[str, Any]:
    """MCP wrapper for calculate_energy_price_scenarios_impl"""
    return calculate_energy_price_scenarios_impl(annual_savings, projection_years)

@mcp.tool()
def calculate_property_value_impact(property_value: float, energy_label_improvement: str, products: List[Dict[str, Any]]) -> Dict[str, Any]:
    """MCP wrapper for calculate_property_value_impact_impl"""
    return calculate_property_value_impact_impl(property_value, energy_label_improvement, products)

@mcp.tool()
def calculate_comfort_improvements(current_complaints: List[str], products: List[Dict[str, Any]]) -> Dict[str, Any]:
    """MCP wrapper for calculate_comfort_improvements_impl"""
    return calculate_comfort_improvements_impl(current_complaints, products)

@mcp.tool()
def calculate_environmental_impact(co2_reduction_kg: float) -> Dict[str, Any]:
    """MCP wrapper for calculate_environmental_impact_impl"""
    return calculate_environmental_impact_impl(co2_reduction_kg)

@mcp.tool()
def calculate_comprehensive_metrics(
    deal_id: str,
    energy_profile: Dict[str, Any],
    products: List[Dict[str, Any]],
    loan_terms: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Calculate ALL metrics needed for the report in one comprehensive call.
    
    This tool calculates:
    - Energy savings (gas, electricity, solar production)
    - Financial metrics (investment, subsidies, payback, ROI)
    - Per-product metrics (individual savings and payback)
    - Financing/loan calculations
    - Energy label improvements
    - CO2 reduction and equivalents
    
    Args:
        deal_id: The deal ID to calculate for
        energy_profile: Current energy usage and tariffs
        products: List of products/measures being installed
        loan_terms: Optional loan parameters (interest_rate, term_years)
    
    Returns:
        Comprehensive metrics dict with all calculations completed
    """
    return calculate_comprehensive_metrics_impl(deal_id, energy_profile, products, loan_terms)

@mcp.tool()
def calculate_from_deal_data(comprehensive_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate all metrics from comprehensive deal data structure.
    
    This tool accepts the output from energy-data MCP's get_comprehensive_deal_data
    and performs all calculations without database access.
    
    Args:
        comprehensive_data: Complete deal data structure from energy-data MCP
        
    Returns:
        All calculated metrics including savings, ROI, payback, CO2 reduction, etc.
    """
    return calculate_from_comprehensive_data(comprehensive_data)


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()