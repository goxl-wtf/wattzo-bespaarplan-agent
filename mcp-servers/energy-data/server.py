#!/usr/bin/env python3
"""
Energy Data MCP Server
Provides tools for accessing home energy assessments and consumption data
Inspired by HolyGrail's narrative_engine pattern
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import random
from supabase import create_client, Client

from fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("EnergyData")

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


# Demo data for testing
DEMO_HOMES = {
    "demo-123": {
        "address": "Keizersgracht 123, Amsterdam",
        "type": "tussenwoning",
        "build_year": 1985,
        "living_area": 120,
        "energy_label": "D",
        "residents": 4,
        "current_heating": "cv-ketel",
        "insulation": {
            "roof": "partial",
            "walls": "none",
            "floor": "none",
            "windows": "double_glazing"
        },
        "solar_panels": 0,
        "heat_pump": False
    },
    "demo-456": {
        "address": "Wilhelminastraat 45, Utrecht",
        "type": "vrijstaand",
        "build_year": 1972,
        "living_area": 180,
        "energy_label": "E",
        "residents": 3,
        "current_heating": "cv-ketel",
        "insulation": {
            "roof": "none",
            "walls": "none", 
            "floor": "none",
            "windows": "single_glazing"
        },
        "solar_panels": 0,
        "heat_pump": False
    }
}

DEMO_CONSUMPTION = {
    "demo-123": {
        "electricity": {
            "annual_kwh": 3500,
            "monthly_pattern": [350, 320, 300, 280, 250, 220, 200, 210, 240, 280, 310, 340]
        },
        "gas": {
            "annual_m3": 1400,
            "monthly_pattern": [200, 180, 150, 120, 80, 40, 20, 30, 60, 100, 160, 190]
        }
    },
    "demo-456": {
        "electricity": {
            "annual_kwh": 4800,
            "monthly_pattern": [480, 450, 420, 380, 340, 300, 280, 290, 330, 380, 430, 470]
        },
        "gas": {
            "annual_m3": 2200,
            "monthly_pattern": [320, 290, 240, 190, 130, 60, 30, 40, 90, 160, 250, 300]
        }
    }
}


def get_energy_profile_impl(deal_id: str) -> Dict[str, Any]:
    """
    Get complete energy profile for a deal including home assessment data,
    current energy usage, costs, and CO2 emissions
    """
    if DEMO_MODE:
        # Return comprehensive demo data simulating real energy profile
        demo_data = {
            "yearlyGasUsage": 1400,
            "yearlyElectricityUsage": 3500,
            "yearlyElectricityReturn": 0,
            "gasTariff": 1.25,  # Updated to current market average (June 2025)
            "electricityTariff": 0.25,  # Updated to current market average (June 2025)
            "returnTariff": 0.17,  # Updated to current market average (June 2025)
            "networkCosts": 40,
            "surfaceArea": 120,
            "numberOfResidents": 4,
            "buildingYear": 1985,
            "property_type": "tussenwoning",
            "wozValue": 335000,
            "energyLabel": "D",
            "wall_insulation": "none",
            "roof_insulation": "partial",
            "floor_insulation": "none",
            "glass_type": "double",
            "heating_system": "cv_ketel",
            "heating_age": 8,
            "has_heat_pump": False,
            "wants_heat_pump": True,
            "suitable_for_solar": True,
            "has_solar_panels": False,
            "num_solar_panels": 0,
            "roof_orientation": "south",
            "available_roof_area": 45,
            "thermostatDay": 20,
            "thermostatNight": 18,
            "comfortComplaints": ["cold_floors", "draft"],
            "ventilationBehavior": "moderate"
        }
        
        # Calculate current costs
        gas_cost = demo_data["yearlyGasUsage"] * demo_data["gasTariff"]
        electricity_cost = demo_data["yearlyElectricityUsage"] * demo_data["electricityTariff"]
        return_income = demo_data["yearlyElectricityReturn"] * demo_data["returnTariff"]
        total_cost = gas_cost + electricity_cost - return_income + (demo_data["networkCosts"] * 12)
        
        # Calculate CO2 emissions
        gas_co2 = demo_data["yearlyGasUsage"] * 1.78  # kg CO2 per m³
        electricity_co2 = demo_data["yearlyElectricityUsage"] * 0.4  # kg CO2 per kWh
        total_co2 = gas_co2 + electricity_co2
        
        return {
            "deal_id": deal_id,
            "current_usage": {
                "gas": demo_data["yearlyGasUsage"],
                "electricity": demo_data["yearlyElectricityUsage"],
                "solar_return": demo_data["yearlyElectricityReturn"]
            },
            "tariffs": {
                "gas": demo_data["gasTariff"],
                "electricity": demo_data["electricityTariff"],
                "return": demo_data["returnTariff"],
                "network": demo_data["networkCosts"]
            },
            "current_costs": {
                "gas": gas_cost,
                "electricity": electricity_cost,
                "return_income": return_income,
                "network": demo_data["networkCosts"] * 12,
                "total_yearly": total_cost,
                "total_monthly": total_cost / 12
            },
            "co2_emissions": {
                "gas": gas_co2,
                "electricity": electricity_co2,
                "total": total_co2
            },
            "benchmarks": {
                "average_gas_similar_homes": 1300,
                "average_electricity_similar_homes": 3200,
                "gas_percentile": 65,  # Uses more gas than 65% of similar homes
                "electricity_percentile": 60
            },
            "house_profile": {
                "type": demo_data["property_type"],
                "year": demo_data["buildingYear"],
                "area": demo_data["surfaceArea"],
                "residents": demo_data["numberOfResidents"],
                "energy_label": demo_data["energyLabel"],
                "woz_value": demo_data["wozValue"]
            },
            "insulation_status": {
                "walls": demo_data["wall_insulation"],
                "roof": demo_data["roof_insulation"],
                "floor": demo_data["floor_insulation"],
                "windows": demo_data["glass_type"]
            },
            "heating": {
                "system": demo_data["heating_system"],
                "age": demo_data["heating_age"],
                "wants_heat_pump": demo_data["wants_heat_pump"]
            },
            "solar": {
                "suitable": demo_data["suitable_for_solar"],
                "has_panels": demo_data["has_solar_panels"],
                "current_panels": demo_data["num_solar_panels"],
                "roof_orientation": demo_data["roof_orientation"],
                "available_area": demo_data["available_roof_area"]
            },
            "comfort": {
                "thermostat_day": demo_data["thermostatDay"],
                "thermostat_night": demo_data["thermostatNight"],
                "complaints": demo_data["comfortComplaints"],
                "ventilation": demo_data["ventilationBehavior"]
            },
            "customer_context": get_customer_context_from_assessment(demo_data),
            "assessment_data": demo_data  # Include full assessment data for backward compatibility
        }
    
    # Real mode - fetch from Supabase
    try:
        # 1. Get deal with appointment and contact info
        try:
            deal_response = supabase.table('deals') \
                .select('*, appointments!deals_appointment_id_fkey(*), contacts!inner(*)') \
                .eq('id', deal_id) \
                .single() \
                .execute()
        except Exception as e:
            # Handle "no rows found" case specifically
            if "no rows returned" in str(e) or "PGRST116" in str(e):
                # Check if this might be a contact_id instead of deal_id
                contact_check = supabase.table('deals') \
                    .select('id, contact_id') \
                    .eq('contact_id', deal_id) \
                    .execute()
                
                if contact_check.data:
                    correct_deal_id = contact_check.data[0]['id']
                    return {
                        "error": f"Deal not found. ID '{deal_id}' appears to be a contact_id, not a deal_id",
                        "suggestion": f"Try using deal_id: {correct_deal_id}",
                        "deal_id": deal_id
                    }
                
                return {
                    "error": "Deal not found. Please verify the deal_id is correct",
                    "deal_id": deal_id,
                    "available_deals": [d['id'] for d in supabase.table('deals').select('id').limit(5).execute().data]
                }
            else:
                raise e
        
        if not deal_response.data:
            # Check if this might be a contact_id instead of deal_id
            contact_check = supabase.table('deals') \
                .select('id, contact_id') \
                .eq('contact_id', deal_id) \
                .execute()
            
            if contact_check.data:
                correct_deal_id = contact_check.data[0]['id']
                return {
                    "error": f"Deal not found. ID '{deal_id}' appears to be a contact_id, not a deal_id",
                    "suggestion": f"Try using deal_id: {correct_deal_id}",
                    "deal_id": deal_id
                }
            
            return {
                "error": "Deal not found. Please verify the deal_id is correct",
                "deal_id": deal_id,
                "available_deals": [d['id'] for d in supabase.table('deals').select('id').limit(5).execute().data]
            }
        
        deal = deal_response.data
        appointment_id = deal['appointment_id']
        
        # 2. Get home assessment
        assessment_response = supabase.table('home_assessments') \
            .select('*') \
            .eq('appointment_id', appointment_id) \
            .single() \
            .execute()
        
        if not assessment_response.data:
            return {
                "error": "Home assessment not found for deal",
                "deal_id": deal_id,
                "appointment_id": appointment_id
            }
        
        assessment = assessment_response.data
        data = assessment.get('assessment_data', {})
        
        # 3. Calculate current energy costs
        gas_usage = data.get('yearlyGasUsage') or 0
        electricity_usage = data.get('yearlyElectricityUsage') or 0
        electricity_return = data.get('yearlyElectricityReturn') or 0
        gas_tariff = data.get('gasTariff') or 1.25  # Current market average fallback
        electricity_tariff = data.get('electricityTariff') or 0.25  # Current market average fallback
        return_tariff = data.get('returnTariff') or 0.17  # Current market average fallback
        network_costs = data.get('networkCosts') or 40
        
        gas_cost = gas_usage * gas_tariff
        electricity_cost = electricity_usage * electricity_tariff
        return_income = electricity_return * return_tariff
        total_cost = gas_cost + electricity_cost - return_income + (network_costs * 12)
        
        # 4. Calculate CO2 emissions
        gas_co2 = gas_usage * 1.78  # kg CO2 per m³ gas
        electricity_co2 = electricity_usage * 0.4  # kg CO2 per kWh
        total_co2 = gas_co2 + electricity_co2
        
        # 5. Compare to benchmarks (simplified for now)
        surface_area = data.get('surfaceArea') or 100
        residents = data.get('numberOfResidents') or 2
        
        # Average gas usage per m² for Dutch homes
        avg_gas_per_m2 = 12  # m³/m²
        expected_gas = surface_area * avg_gas_per_m2
        gas_percentile = min(95, max(5, 50 + ((gas_usage - expected_gas) / expected_gas * 100)))
        
        # Average electricity per resident
        avg_electricity_per_resident = 1200  # kWh/resident
        expected_electricity = residents * avg_electricity_per_resident
        electricity_percentile = min(95, max(5, 50 + ((electricity_usage - expected_electricity) / expected_electricity * 100)))
        
        # Get contact info from the deal
        contact = deal.get('contacts', {})
        
        return {
            'deal_id': deal_id,
            'contact_info': {
                'id': contact.get('id', ''),
                'name': f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip(),
                'email': contact.get('email', ''),
                'phone': contact.get('phone', ''),
                'address': contact.get('address', ''),
                'postal_code': contact.get('postal_code', ''),
                'city': contact.get('city', ''),
                'province': contact.get('province', '')
            },
            'current_usage': {
                'gas': gas_usage,
                'electricity': electricity_usage,
                'solar_return': electricity_return
            },
            'tariffs': {
                'gas': gas_tariff,
                'electricity': electricity_tariff,
                'return': return_tariff,
                'network': network_costs
            },
            'current_costs': {
                'gas': gas_cost,
                'electricity': electricity_cost,
                'return_income': return_income,
                'network': network_costs * 12,
                'total_yearly': total_cost,
                'total_monthly': total_cost / 12
            },
            'co2_emissions': {
                'gas': gas_co2,
                'electricity': electricity_co2,
                'total': total_co2
            },
            'benchmarks': {
                'average_gas_similar_homes': expected_gas,
                'average_electricity_similar_homes': expected_electricity,
                'gas_percentile': int(gas_percentile),
                'electricity_percentile': int(electricity_percentile)
            },
            'house_profile': {
                'type': data.get('property_type', 'unknown'),
                'year': data.get('buildingYear', 0),
                'area': surface_area,
                'residents': residents,
                'energy_label': data.get('energyLabel', 'Unknown'),
                'woz_value': data.get('wozValue', 0)
            },
            'insulation_status': {
                'walls': data.get('wall_insulation', 'none'),
                'roof': data.get('roof_insulation', 'none'),
                'floor': data.get('floor_insulation', 'none'),
                'windows': data.get('glass_type', 'double')
            },
            'heating': {
                'system': data.get('heating_system', 'cv_ketel'),
                'age': data.get('heating_age', 10),
                'wants_heat_pump': data.get('wants_heat_pump', False)
            },
            'solar': {
                'suitable': data.get('suitable_for_solar', True),
                'has_panels': data.get('has_solar_panels', False),
                'current_panels': data.get('num_solar_panels', 0),
                'roof_orientation': data.get('roof_orientation', 'unknown'),
                'available_area': data.get('available_roof_area', 0)
            },
            'comfort': {
                'thermostat_day': data.get('thermostatDay', 20),
                'thermostat_night': data.get('thermostatNight', 18),
                'complaints': data.get('comfortComplaints', []),
                'ventilation': data.get('ventilationBehavior', 'moderate')
            },
            'advisor_notes': {
                'general': data.get('generalNotes', ''),
                'technical_inspection': data.get('technicalInspection', {}),
                'current_measures': data.get('currentMeasures', [])
            },
            'customer_context': get_customer_context_from_assessment(data),
            'assessment_data': data  # Include full assessment data for backward compatibility
        }
        
    except Exception as e:
        return {
            "error": f"Failed to fetch energy profile: {str(e)}",
            "deal_id": deal_id
        }


def get_quote_products_impl(deal_id: str) -> Dict[str, Any]:
    """
    Get all products from the deal's quote including quantities and specifications
    """
    if DEMO_MODE:
        # Return demo products for testing
        return {
            "deal_id": deal_id,
            "products": [
                {
                    "id": "prod-1",
                    "name": "Hybride Warmtepomp",
                    "category": "Heating",
                    "quantity": 1,
                    "unit_price": 3500,
                    "total_price": 3500,
                    "subsidy_code": "WP-H",
                    "subsidy_amount": 2100,
                    "technical_specs": {
                        "cop": 4.0,
                        "power_kw": 5.0
                    }
                },
                {
                    "id": "prod-2",
                    "name": "Spouwmuurisolatie",
                    "category": "Insulation",
                    "quantity": 85,
                    "unit_price": 22,
                    "total_price": 1870,
                    "subsidy_code": "ISO-SW",
                    "subsidy_amount": 425,
                    "subsidy_amount_per_unit": 5,  # Min rate €5/m²
                    "subsidy_amount_max": 8,       # Max rate €8/m²
                    "technical_specs": {
                        "material": "EPS parels",
                        "lambda_value": 0.034
                    }
                },
                {
                    "id": "prod-3",
                    "name": "Dakisolatie (zonder afwerking)",
                    "category": "Insulation",
                    "quantity": 60,
                    "unit_price": 45,
                    "total_price": 2700,
                    "subsidy_code": "ISO-DK",
                    "subsidy_amount": 975,
                    "subsidy_amount_per_unit": 16.25,  # Min rate €16.25/m²
                    "subsidy_amount_max": 30,           # Max rate €30/m²
                    "technical_specs": {
                        "material": "Glaswol",
                        "rd_value": 4.5
                    }
                },
                {
                    "id": "prod-4",
                    "name": "Bodemisolatie",
                    "category": "Insulation",
                    "quantity": 50,
                    "unit_price": 35,
                    "total_price": 1750,
                    "subsidy_code": "ISO-BD",
                    "subsidy_amount": 375,
                    "subsidy_amount_per_unit": 7.50,   # Min rate €7.50/m²
                    "subsidy_amount_max": 10,           # Max rate €10/m²
                    "technical_specs": {
                        "material": "PUR schuim",
                        "rd_value": 3.5
                    }
                }
            ],
            "totals": {
                "products_count": 4,
                "total_investment": 9820,
                "total_subsidies": 3875,
                "net_investment": 5945
            }
        }
    
    # Real mode - fetch from Supabase
    try:
        # 1. Get deal to find quote
        try:
            deal_response = supabase.table('deals') \
                .select('final_quote_id, quote_id') \
                .eq('id', deal_id) \
                .single() \
                .execute()
        except Exception as e:
            if "no rows returned" in str(e) or "PGRST116" in str(e):
                # Check if this might be a contact_id instead of deal_id
                contact_check = supabase.table('deals') \
                    .select('id, contact_id') \
                    .eq('contact_id', deal_id) \
                    .execute()
                
                if contact_check.data:
                    correct_deal_id = contact_check.data[0]['id']
                    return {
                        "error": f"Deal not found. ID '{deal_id}' appears to be a contact_id, not a deal_id",
                        "suggestion": f"Try using deal_id: {correct_deal_id}",
                        "deal_id": deal_id
                    }
                
                return {
                    "error": "Deal not found. Please verify the deal_id is correct",
                    "deal_id": deal_id
                }
            else:
                raise e
        
        if not deal_response.data:
            return {
                "error": "Deal not found",
                "deal_id": deal_id
            }
        
        deal = deal_response.data
        quote_id = deal['final_quote_id'] or deal['quote_id']
        
        if not quote_id:
            return {
                "error": "No quote found for deal",
                "deal_id": deal_id
            }
        
        # 2. Get quote details including loan information
        quote_response = supabase.table('quotes') \
            .select('*') \
            .eq('id', quote_id) \
            .single() \
            .execute()
        
        quote_data = quote_response.data if quote_response.data else {}
        
        # 3. Get quote items with products
        quote_items_response = supabase.table('quote_items') \
            .select('*, products!inner(*)') \
            .eq('quote_id', quote_id) \
            .execute()
        
        if not quote_items_response.data:
            return {
                "error": "No products found in quote",
                "deal_id": deal_id,
                "quote_id": quote_id
            }
        
        # 3. Format products data
        products = []
        total_investment = 0
        total_subsidies = 0
        
        for item in quote_items_response.data:
            product = item['products']
            
            product_data = {
                "id": product['id'],
                "name": product['name'],
                "category": product.get('category', 'Other'),
                "quantity": item.get('quantity', 1),
                "unit_price": round(float(item.get('unit_price_incl_vat') or 0), 2),
                "total_price": round(float(item.get('total_item_price_incl_vat') or 0), 2),
                "subsidy_code": product.get('subsidy_code'),
                "subsidy_amount": round(float(item.get('item_subsidy_estimate', 0) or 0), 2),
                "technical_specs": product.get('technical_specs', {}),
                "calculation_impact": product.get('calculation_impact', []),
                "warranty_years": product.get('warranty_years', 10)
            }
            
            products.append(product_data)
            total_investment += float(item.get('total_item_price_incl_vat') or 0)
            total_subsidies += float(item.get('item_subsidy_estimate', 0) or 0)
        
        # Extract loan information with defaults for NULL values
        loan_info = {
            "income_category": quote_data.get('loan_income_category', '<60k'),  # Default to <60k if NULL
            "municipality": quote_data.get('loan_municipality', ''),
            "term_years": quote_data.get('loan_term_years') or 15,  # Default to 15 years if NULL
            "interest_rate": float(quote_data.get('loan_interest_rate') or 0),  # Default to 0% if NULL
            "monthly_payment": float(quote_data.get('loan_monthly_payment') or 0)
        }
        
        # Calculate monthly payment if not provided
        net_investment = total_investment - float(quote_data.get('total_subsidy_estimate') or total_subsidies)
        if loan_info['monthly_payment'] == 0 and net_investment > 0 and loan_info['term_years'] > 0:
            # Simple calculation: net investment / (term years * 12 months)
            # This is a simplified calculation without interest
            loan_info['monthly_payment'] = net_investment / (loan_info['term_years'] * 12)
        
        return {
            "deal_id": deal_id,
            "quote_id": quote_id,
            "payment_method": quote_data.get('payment_method', ''),
            "products": products,
            "loan": loan_info,
            "totals": {
                "products_count": len(products),
                "total_investment": round(total_investment, 2),
                "total_subsidies": round(float(quote_data.get('total_subsidy_estimate') or total_subsidies), 2),
                "net_investment": round(net_investment, 2)
            }
        }
        
    except Exception as e:
        return {
            "error": f"Failed to fetch quote products: {str(e)}",
            "deal_id": deal_id
        }


def get_contact_info_impl(deal_id: str) -> Dict[str, Any]:
    """
    Get contact information for the customer associated with the deal
    """
    if DEMO_MODE:
        return {
            "deal_id": deal_id,
            "contact": {
                "id": "contact-123",
                "name": "Jan de Vries",
                "email": "jan.devries@example.com",
                "phone": "+31612345678",
                "address": "Keizersgracht 123",
                "postal_code": "1015 CJ",
                "city": "Amsterdam",
                "province": "Noord-Holland"
            },
            "appointment": {
                "date": "2024-01-15",
                "advisor_name": "Peter Bakker",
                "advisor_role": "Energie Adviseur"
            }
        }
    
    # Real mode - fetch from Supabase
    try:
        # Get deal with contact and appointment info
        try:
            deal_response = supabase.table('deals') \
                .select('''
                    *,
                    contacts!inner(*),
                    appointments!deals_appointment_id_fkey(*)
                ''') \
                .eq('id', deal_id) \
                .single() \
                .execute()
        except Exception as e:
            if "no rows returned" in str(e) or "PGRST116" in str(e):
                # Check if this might be a contact_id instead of deal_id
                contact_check = supabase.table('deals') \
                    .select('id, contact_id') \
                    .eq('contact_id', deal_id) \
                    .execute()
                
                if contact_check.data:
                    correct_deal_id = contact_check.data[0]['id']
                    return {
                        "error": f"Deal not found. ID '{deal_id}' appears to be a contact_id, not a deal_id",
                        "suggestion": f"Try using deal_id: {correct_deal_id}",
                        "deal_id": deal_id
                    }
                
                return {
                    "error": "Deal not found. Please verify the deal_id is correct",
                    "deal_id": deal_id
                }
            else:
                raise e
        
        if not deal_response.data:
            return {
                "error": "Deal not found",
                "deal_id": deal_id
            }
        
        deal = deal_response.data
        contact = deal['contacts']
        appointment = deal['appointments']
        
        # Get advisor info separately
        advisor_name = "Adviseur"
        advisor_role = "Energie Adviseur"
        if appointment.get('closer_id'):
            advisor_response = supabase.table('profiles') \
                .select('full_name, role') \
                .eq('id', appointment['closer_id']) \
                .single() \
                .execute()
            if advisor_response.data:
                advisor_name = advisor_response.data.get('full_name', 'Adviseur')
                advisor_role = advisor_response.data.get('role', 'Energie Adviseur')
        
        return {
            "deal_id": deal_id,
            "contact": {
                "id": contact['id'],
                "name": f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip(),
                "email": contact.get('email', ''),
                "phone": contact.get('phone', ''),
                "address": contact.get('address', ''),
                "postal_code": contact.get('postal_code', ''),
                "city": contact.get('city', ''),
                "province": contact.get('province', '')
            },
            "appointment": {
                "date": appointment.get('appointment_date', ''),
                "advisor_name": advisor_name,
                "advisor_role": advisor_role
            }
        }
        
    except Exception as e:
        return {
            "error": f"Failed to fetch contact info: {str(e)}",
            "deal_id": deal_id
        }




def get_customer_context_from_assessment(assessment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract or infer customer context from assessment data
    This provides personalization data for the report
    """
    # Check if customerContext already exists in assessment data
    if 'customerContext' in assessment_data:
        return assessment_data['customerContext']
    
    # Otherwise, create smart defaults based on available data
    context = {
        "primaryMotivation": "cost_savings",  # Default
        "personalityType": "big_picture",     # Default
        "keyConcerns": ["monthly_payment", "roi"],  # Default concerns
        "lifeSituation": "young_family",      # Default or infer
        "decisionTimeline": "exploring",      # Default
        "specialCircumstances": [],
        "memorableQuotes": {
            "customerSaid": "",
            "mainWorry": "",
            "excitedAbout": ""
        },
        "advisorObservations": assessment_data.get('generalNotes', '')
    }
    
    # Smart inference based on data
    
    # Infer primary motivation
    gas_usage = assessment_data.get('yearlyGasUsage', 0)
    if gas_usage > 1500:
        context['primaryMotivation'] = 'cost_savings'
    elif assessment_data.get('has_solar_panels', False):
        context['primaryMotivation'] = 'environmental'
    elif assessment_data.get('comfortComplaints', []):
        context['primaryMotivation'] = 'comfort'
    
    # Infer personality type from notes
    notes = assessment_data.get('generalNotes', '').lower()
    if 'technisch' in notes or 'details' in notes:
        context['personalityType'] = 'detail_oriented'
    elif 'sceptisch' in notes or 'twijfel' in notes:
        context['personalityType'] = 'skeptical'
    elif 'enthousiast' in notes:
        context['personalityType'] = 'enthusiastic'
    
    # Infer life situation
    residents = assessment_data.get('numberOfResidents', 2)
    building_year = assessment_data.get('buildingYear', 2000)
    
    if residents >= 4:
        context['lifeSituation'] = 'young_family'
    elif residents <= 2 and building_year < 1990:
        context['lifeSituation'] = 'empty_nesters'
    elif residents == 1:
        context['lifeSituation'] = 'single_professional'
    elif 'werkruimte' in notes or 'thuiswerk' in notes:
        context['lifeSituation'] = 'working_from_home'
    
    # Extract concerns from comfort complaints
    complaints = assessment_data.get('comfortComplaints', [])
    if complaints:
        if any('koud' in c.lower() or 'tocht' in c.lower() for c in complaints if isinstance(c, str)):
            context['keyConcerns'].append('comfort')
        if any('vocht' in c.lower() or 'schimmel' in c.lower() for c in complaints if isinstance(c, str)):
            context['keyConcerns'].append('health')
    
    # Check for special circumstances in notes
    if 'batterij' in notes:
        context['specialCircumstances'].append('battery_interest')
    if 'off grid' in notes or 'off-grid' in notes:
        context['specialCircumstances'].append('off_grid_interest')
    if 'saldering' in notes:
        context['specialCircumstances'].append('net_metering_concerns')
    if 'dakkapel' in notes or 'dak' in notes:
        context['specialCircumstances'].append('roof_concerns')
    
    # Extract quotes if present in notes
    if '"' in notes:
        # Simple quote extraction - in production would use better parsing
        import re
        quotes = re.findall(r'"([^"]+)"', notes)
        if quotes:
            context['memorableQuotes']['customerSaid'] = quotes[0]
    
    return context


def get_comprehensive_deal_data_impl(deal_id: str) -> Dict[str, Any]:
    """
    Get all deal data in a single comprehensive query.
    This includes energy profile, products, subsidies, market data, and more.
    """
    if DEMO_MODE:
        # Return comprehensive demo data
        timestamp = datetime.now().isoformat()
        
        # Get individual components
        energy_profile = get_energy_profile_impl(deal_id)
        quote_products = get_quote_products_impl(deal_id)
        contact_info = get_contact_info_impl(deal_id)
        
        # Build comprehensive structure
        return {
            "deal_id": deal_id,
            "timestamp": timestamp,
            
            # Customer Information
            "customer": {
                "id": contact_info["contact"]["id"],
                "name": contact_info["contact"]["name"],
                "email": contact_info["contact"]["email"],
                "phone": contact_info["contact"]["phone"],
                "address": contact_info["contact"]["address"],
                "postal_code": contact_info["contact"]["postal_code"],
                "city": contact_info["contact"]["city"],
                "province": contact_info["contact"]["province"]
            },
            
            # Property Profile
            "property": {
                "type": energy_profile["house_profile"]["type"],
                "year": energy_profile["house_profile"]["year"],
                "area": energy_profile["house_profile"]["area"],
                "residents": energy_profile["house_profile"]["residents"],
                "energy_label": energy_profile["house_profile"]["energy_label"],
                "woz_value": energy_profile["house_profile"]["woz_value"],
                "is_owner": True,  # Demo default
                "is_rental": False  # Demo default
            },
            
            # Current Energy Usage & Costs
            "energy": {
                "usage": {
                    "gas_m3": energy_profile["current_usage"]["gas"],
                    "electricity_kwh": energy_profile["current_usage"]["electricity"],
                    "solar_return_kwh": energy_profile["current_usage"]["solar_return"]
                },
                "tariffs": energy_profile["tariffs"],
                "costs": energy_profile["current_costs"],
                "co2_emissions": energy_profile["co2_emissions"],
                "benchmarks": energy_profile["benchmarks"]
            },
            
            # Current Systems & Status
            "current_systems": {
                "heating": energy_profile["heating"],
                "insulation": energy_profile["insulation_status"],
                "solar": energy_profile["solar"],
                "comfort": energy_profile["comfort"]
            },
            
            # Quote & Products with Pricing
            "quote": {
                "id": quote_products.get("quote_id", "demo-quote-123"),
                "date": timestamp,
                "payment_method": quote_products.get("payment_method", "loan"),
                "products": [
                    {
                        **prod,
                        "subsidy": {
                            "code": prod.get("subsidy_code", ""),
                            "amount": prod.get("subsidy_amount", 0),
                            "type": "ISDE",
                            "description": f"ISDE subsidie voor {prod['name']}"
                        }
                    }
                    for prod in quote_products["products"]
                ],
                "totals": quote_products["totals"],
                "financing": {
                    "type": "loan",
                    "loan": quote_products.get("loan", {
                        "amount": quote_products["totals"]["net_investment"],
                        "term_years": 15,
                        "interest_rate": 0.0,
                        "monthly_payment": quote_products["totals"]["net_investment"] / (15 * 12),
                        "income_category": "<60k",
                        "municipality": contact_info["contact"]["city"]
                    })
                }
            },
            
            # Regulations & Subsidies Detail
            "regulations": {
                "subsidies": {
                    "isde": {
                        "total": quote_products["totals"]["total_subsidies"],
                        "items": [
                            {
                                "product": prod["name"],
                                "code": prod.get("subsidy_code", ""),
                                "quantity": prod["quantity"],
                                "unit": "m²" if prod["category"] == "Insulation" else "stuk",
                                "rate": prod["subsidy_amount"] / prod["quantity"] if prod["quantity"] > 0 else 0,
                                "amount": prod["subsidy_amount"],
                                "description": f"ISDE subsidie voor {prod['name']}"
                            }
                            for prod in quote_products["products"]
                            if prod.get("subsidy_amount", 0) > 0
                        ]
                    },
                    "municipal": {
                        "total": 0,
                        "items": []
                    }
                },
                "requirements": [
                    "Werkzaamheden nog niet gestart bij aanvraag",
                    "Aanvraag binnen 24 maanden na installatie",
                    "Installatie door gecertificeerd installateur"
                ],
                "documentation": [
                    "Kopie facturen met specificatie maatregelen",
                    "Foto's van voor en na de werkzaamheden",
                    "Installatieverklaring warmtepomp"
                ],
                "warnings": []
            },
            
            # Market Intelligence Data
            "market": {
                "price_trends": {
                    "energy_prices": {
                        "current": {
                            "gas": energy_profile["tariffs"]["gas"],
                            "electricity": energy_profile["tariffs"]["electricity"]
                        },
                        "forecast": {
                            "1_year": {"gas": 1.30, "electricity": 0.26},
                            "5_year": {"gas": 1.45, "electricity": 0.30}
                        }
                    },
                    "product_prices": {
                        "heat_pump": {"trend": "stable"},
                        "insulation": {"trend": "rising"},
                        "solar": {"trend": "falling"}
                    }
                },
                "installers": {
                    "region": contact_info["contact"]["city"],
                    "availability": "medium",
                    "lead_time_days": 30
                }
            },
            
            # Advisor Context
            "context": {
                "appointment": contact_info["appointment"],
                "customer_profile": energy_profile["customer_context"],
                "advisor_notes": energy_profile.get("advisor_notes", {})
            },
            
            # Raw assessment data for backward compatibility
            "assessment_data": energy_profile.get("assessment_data", {})
        }
    
    # Real mode - fetch from Supabase with comprehensive query
    try:
        # Single comprehensive query to get all related data
        deal_response = supabase.table('deals') \
            .select('''
                *,
                contacts!inner(*),
                appointments!deals_appointment_id_fkey(
                    *,
                    home_assessments(*)
                ),
                quotes!deals_final_quote_id_fkey(
                    *,
                    quote_items(
                        *,
                        products!inner(*)
                    )
                )
            ''') \
            .eq('id', deal_id) \
            .single() \
            .execute()
        
        if not deal_response.data:
            return {"error": "Deal not found", "deal_id": deal_id}
        
        deal = deal_response.data
        contact = deal['contacts']
        appointment = deal.get('appointments')
        quote = deal.get('quotes')
        
        # Get quote from either final_quote_id or quote_id
        if not quote and deal.get('quote_id'):
            quote_response = supabase.table('quotes') \
                .select('''
                    *,
                    quote_items(
                        *,
                        products!inner(*)
                    )
                ''') \
                .eq('id', deal['quote_id']) \
                .single() \
                .execute()
            quote = quote_response.data if quote_response.data else {}
        
        # Get assessment data from appointment
        assessment_data = {}
        if appointment and 'home_assessments' in appointment and appointment['home_assessments']:
            # Get the first (and usually only) assessment
            if isinstance(appointment['home_assessments'], list) and len(appointment['home_assessments']) > 0:
                assessment_data = appointment['home_assessments'][0].get('assessment_data', {})
            elif isinstance(appointment['home_assessments'], dict):
                assessment_data = appointment['home_assessments'].get('assessment_data', {})
        
        # Get energy data from assessment or use defaults
        gas_usage = assessment_data.get('yearlyGasUsage', 1500)
        electricity_usage = assessment_data.get('yearlyElectricityUsage', 3500)
        electricity_return = assessment_data.get('yearlyElectricityReturn', 0)
        
        gas_tariff = assessment_data.get('gasTariff', 1.45)
        electricity_tariff = assessment_data.get('electricityTariff', 0.40)
        return_tariff = assessment_data.get('returnTariff', 0.17)
        network_costs = assessment_data.get('networkCosts', 40)
        
        # Calculate costs
        gas_cost = gas_usage * gas_tariff
        electricity_cost = electricity_usage * electricity_tariff
        return_income = electricity_return * return_tariff
        total_cost = gas_cost + electricity_cost - return_income + (network_costs * 12)
        
        # Calculate CO2
        gas_co2 = gas_usage * 1.78
        electricity_co2 = electricity_usage * 0.4
        total_co2 = gas_co2 + electricity_co2
        
        # Process products and subsidies
        products = []
        total_investment = 0
        total_subsidies = 0
        subsidy_items = []
        
        # First pass: count insulation products for ISDE multiple measures rule
        insulation_count = 0
        if quote and quote.get('quote_items'):
            for item in quote['quote_items']:
                product = item['products']
                if product.get('category') == 'Insulation':
                    insulation_count += 1
        
        print(f"Total insulation products found: {insulation_count}")
        
        if quote and quote.get('quote_items'):
            for item in quote['quote_items']:
                product = item['products']
                
                # Get subsidy amount from quote
                quote_subsidy = float(item.get('item_subsidy_estimate', 0) or 0)
                
                # Calculate subsidy based on product catalog rules
                if product.get('subsidy_code'):
                    # Get quantity and subsidy parameters
                    quantity = float(item.get('quantity', 1))
                    subsidy_per_unit = float(product.get('subsidy_amount_per_unit') or 0)
                    subsidy_min = float(product.get('subsidy_amount_min') or 0)
                    subsidy_max_raw = product.get('subsidy_amount_max')
                    subsidy_unit = product.get('subsidy_unit', 'stuk')
                    
                    # Check if this is an insulation product for ISDE rules
                    is_insulation = product.get('category') == 'Insulation'
                    
                    # Calculate subsidy based on subsidy_unit
                    if subsidy_unit == 'm2':
                        # For per-m2 subsidies, min/max are per-unit rates
                        if is_insulation:
                            # Apply ISDE multiple insulation measures rule
                            if insulation_count >= 2:
                                # With 2+ insulation measures, use maximum rate
                                rate_per_unit = float(subsidy_max_raw) if subsidy_max_raw else subsidy_per_unit
                            else:
                                # With 0-1 insulation measures, use minimum rate
                                rate_per_unit = subsidy_min
                        else:
                            # Non-insulation m2 products use the per-unit rate
                            rate_per_unit = subsidy_per_unit
                        
                        subsidy_amount = quantity * rate_per_unit
                    else:
                        # For 'stuk' subsidies, min/max are total amounts
                        calculated_subsidy = quantity * subsidy_per_unit
                        subsidy_max = float(subsidy_max_raw) if subsidy_max_raw else float('inf')
                        # Apply min/max constraints to total
                        subsidy_amount = max(subsidy_min, min(calculated_subsidy, subsidy_max))
                    
                    # Log if there was any constraint applied for debugging
                    if subsidy_unit == 'm2' and is_insulation:
                        actual_rate = subsidy_amount / quantity if quantity > 0 else 0
                        print(f"Subsidy calculation for {product['name']}: {quantity} {subsidy_unit} × €{actual_rate:.2f}/{subsidy_unit} = €{subsidy_amount:.2f}")
                    
                    # Log if there's a mismatch with quote
                    if quote_subsidy != subsidy_amount:
                        print(f"Corrected subsidy for {product['name']}: €{subsidy_amount} (was €{quote_subsidy} in quote)")
                else:
                    # Fallback to quote value if no product catalog value
                    subsidy_amount = quote_subsidy
                
                product_data = {
                    "id": product['id'],
                    "name": product['name'],
                    "category": product.get('category', 'Other'),
                    "quantity": item.get('quantity', 1),
                    "unit": product.get('subsidy_unit', 'stuk'),
                    "unit_price": round(float(item.get('unit_price_incl_vat') or 0), 2),
                    "total_price": round(float(item.get('total_item_price_incl_vat') or 0), 2),
                    "warranty_years": product.get('warranty_years', 10),
                    "technical_specs": product.get('technical_specs', {}),
                    "calculation_impact": product.get('calculation_impact', []),
                    "subsidy": {
                        "code": product.get('subsidy_code', ''),
                        "amount": round(subsidy_amount, 2),
                        "type": "ISDE",
                        "description": f"ISDE subsidie voor {product['name']}"
                    }
                }
                
                products.append(product_data)
                total_investment += float(item.get('total_item_price_incl_vat') or 0)
                
                # Add to subsidy items if has subsidy
                if product_data["subsidy"]["amount"] > 0:
                    subsidy_items.append({
                        "product": product['name'],
                        "code": product.get('subsidy_code', ''),
                        "quantity": item.get('quantity', 1),
                        "unit": product_data["unit"],
                        "rate": product_data["subsidy"]["amount"] / item.get('quantity', 1) if item.get('quantity', 1) > 0 else 0,
                        "amount": product_data["subsidy"]["amount"],
                        "description": product_data["subsidy"]["description"]
                    })
        
        # ISDE multiple insulation measures rule is now handled in the initial calculation above
        # We apply the correct rate (min or max) based on insulation_count during the constraint logic
        
        # Calculate total subsidies from corrected product amounts
        # Don't trust quote total if we had to correct individual subsidies
        total_subsidies = sum(p["subsidy"]["amount"] for p in products)
        
        # Get advisor info
        advisor_name = "Adviseur"
        advisor_role = "Energie Adviseur"
        if appointment and appointment.get('closer_id'):
            advisor_response = supabase.table('profiles') \
                .select('full_name, role') \
                .eq('id', appointment['closer_id']) \
                .single() \
                .execute()
            if advisor_response.data:
                advisor_name = advisor_response.data.get('full_name', 'Adviseur')
                advisor_role = advisor_response.data.get('role', 'Energie Adviseur')
        
        # Build comprehensive response
        return {
            "deal_id": deal_id,
            "timestamp": datetime.now().isoformat(),
            
            # Customer Information
            "customer": {
                "id": contact['id'],
                "name": f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip(),
                "email": contact.get('email', ''),
                "phone": contact.get('phone', ''),
                "address": contact.get('address', ''),
                "postal_code": contact.get('postal_code', ''),
                "city": contact.get('city', ''),
                "province": contact.get('province', '')
            },
            
            # Property Profile from assessment data
            "property": {
                "type": assessment_data.get('property_type', 'rijtjeshuis'),
                "year": assessment_data.get('buildingYear', 1985),
                "area": assessment_data.get('surfaceArea', 120),
                "residents": assessment_data.get('numberOfResidents', 2),
                "energy_label": assessment_data.get('energyLabel', 'D'),
                "woz_value": assessment_data.get('wozValue', 250000),
                "is_owner": assessment_data.get('is_owner', True),
                "is_rental": assessment_data.get('is_rental', False)
            },
            
            # Current Energy Usage & Costs
            "energy": {
                "usage": {
                    "gas_m3": gas_usage,
                    "electricity_kwh": electricity_usage,
                    "solar_return_kwh": electricity_return
                },
                "tariffs": {
                    "gas": gas_tariff,
                    "electricity": electricity_tariff,
                    "return": return_tariff,
                    "network": network_costs
                },
                "costs": {
                    "gas": round(gas_cost, 2),
                    "electricity": round(electricity_cost, 2),
                    "return_income": round(return_income, 2),
                    "network": round(network_costs * 12, 2),
                    "total_yearly": round(total_cost, 2),
                    "total_monthly": round(total_cost / 12, 2)
                },
                "co2_emissions": {
                    "gas": round(gas_co2, 2),
                    "electricity": round(electricity_co2, 2),
                    "total": round(total_co2, 2)
                },
                "benchmarks": {
                    "avg_gas_similar": assessment_data.get('surfaceArea', 120) * 12,
                    "avg_electricity_similar": assessment_data.get('numberOfResidents', 2) * 1200,
                    "gas_percentile": 50,  # Would need calculation
                    "electricity_percentile": 50  # Would need calculation
                }
            },
            
            # Current Systems & Status
            "current_systems": {
                "heating": {
                    "system": assessment_data.get('heating_system', 'cv_ketel'),
                    "age": assessment_data.get('heating_age', 10),
                    "wants_heat_pump": assessment_data.get('wants_heat_pump', False)
                },
                "insulation": {
                    "walls": assessment_data.get('wall_insulation', 'none'),
                    "roof": assessment_data.get('roof_insulation', 'none'),
                    "floor": assessment_data.get('floor_insulation', 'none'),
                    "windows": assessment_data.get('glass_type', 'double')
                },
                "solar": {
                    "has_panels": assessment_data.get('has_solar_panels', False),
                    "current_panels": assessment_data.get('num_solar_panels', 0),
                    "suitable": assessment_data.get('suitable_for_solar', True),
                    "roof_orientation": assessment_data.get('roof_orientation', 'south'),
                    "available_area": assessment_data.get('available_roof_area', 30)
                },
                "comfort": {
                    "thermostat_day": assessment_data.get('thermostatDay', 20),
                    "thermostat_night": assessment_data.get('thermostatNight', 18),
                    "complaints": assessment_data.get('comfortComplaints', []),
                    "ventilation": assessment_data.get('ventilationBehavior', 'moderate')
                }
            },
            
            # Quote & Products with Pricing
            "quote": {
                "id": quote.get('id', '') if quote else '',
                "date": quote.get('created_at', '') if quote else '',
                "payment_method": quote.get('payment_method', '') if quote else '',
                "products": products,
                "totals": {
                    "products_count": len(products),
                    "total_investment": round(total_investment, 2),
                    "total_subsidies": round(total_subsidies, 2),
                    "net_investment": round(total_investment - total_subsidies, 2)
                },
                "financial_summary": {
                    "total_investment": round(total_investment, 2),
                    "total_subsidies": round(total_subsidies, 2),
                    "net_investment": round(total_investment - total_subsidies, 2)
                },
                "financing": {
                    "type": quote.get('payment_method', 'loan') if quote else 'loan',
                    "loan": {
                        "amount": round(total_investment - total_subsidies, 2),
                        "term_years": quote.get('loan_term_years', 15) if quote else 15,
                        "interest_rate": float(quote.get('loan_interest_rate') or 0) if quote else 0,
                        "monthly_payment": float(quote.get('loan_monthly_payment') or 0) if quote else 0,
                        "income_category": quote.get('loan_income_category') or '<60k' if quote else '<60k',
                        "municipality": contact.get('city', '')
                    }
                }
            },
            
            # Regulations & Subsidies Detail
            "regulations": {
                "subsidies": {
                    "isde": {
                        "total": round(total_subsidies, 2),
                        "items": subsidy_items
                    },
                    "municipal": {
                        "total": 0,
                        "items": []
                    }
                },
                "requirements": [
                    "Werkzaamheden nog niet gestart bij aanvraag",
                    "Aanvraag binnen 24 maanden na installatie",
                    "Installatie door gecertificeerd installateur"
                ],
                "documentation": [
                    "Kopie facturen met specificatie maatregelen",
                    "Foto's van voor en na de werkzaamheden",
                    "Installatieverklaring warmtepomp"
                ],
                "warnings": [] if assessment_data.get('is_owner', True) else ["ISDE subsidies vereisen een eigen woning"]
            },
            
            # Market Intelligence Data
            "market": {
                "price_trends": {
                    "energy_prices": {
                        "current": {
                            "gas": gas_tariff,
                            "electricity": electricity_tariff
                        },
                        "forecast": {
                            "1_year": {"gas": gas_tariff * 1.04, "electricity": electricity_tariff * 1.04},
                            "5_year": {"gas": gas_tariff * 1.16, "electricity": electricity_tariff * 1.20}
                        }
                    },
                    "product_prices": {
                        "heat_pump": {"trend": "stable"},
                        "insulation": {"trend": "rising"},
                        "solar": {"trend": "falling"}
                    }
                },
                "installers": {
                    "region": contact.get('city', ''),
                    "availability": "medium",
                    "lead_time_days": 30
                }
            },
            
            # Advisor Context
            "context": {
                "appointment": {
                    "date": appointment.get('appointment_date', '') if appointment else '',
                    "advisor_name": advisor_name,
                    "advisor_role": advisor_role
                },
                "customer_profile": get_customer_context_from_assessment(assessment_data),
                "advisor_notes": {
                    "general": assessment_data.get('generalNotes', ''),
                    "technical_inspection": assessment_data.get('technicalInspection', {}),
                    "current_measures": assessment_data.get('currentMeasures', [])
                }
            },
            
            # Raw assessment data for backward compatibility
            "assessment_data": assessment_data
        }
        
    except Exception as e:
        return {
            "error": f"Failed to fetch comprehensive deal data: {str(e)}",
            "deal_id": deal_id
        }


# MCP tool wrappers for future FastAgent integration
@mcp.tool()
def get_energy_profile(deal_id: str) -> Dict[str, Any]:
    """MCP wrapper for get_energy_profile_impl"""
    return get_energy_profile_impl(deal_id)

@mcp.tool()
def get_quote_products(deal_id: str) -> Dict[str, Any]:
    """MCP wrapper for get_quote_products_impl"""
    return get_quote_products_impl(deal_id)

@mcp.tool()
def get_contact_info(deal_id: str) -> Dict[str, Any]:
    """MCP wrapper for get_contact_info_impl"""
    return get_contact_info_impl(deal_id)

@mcp.tool()
def get_comprehensive_deal_data(deal_id: str) -> Dict[str, Any]:
    """
    Get all deal data in a single comprehensive query.
    This tool consolidates all data fetching into one call, including:
    - Customer information and contact details
    - Property profile and energy assessment
    - Current energy usage, costs, and CO2 emissions
    - Current systems (heating, insulation, solar)
    - Complete quote with products and pricing
    - Subsidies and regulations
    - Market intelligence and trends
    - Advisor context and notes
    
    Returns a comprehensive JSON structure with all deal-related data.
    """
    return get_comprehensive_deal_data_impl(deal_id)


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()