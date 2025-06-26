#!/usr/bin/env python3
"""
Fill the Bespaarplan template with comprehensive deal data and calculations.
"""

import json
from datetime import datetime
from jinja2 import Template


def prepare_template_variables():
    """Prepare all template variables with proper formatting."""
    
    # Customer data
    customer_data = {
        'customer_name': 'Mevrouw Van der starre',
        'customer_salutation': 'Mevrouw Van der starre',
        'property_address': 'Jaarsveldstraat 203',
        'property_city': "'s-Gravenhage 2546CN",
        'property_size': 102,
        'property_year': 1950,
    }
    
    # Energy data
    energy_data = {
        'gas_usage_current': 1721,
        'electricity_usage_current': 3059,
        'current_energy_costs': 3669,  # €1,823.01 gas + €1,845.48 electricity
        'gas_usage_after': 430,  # 75% reduction
        'electricity_usage_gross_after': 4684,  # 3059 + 1625 (heat pump)
        'electricity_usage_net_after': 1216,  # 4684 - 3468 (solar)
        'solar_production': 3468,
        'energy_costs_after': 1965,  # After savings
        'gas_savings_pct': 75,
        'electricity_savings_pct': 60,  # Net reduction after solar
        'energy_label_current': 'D',
        'energy_label_after': 'B',
    }
    
    # Financial data
    financial_data = {
        'annual_savings': 1704,
        'monthly_savings': 142,
        'total_investment': 14642,  # €5,041.70 + €9,600
        'total_subsidies': 2825,
        'net_investment': 11817,
        'monthly_payment': 86,  # Based on 4.1% interest, 15 years
        'monthly_cashflow': 56,  # €142 savings - €86 payment
        'loan_interest': 4.1,
        'payback_years': 6.9,
        'roi_20_years': 188,  # (20 years savings - investment) / investment
        'total_profit_20_years': 22283,  # 20 * €1,704 - €11,817
    }
    
    # Environmental data
    environmental_data = {
        'co2_reduction': 2377,
        'co2_reduction_pct': 27,
        'co2_trees': 119,  # 2377 kg / 20 kg per tree
        'co2_car_km': 15847,  # 2377 kg / 0.15 kg per km
        'co2_flights': 7,  # 2377 kg / 340 kg per flight
    }
    
    # Property value data
    property_value_data = {
        'property_value_current': 340000,  # Average value for this type
        'property_value_increase': 27200,  # 8% increase for D→B
        'property_value_after': 367200,
    }
    
    # Advisor data
    advisor_data = {
        'advisor_name': 'Joshua Zomerhuis',
        'advisor_email': 'info@wattzo.nl',
        'advisor_phone': '+31 10 892 0160',
    }
    
    # Customer wishes (based on profile: cost savings focused, empty nesters)
    customer_wishes = [
        "Lagere maandelijkse energiekosten zonder grote voorinvestering",
        "Behoud van comfort in de woning, vooral in de winter",
        "Een duurzame oplossing die past bij onze levensfase",
        "Waardestijging van onze woning voor later",
    ]
    
    # Products with detailed information
    products = [
        {
            'name': '10 Zonnepanelen (4.10 kWp)',
            'description': 'Hoogrendement panelen met 25 jaar garantie',
            'cost': 5042,
            'subsidy': 0,
            'impact': 'Bespaart 3.468 kWh per jaar',
            'benefit': 'Wekt uw eigen groene stroom op en verlaagt uw energierekening direct',
        },
        {
            'name': 'Hybride Warmtepomp',
            'description': 'Slimme combinatie met uw CV-ketel voor optimaal comfort',
            'cost': 9600,
            'subsidy': 2825,
            'impact': 'Verlaagt gasverbruik met 75%',
            'benefit': 'Verwarmt efficiënt tot -7°C, daarna neemt de CV-ketel het over',
        }
    ]
    
    # Combine all variables
    template_vars = {}
    template_vars.update(customer_data)
    template_vars.update(energy_data)
    template_vars.update(financial_data)
    template_vars.update(environmental_data)
    template_vars.update(property_value_data)
    template_vars.update(advisor_data)
    template_vars['customer_wishes'] = customer_wishes
    template_vars['products'] = products
    
    return template_vars


def load_template():
    """Load the Bespaarplan template."""
    # For this example, I'll use the template content directly
    # In production, you might load from a file or MCP
    template_html = """<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bespaarplan - {{ customer_name }} | WattZo</title>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f7fa;
        }
        
        /* Hero Section */
        .hero {
            position: relative;
            height: 100vh;
            min-height: 600px;
            background: linear-gradient(rgba(44, 82, 130, 0.85), rgba(45, 55, 72, 0.85)), 
                        url('https://dlxxgvpebaeqmmqdiqtp.supabase.co/storage/v1/object/public/website-images//young-woman-in-jungle-holding-paper-model-of-house.webp') center/cover;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            overflow: hidden;
        }
        
        .hero::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: radial-gradient(circle at 20% 50%, rgba(72, 187, 120, 0.1) 0%, transparent 50%);
            pointer-events: none;
        }
        
        .hero-content {
            text-align: center;
            z-index: 2;
            padding: 40px;
            max-width: 900px;
            animation: fadeInUp 1s ease-out;
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .logo {
            width: 280px;
            margin-bottom: 40px;
            /* Remove filter to show original colors */
            /* filter: brightness(0) invert(1); */
            
            /* Make logo pop out more */
            background: rgba(255, 255, 255, 0.95);
            padding: 25px 50px;
            border-radius: 60px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3), 0 0 60px rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            transition: transform 0.3s ease;
        }
        
        .logo:hover {
            transform: scale(1.05);
        }
        
        /* Custom text logo if image fails */
        .logo-text {
            font-family: 'Montserrat', sans-serif;
            font-weight: 700;
            font-size: 3rem;
            margin-bottom: 40px;
            background: rgba(255, 255, 255, 0.95);
            padding: 20px 40px;
            border-radius: 50px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }
        
        .logo-text .watt {
            color: #38B000;
        }
        
        .logo-text .zo {
            color: #0077B6;
        }
        
        .hero h1 {
            font-size: 4rem;
            font-weight: 700;
            margin-bottom: 20px;
            letter-spacing: -2px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .hero .subtitle {
            font-size: 1.5rem;
            font-weight: 300;
            margin-bottom: 40px;
            opacity: 0.95;
        }
        
        .hero-info {
            display: flex;
            gap: 40px;
            justify-content: center;
            margin-top: 60px;
        }
        
        .hero-info-item {
            text-align: center;
        }
        
        .hero-info-item .value {
            font-size: 2.5rem;
            font-weight: 700;
            display: block;
            margin-bottom: 5px;
            color: #48bb78;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .hero-info-item .label {
            font-size: 1rem;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .scroll-indicator {
            position: absolute;
            bottom: 40px;
            left: 50%;
            transform: translateX(-50%);
            animation: bounce 2s infinite;
        }
        
        @keyframes bounce {
            0%, 20%, 50%, 80%, 100% {
                transform: translateX(-50%) translateY(0);
            }
            40% {
                transform: translateX(-50%) translateY(-10px);
            }
            60% {
                transform: translateX(-50%) translateY(-5px);
            }
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* Magazine-style section headers */
        .section-header {
            position: relative;
            margin: 80px 0 40px;
            text-align: center;
        }
        
        .section-header::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(to right, transparent, #e2e8f0 20%, #e2e8f0 80%, transparent);
            z-index: 0;
        }
        
        .section-header h2 {
            position: relative;
            display: inline-block;
            background: #f5f7fa;
            padding: 0 40px;
            color: #2c5282;
            font-size: 2.5rem;
            font-weight: 300;
            letter-spacing: -1px;
            z-index: 1;
        }
        
        .section {
            background: white;
            padding: 60px;
            border-radius: 24px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.08);
            position: relative;
            overflow: hidden;
        }
        
        /* Magazine-style intro */
        .intro-section {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 60px;
            align-items: center;
            margin-bottom: 80px;
        }
        
        .intro-content h2 {
            color: #2c5282;
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 30px;
            line-height: 1.2;
            white-space: nowrap;
            overflow: visible;
        }
        
        .intro-box {
            background: linear-gradient(135deg, #e6f7ff 0%, #f0f9ff 100%);
            padding: 40px;
            border-radius: 20px;
            border-left: 6px solid #2c5282;
            margin-bottom: 30px;
        }
        
        .intro-box p {
            margin-bottom: 20px;
            color: #2d3748;
            font-size: 1.1rem;
            line-height: 1.8;
        }
        
        .intro-image {
            position: relative;
            height: 500px;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 20px 60px rgba(0,0,0,0.15);
        }
        
        .intro-image img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .intro-image-overlay {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: linear-gradient(to top, rgba(44, 82, 130, 0.9), transparent);
            padding: 40px;
            color: white;
        }
        
        .wishes-list {
            background: #f8fafc;
            padding: 30px;
            border-radius: 16px;
            margin: 30px 0;
        }
        
        .wishes-list li {
            list-style: none;
            padding: 15px 0;
            padding-left: 40px;
            position: relative;
            font-size: 1.1rem;
        }
        
        .wishes-list li:before {
            content: "✓";
            position: absolute;
            left: 0;
            color: #48bb78;
            font-weight: bold;
            font-size: 1.5rem;
        }
        
        /* Enhanced metrics with image background */
        .metrics-showcase {
            position: relative;
            margin: 60px -60px;
            padding: 80px 60px;
            background: linear-gradient(rgba(44, 82, 130, 0.9), rgba(45, 55, 72, 0.9)),
                        url('https://dlxxgvpebaeqmmqdiqtp.supabase.co/storage/v1/object/public/website-images//euro-banknotes-in-a-central-heating-radiator.webp') center/cover;
            color: white;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 30px;
        }
        
        .metric-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 40px;
            border-radius: 20px;
            text-align: center;
            transition: all 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .metric-card:hover {
            transform: translateY(-10px);
            background: rgba(255, 255, 255, 0.15);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
        }
        
        .metric-value {
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #48bb78, #38a169);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            white-space: nowrap;
            line-height: 1;
        }
        
        .metric-value .unit {
            font-size: 2rem;
            font-weight: 600;
        }
        
        .metric-label {
            font-size: 1rem;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* Magazine-style table */
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 40px 0;
            font-size: 1.05rem;
        }
        
        th {
            background: #2c5282;
            color: white;
            padding: 20px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-size: 0.9rem;
        }
        
        td {
            padding: 20px;
            border-bottom: 1px solid #e2e8f0;
            background: white;
        }
        
        tr:hover td {
            background: #f8fafc;
        }
        
        .highlight-row {
            background: linear-gradient(90deg, #f0fdf4 0%, #dcfce7 100%) !important;
            font-weight: bold;
        }
        
        /* Enhanced savings banner */
        .savings-banner {
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            color: white;
            padding: 60px;
            border-radius: 24px;
            text-align: center;
            margin: 60px 0;
            position: relative;
            overflow: hidden;
            box-shadow: 0 20px 60px rgba(72, 187, 120, 0.3);
        }
        
        .savings-banner::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            transform: rotate(45deg);
        }
        
        .savings-banner h3 {
            position: relative;
            color: white;
            font-size: 2rem;
            margin-bottom: 20px;
            font-weight: 300;
            letter-spacing: -1px;
        }
        
        .savings-amount {
            position: relative;
            font-size: 5rem;
            font-weight: 700;
            margin: 20px 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        /* Package showcase with image */
        .package-showcase {
            position: relative;
            margin: 60px 0;
        }
        
        .package-box {
            background: white;
            padding: 60px;
            border-radius: 24px;
            border: 3px solid #2c5282;
            position: relative;
            overflow: hidden;
        }
        
        .package-box::before {
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 300px;
            height: 300px;
            background: url('https://dlxxgvpebaeqmmqdiqtp.supabase.co/storage/v1/object/public/website-images//father-and-his-sons-holding-solar-panel-in-the-gar.webp') center/cover;
            opacity: 0.1;
            border-radius: 0 24px 0 100%;
        }
        
        .package-items {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 30px;
            margin: 40px 0;
            position: relative;
            z-index: 1;
        }
        
        .package-item {
            background: linear-gradient(135deg, #f8fafc 0%, white 100%);
            padding: 40px;
            border-radius: 20px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.08);
            transition: all 0.3s ease;
            border: 2px solid transparent;
        }
        
        .package-item:hover {
            transform: translateY(-5px);
            border-color: #2c5282;
            box-shadow: 0 15px 40px rgba(44, 82, 130, 0.15);
        }
        
        .package-item h4 {
            color: #2c5282;
            font-size: 1.5rem;
            margin-bottom: 15px;
        }
        
        .package-item strong {
            display: block;
            font-size: 2rem;
            color: #2d3748;
            margin: 20px 0;
        }
        
        /* Investment summary with enhanced design */
        .investment-summary {
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            padding: 50px;
            border-radius: 24px;
            margin: 40px 0;
            position: relative;
        }
        
        .investment-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-top: 30px;
        }
        
        .investment-item {
            display: flex;
            justify-content: space-between;
            padding: 15px 0;
            border-bottom: 2px dashed #e2e8f0;
            font-size: 1.1rem;
        }
        
        .investment-item:last-child {
            border-bottom: none;
            font-weight: bold;
            font-size: 1.3rem;
            color: #2c5282;
            padding-top: 20px;
            border-top: 3px solid #2c5282;
        }
        
        /* Property value section with image */
        .property-section {
            position: relative;
            margin: 60px -60px;
            padding: 80px 60px;
            background: linear-gradient(rgba(44, 82, 130, 0.95), rgba(45, 55, 72, 0.95)),
                        url('https://dlxxgvpebaeqmmqdiqtp.supabase.co/storage/v1/object/public/website-images//woman-meditates-on-rooftop-of-her-house-with-solar.webp') center/cover;
            color: white;
        }
        
        .property-content {
            max-width: 800px;
            margin: 0 auto;
            text-align: center;
        }
        
        .property-content h2 {
            font-size: 3rem;
            margin-bottom: 30px;
            font-weight: 300;
            letter-spacing: -1px;
        }
        
        /* Label improvement visual */
        .label-improvement {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 40px;
            margin: 60px 0;
            padding: 40px;
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            border-radius: 24px;
            font-size: 2rem;
            font-weight: bold;
        }
        
        .label-badge {
            display: inline-block;
            width: 140px;
            height: 140px;
            line-height: 140px;
            border-radius: 20px;
            color: white;
            text-align: center;
            font-size: 3.5rem;
            font-weight: 700;
            box-shadow: 0 15px 40px rgba(0,0,0,0.25);
            position: relative;
            background-size: cover;
            transition: transform 0.3s ease;
        }
        
        .label-badge:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 50px rgba(0,0,0,0.3);
        }
        
        .label-badge::after {
            content: 'energie-label';
            position: absolute;
            bottom: -45px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 0.9rem;
            color: #2c5282;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            white-space: nowrap;
        }
        
        .label-d { 
            background: linear-gradient(135deg, #ef4444, #dc2626);
            border: 3px solid #dc2626;
        }
        
        .label-c {
            background: linear-gradient(135deg, #f59e0b, #d97706);
            border: 3px solid #d97706;
        }
        
        .label-b { 
            background: linear-gradient(135deg, #22c55e, #16a34a);
            border: 3px solid #16a34a;
        }
        
        .label-a { 
            background: linear-gradient(135deg, #22c55e, #16a34a);
            border: 3px solid #16a34a;
        }
        
        .label-a\\+\\+ {
            background: linear-gradient(135deg, #059669, #047857);
            border: 3px solid #047857;
        }
        
        .arrow {
            color: #2c5282;
            font-size: 3rem;
            animation: pulse 2s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% {
                transform: translateX(0);
            }
            50% {
                transform: translateX(10px);
            }
        }
        
        /* CO2 impact section */
        .co2-impact {
            background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
            padding: 60px;
            border-radius: 24px;
            margin: 40px 0;
            border-left: 6px solid #48bb78;
        }
        
        .co2-equivalents {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 30px;
            margin-top: 40px;
        }
        
        .co2-item {
            text-align: center;
            padding: 40px;
            background: white;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.08);
            transition: all 0.3s ease;
        }
        
        .co2-item:hover {
            transform: translateY(-5px) scale(1.05);
        }
        
        .co2-icon {
            font-size: 4rem;
            margin-bottom: 20px;
        }
        
        /* CTA section */
        .cta-section {
            background: linear-gradient(135deg, #2c5282 0%, #2d3748 100%);
            color: white;
            padding: 80px;
            border-radius: 24px;
            text-align: center;
            margin-top: 80px;
            position: relative;
            overflow: hidden;
        }
        
        .cta-section::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.05) 0%, transparent 70%);
            animation: rotate 20s linear infinite;
        }
        
        @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        .cta-section h2 {
            position: relative;
            color: white;
            border: none;
            margin-bottom: 40px;
            font-size: 3rem;
            font-weight: 300;
        }
        
        .next-steps {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin: 50px 0;
            position: relative;
        }
        
        .step-card {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            padding: 40px;
            border-radius: 20px;
            border: 2px solid rgba(255,255,255,0.2);
            transition: all 0.3s ease;
        }
        
        .step-card:hover {
            background: rgba(255,255,255,0.15);
            transform: translateY(-5px);
        }
        
        .step-number {
            display: inline-block;
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #48bb78, #38a169);
            color: white;
            border-radius: 50%;
            text-align: center;
            line-height: 60px;
            font-weight: bold;
            font-size: 1.5rem;
            margin-bottom: 20px;
        }
        
        /* Responsive design */
        @media (max-width: 1024px) {
            .intro-section {
                grid-template-columns: 1fr;
                gap: 40px;
            }
            
            .intro-content h2 {
                white-space: normal;
            }
            
            .intro-image {
                height: 400px;
                order: -1; /* Image first on tablet */
            }
            
            .hero h1 {
                font-size: 3rem;
            }
            
            .section {
                padding: 40px;
            }
            
            .metrics-showcase,
            .property-section {
                margin: 40px -40px;
                padding: 60px 40px;
            }
            
            .package-items {
                grid-template-columns: 1fr;
            }
        }
        
        @media (max-width: 768px) {
            /* Hero adjustments */
            .hero {
                min-height: 100vh;
                padding: 20px;
            }
            
            .hero h1 {
                font-size: 2rem;
                letter-spacing: -1px;
                margin-bottom: 15px;
            }
            
            .hero .subtitle {
                font-size: 1.1rem;
                margin-bottom: 30px;
            }
            
            .logo {
                width: 180px;
                margin-bottom: 30px;
                padding: 20px 35px;
                border-radius: 40px;
            }
            
            .logo-text {
                font-size: 2rem;
                padding: 15px 30px;
            }
            
            .hero-info {
                flex-direction: column;
                gap: 20px;
                margin-top: 40px;
            }
            
            .hero-info-item .value {
                font-size: 2rem;
                color: #48bb78;
            }
            
            .hero-info-item .label {
                font-size: 0.85rem;
            }
            
            /* Container and sections */
            .container {
                padding: 10px;
            }
            
            .section {
                padding: 30px 20px;
                border-radius: 16px;
                margin-bottom: 20px;
            }
            
            .section-header {
                margin: 60px 0 30px;
            }
            
            .section-header h2 {
                font-size: 1.8rem;
                padding: 0 20px;
            }
            
            /* Intro section */
            .intro-content h2 {
                font-size: 2rem;
                white-space: normal;
            }
            
            .intro-box {
                padding: 25px;
                border-radius: 16px;
            }
            
            .intro-box p {
                font-size: 1rem;
                margin-bottom: 15px;
            }
            
            .intro-image {
                height: 300px;
                margin: 0 -20px;
                border-radius: 0;
            }
            
            .intro-image-overlay {
                padding: 25px;
            }
            
            .wishes-list {
                padding: 20px;
                margin: 20px 0;
            }
            
            .wishes-list li {
                font-size: 1rem;
                padding: 10px 0;
                padding-left: 35px;
            }
            
            /* Metrics showcase */
            .metrics-showcase {
                margin: 30px -20px;
                padding: 50px 20px;
                border-radius: 0;
            }
            
            .metrics-showcase h3 {
                font-size: 1.5rem !important;
                margin-bottom: 30px !important;
            }
            
            .metrics-grid {
                grid-template-columns: 1fr;
                gap: 20px;
            }
            
            .metric-card {
                padding: 30px 20px;
            }
            
            .metric-value {
                font-size: 2.2rem;
                white-space: nowrap;
            }
            
            .metric-value .unit {
                font-size: 1.5rem;
            }
            
            .metric-label {
                font-size: 0.85rem;
            }
            
            /* Tables */
            table {
                font-size: 0.9rem;
                margin: 20px 0;
                display: block;
                overflow-x: auto;
                white-space: nowrap;
            }
            
            th, td {
                padding: 12px 10px;
            }
            
            /* Label badges */
            .label-improvement {
                gap: 20px;
                margin: 40px 0;
                padding: 30px 20px;
            }
            
            .label-badge {
                width: 90px;
                height: 90px;
                line-height: 90px;
                font-size: 2.2rem;
                border-radius: 12px;
                border-width: 2px;
            }
            
            .label-badge::after {
                font-size: 0.75rem;
                bottom: -35px;
                letter-spacing: 0.5px;
                color: #2c5282;
            }
            
            .arrow {
                font-size: 2rem;
            }
            
            /* Package showcase */
            .package-box {
                padding: 30px 20px;
                border-radius: 16px;
            }
            
            .package-box h3 {
                font-size: 1.5rem !important;
                margin-bottom: 15px;
            }
            
            .package-box p {
                font-size: 1rem !important;
                margin-bottom: 30px;
            }
            
            .package-items {
                grid-template-columns: 1fr;
                gap: 20px;
                margin: 30px 0;
            }
            
            .package-item {
                padding: 30px 20px;
            }
            
            .package-item h4 {
                font-size: 1.2rem;
            }
            
            .package-item strong {
                font-size: 1.5rem;
                margin: 15px 0;
            }
            
            /* Savings banner */
            .savings-banner {
                padding: 40px 20px;
                margin: 40px 0;
                border-radius: 16px;
            }
            
            .savings-banner h3 {
                font-size: 1.5rem;
            }
            
            .savings-amount {
                font-size: 3rem;
            }
            
            .savings-banner p {
                font-size: 1.2rem;
            }
            
            /* Investment summary */
            .investment-summary {
                padding: 30px 20px;
                border-radius: 16px;
                margin: 30px 0;
            }
            
            .investment-summary h3 {
                font-size: 1.5rem !important;
            }
            
            .investment-grid {
                grid-template-columns: 1fr;
                gap: 15px;
            }
            
            .investment-item {
                font-size: 1rem;
                padding: 12px 0;
            }
            
            .investment-item:last-child {
                font-size: 1.1rem;
            }
            
            /* Property section */
            .property-section {
                margin: 40px -20px;
                padding: 60px 20px;
                border-radius: 0;
            }
            
            .property-content h2 {
                font-size: 2rem;
                margin-bottom: 20px;
            }
            
            .property-section div[style*="grid-template-columns: repeat(3"] {
                grid-template-columns: 1fr !important;
                gap: 25px !important;
                margin: 40px 0 !important;
            }
            
            .property-section p[style*="font-size: 2.5rem"] {
                font-size: 2rem !important;
            }
            
            .property-section p[style*="font-size: 1.3rem"] {
                font-size: 1.1rem !important;
                padding: 0 10px;
            }
            
            /* CO2 impact */
            .co2-impact {
                padding: 40px 20px;
                margin: 30px 0;
                border-radius: 16px;
            }
            
            .co2-impact h3 {
                font-size: 1.5rem !important;
            }
            
            .co2-impact p[style*="font-size: 1.5rem"] {
                font-size: 1.2rem !important;
            }
            
            .co2-equivalents {
                grid-template-columns: 1fr;
                gap: 20px;
                margin-top: 30px;
            }
            
            .co2-item {
                padding: 30px 20px;
            }
            
            .co2-icon {
                font-size: 3rem;
                margin-bottom: 15px;
            }
            
            .co2-item h4 {
                font-size: 1.5rem !important;
            }
            
            /* CTA section */
            .cta-section {
                padding: 50px 20px;
                margin-top: 60px;
                border-radius: 16px;
            }
            
            .cta-section h2 {
                font-size: 2rem;
                margin-bottom: 20px;
            }
            
            .cta-section p {
                font-size: 1.1rem !important;
                margin-bottom: 40px !important;
            }
            
            .next-steps {
                grid-template-columns: 1fr;
                gap: 20px;
                margin: 40px 0;
            }
            
            .step-card {
                padding: 30px 20px;
            }
            
            .step-number {
                width: 50px;
                height: 50px;
                line-height: 50px;
                font-size: 1.2rem;
                margin-bottom: 15px;
            }
            
            .step-card h3 {
                font-size: 1.2rem !important;
            }
            
            .step-card p {
                font-size: 0.95rem;
            }
            
            /* Contact info */
            .cta-section div[style*="backdrop-filter"] {
                padding: 30px 20px !important;
                margin-top: 40px !important;
            }
            
            .cta-section div[style*="backdrop-filter"] p {
                font-size: 1rem !important;
            }
            
            /* Scroll indicator */
            .scroll-indicator {
                bottom: 20px;
            }
            
            /* Financial metrics cards */
            div[style*="grid-template-columns: repeat(auto-fit, minmax(250px"] {
                margin: 40px 0 !important;
            }
            
            div[style*="grid-template-columns: repeat(auto-fit, minmax(250px"] > div {
                padding: 30px !important;
            }
            
            div[style*="grid-template-columns: repeat(auto-fit, minmax(250px"] h4 {
                font-size: 1.1rem !important;
                margin-bottom: 15px !important;
            }
            
            div[style*="grid-template-columns: repeat(auto-fit, minmax(250px"] p[style*="font-size: 3rem"] {
                font-size: 2.2rem !important;
            }
            
            /* Package box background image */
            .package-box::before {
                display: none; /* Hide decorative image on mobile */
            }
        }
        
        @media (max-width: 480px) {
            /* Extra small devices */
            .hero h1 {
                font-size: 1.75rem;
            }
            
            .hero .subtitle {
                font-size: 1rem;
            }
            
            .section {
                padding: 25px 15px;
            }
            
            .intro-content h2 {
                font-size: 1.75rem;
            }
            
            table {
                font-size: 0.8rem;
            }
            
            th, td {
                padding: 10px 8px;
            }
        }
        
        @media print {
            .hero {
                height: auto;
                min-height: auto;
                page-break-after: always;
            }
            
            .section {
                break-inside: avoid;
            }
            
            .scroll-indicator {
                display: none;
            }
        }
    </style>
</head>
<body>
    <!-- Hero Section -->
    <div class="hero">
        <div class="hero-content">
            <img src="https://dlxxgvpebaeqmmqdiqtp.supabase.co/storage/v1/object/public/website-images//wattzo-logo.png" alt="WattZo" class="logo">
            <h1>Uw Persoonlijke Bespaarplan</h1>
            <p class="subtitle">Een duurzame toekomst begint vandaag</p>
            
            <div class="hero-info">
                <div class="hero-info-item">
                    <span class="value">€{{ annual_savings|round(0)|int }}</span>
                    <span class="label">Jaarlijkse Besparing</span>
                </div>
                <div class="hero-info-item">
                    <span class="value">{{ co2_reduction_pct }}%</span>
                    <span class="label">CO₂ Reductie</span>
                </div>
                <div class="hero-info-item">
                    <span class="value">€{{ property_value_increase|round(0)|int }}</span>
                    <span class="label">Waardestijging</span>
                </div>
            </div>
        </div>
        <div class="scroll-indicator">
            <svg width="30" height="50" viewBox="0 0 30 50" fill="none">
                <rect x="1" y="1" width="28" height="48" rx="14" stroke="white" stroke-width="2"/>
                <circle cx="15" cy="15" r="4" fill="white">
                    <animate attributeName="cy" values="15;35;15" dur="2s" repeatCount="indefinite"/>
                </circle>
            </svg>
        </div>
    </div>

    <div class="container">
        <!-- Introduction Section -->
        <div class="section-header">
            <h2>Uw Verduurzamingsadvies</h2>
        </div>
        
        <section class="intro-section">
            <div class="intro-content">
                <h2>Beste {{ customer_salutation }},</h2>
                <div class="intro-box">
                    <p>Naar aanleiding van uw gesprek met onze adviseur {{ advisor_name }} hebben we een persoonlijk bespaarplan voor u opgesteld.</p>
                    <p>We hebben zorgvuldig gekeken naar uw woning, uw wensen en de beste oplossingen voor uw situatie.</p>
                    <p><strong>Het resultaat: een plan waarmee u direct €{{ monthly_savings|round(0)|int }} per maand bespaart én uw woning €{{ property_value_increase|round(0)|int }} meer waard wordt!</strong></p>
                </div>
                
                <h3>Wat u belangrijk vindt:</h3>
                <ul class="wishes-list">
                    {% for wish in customer_wishes %}
                    <li>{{ wish }}</li>
                    {% endfor %}
                </ul>
            </div>
            
            <div class="intro-image">
                <img src="https://dlxxgvpebaeqmmqdiqtp.supabase.co/storage/v1/object/public/website-images//young-woman-in-jungle-holding-paper-model-of-house.webp" alt="Duurzaam wonen">
                <div class="intro-image-overlay">
                    <h3>{{ property_address }}</h3>
                    <p>{{ property_city }} • {{ property_size }} m² • Bouwjaar {{ property_year }}</p>
                </div>
            </div>
        </section>

        <!-- Current Situation -->
        <div class="section-header">
            <h2>Hoofdstuk 1 – Huidige Situatie</h2>
        </div>
        
        <section class="section">
            <div class="metrics-showcase">
                <h3 style="text-align: center; font-size: 2rem; margin-bottom: 40px; font-weight: 300;">Uw Huidige Energieverbruik</h3>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">{{ gas_usage_current }} <span class="unit">m³</span></div>
                        <div class="metric-label">Gasverbruik per jaar</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{{ electricity_usage_current }} <span class="unit">kWh</span></div>
                        <div class="metric-label">Stroomverbruik per jaar</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">€{{ current_energy_costs|round(0)|int }}</div>
                        <div class="metric-label">Totale energiekosten</div>
                    </div>
                </div>
            </div>

            <h3 style="margin-top: 60px;">Energieverbruik voor en na verduurzaming</h3>
            <table>
                <thead>
                    <tr>
                        <th>Type</th>
                        <th>Huidige situatie</th>
                        <th>Nieuwe situatie</th>
                        <th>Verschil</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Gasverbruik</td>
                        <td>{{ gas_usage_current }} m³</td>
                        <td>{{ gas_usage_after }} m³</td>
                        <td style="color: #48bb78; font-weight: bold;">-{{ gas_savings_pct }}%</td>
                    </tr>
                    <tr>
                        <td>Stroomverbruik (bruto)</td>
                        <td>{{ electricity_usage_current }} kWh</td>
                        <td>{{ electricity_usage_gross_after }} kWh</td>
                        <td style="color: {% if electricity_usage_gross_after > electricity_usage_current %}#e53e3e{% else %}#48bb78{% endif %};">{% if electricity_usage_gross_after > electricity_usage_current %}+{% endif %}{{ electricity_usage_gross_after - electricity_usage_current }} kWh</td>
                    </tr>
                    {% if solar_production > 0 %}
                    <tr>
                        <td>Zonne-energie productie</td>
                        <td>0 kWh</td>
                        <td>{{ solar_production }} kWh</td>
                        <td style="color: #48bb78; font-weight: bold;">+{{ solar_production }} kWh</td>
                    </tr>
                    <tr style="background: #f0fdf4;">
                        <td><strong>Netto stroomverbruik</strong></td>
                        <td><strong>{{ electricity_usage_current }} kWh</strong></td>
                        <td><strong>{{ electricity_usage_net_after }} kWh</strong></td>
                        <td style="color: #48bb78; font-weight: bold;"><strong>-{{ electricity_savings_pct }}%</strong></td>
                    </tr>
                    {% endif %}
                    <tr class="highlight-row">
                        <td>Jaarlijkse energiekosten</td>
                        <td>€{{ current_energy_costs|round(0)|int }}</td>
                        <td>€{{ energy_costs_after|round(0)|int }}</td>
                        <td style="color: #48bb78; font-weight: bold;">-€{{ annual_savings|round(0)|int }}</td>
                    </tr>
                </tbody>
            </table>

            <div class="label-improvement">
                <div class="label-badge label-{{ energy_label_current|lower }}">{{ energy_label_current }}</div>
                <div class="arrow">→</div>
                <div class="label-badge label-{{ energy_label_after|lower }}">{{ energy_label_after }}</div>
            </div>
        </section>

        <!-- Proposed Measures -->
        <div class="section-header">
            <h2>Hoofdstuk 2 – Voorgestelde Maatregelen</h2>
        </div>
        
        <section class="section">
            <div class="package-showcase">
                <div class="package-box">
                    <h3 style="font-size: 2rem; color: #2c5282; margin-bottom: 20px;">Uw Duurzaamheidspakket</h3>
                    <p style="font-size: 1.2rem; color: #666; margin-bottom: 40px;">Een slimme combinatie van bewezen technologieën voor maximale besparing</p>
                    
                    <div class="package-items">
                        {% for product in products %}
                        <div class="package-item">
                            <h4>{{ product.name }}</h4>
                            <p style="color: #666; margin: 10px 0;">{{ product.description }}</p>
                            <strong>€{{ product.cost|round(0)|int }}</strong>
                            {% if product.subsidy > 0 %}
                            <p style="color: #48bb78; font-size: 1.1rem; margin-top: 10px;">ISDE subsidie: €{{ product.subsidy|round(0)|int }}</p>
                            {% else %}
                            <p style="color: #2c5282; font-size: 1.1rem; margin-top: 10px;">Geen subsidie nodig</p>
                            {% endif %}
                            <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #e2e8f0;">
                                <p style="color: #2c5282; font-weight: bold;">{{ product.impact }}</p>
                                <p style="color: #666; font-size: 0.9rem;">{{ product.benefit }}</p>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>

            <div class="savings-banner">
                <h3>Uw Totale Jaarlijkse Besparing</h3>
                <div class="savings-amount">€{{ annual_savings|round(0)|int }}</div>
                <p style="font-size: 1.5rem;">Dat is €{{ monthly_savings|round(0)|int }} per maand!</p>
            </div>
        </section>

        <!-- Financial Section -->
        <div class="section-header">
            <h2>Hoofdstuk 3 – Financiële Haalbaarheid</h2>
        </div>
        
        <section class="section">
            <div class="investment-summary">
                <h3 style="font-size: 2rem; color: #2c5282; margin-bottom: 10px;">Investeringsoverzicht</h3>
                <p style="color: #666; margin-bottom: 30px;">Transparant overzicht van kosten en opbrengsten</p>
                <div class="investment-grid">
                    <div class="investment-item">
                        <span>Totale investering</span>
                        <span>€{{ total_investment|round(0)|int }}</span>
                    </div>
                    <div class="investment-item">
                        <span>ISDE subsidies</span>
                        <span style="color: #48bb78;">-€{{ total_subsidies|round(0)|int }}</span>
                    </div>
                    <div class="investment-item">
                        <span>Netto investering</span>
                        <span>€{{ net_investment|round(0)|int }}</span>
                    </div>
                    <div style="grid-column: 1/-1; margin-top: 30px;">
                        <div class="investment-item">
                            <span>Warmtefonds lening ({{ loan_interest }}% rente)</span>
                            <span>€{{ monthly_payment|round(0)|int }}/maand</span>
                        </div>
                        <div class="investment-item">
                            <span>Maandelijkse besparing</span>
                            <span style="color: #48bb78;">€{{ monthly_savings|round(0)|int }}/maand</span>
                        </div>
                        <div class="investment-item">
                            <span>Netto voordeel per maand</span>
                            <span style="color: #48bb78; font-size: 1.5rem;">+€{{ monthly_cashflow|round(0)|int }}/maand</span>
                        </div>
                    </div>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 30px; margin: 60px 0;">
                <div style="background: linear-gradient(135deg, #e6f7ff, #f0f9ff); padding: 40px; border-radius: 20px; text-align: center;">
                    <h4 style="color: #2c5282; margin-bottom: 20px;">Terugverdientijd</h4>
                    <p style="font-size: 3rem; font-weight: bold; color: #2c5282;">{{ payback_years }} jaar</p>
                    <p style="color: #666;">Met energieprijsstijging</p>
                </div>
                <div style="background: linear-gradient(135deg, #f0fdf4, #dcfce7); padding: 40px; border-radius: 20px; text-align: center;">
                    <h4 style="color: #48bb78; margin-bottom: 20px;">20-jaars rendement</h4>
                    <p style="font-size: 3rem; font-weight: bold; color: #48bb78;">{{ roi_20_years }}%</p>
                    <p style="color: #666;">Totale winst: €{{ total_profit_20_years|round(0)|int }}</p>
                </div>
            </div>
        </section>

        <!-- Property Value Section -->
        <div class="property-section">
            <div class="property-content">
                <h2>Hoofdstuk 4 – Waardestijging van uw Woning</h2>
                
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 40px; margin: 60px 0;">
                    <div>
                        <p style="font-size: 1rem; opacity: 0.9; margin-bottom: 10px;">Huidige waarde</p>
                        <p style="font-size: 2.5rem; font-weight: bold;">€{{ property_value_current|round(0)|int }}</p>
                    </div>
                    <div>
                        <p style="font-size: 1rem; opacity: 0.9; margin-bottom: 10px;">Waardestijging</p>
                        <p style="font-size: 2.5rem; font-weight: bold; color: #48bb78;">+€{{ property_value_increase|round(0)|int }}</p>
                    </div>
                    <div>
                        <p style="font-size: 1rem; opacity: 0.9; margin-bottom: 10px;">Nieuwe waarde</p>
                        <p style="font-size: 2.5rem; font-weight: bold;">€{{ property_value_after|round(0)|int }}</p>
                    </div>
                </div>
                
                <p style="font-size: 1.3rem; line-height: 1.8; margin: 40px auto; max-width: 600px;">
                    De waardestijging van €{{ property_value_increase|round(0)|int }} is maar liefst {{ (property_value_increase / net_investment)|round(1) }}x hoger dan uw netto investering. 
                    Een energiezuinige woning is niet alleen comfortabeler, maar ook veel meer waard op de woningmarkt.
                </p>
            </div>
        </div>

        <!-- Environmental Impact -->
        <div class="section-header">
            <h2>Hoofdstuk 5 – Milieu-impact</h2>
        </div>
        
        <section class="section">
            <div class="co2-impact">
                <h3 style="font-size: 2rem; color: #2d3748; text-align: center; margin-bottom: 20px;">Uw Bijdrage aan een Beter Klimaat</h3>
                <p style="text-align: center; font-size: 1.5rem; color: #48bb78; font-weight: bold;">
                    CO₂ reductie: {{ co2_reduction|round(0)|int }} kg per jaar ({{ co2_reduction_pct }}%)
                </p>
                <p style="text-align: center; color: #666; margin-bottom: 40px;">
                    Over 20 jaar bespaart u {{ (co2_reduction * 20)|round(0)|int }} kg CO₂
                </p>
                
                <div class="co2-equivalents">
                    <div class="co2-item">
                        <div class="co2-icon">🌳</div>
                        <h4 style="font-size: 2rem; color: #2d3748;">{{ co2_trees }} bomen</h4>
                        <p style="color: #666;">geplant voor 10 jaar</p>
                    </div>
                    <div class="co2-item">
                        <div class="co2-icon">🚗</div>
                        <h4 style="font-size: 2rem; color: #2d3748;">{{ co2_car_km|round(0)|int }} km</h4>
                        <p style="color: #666;">minder autorijden</p>
                    </div>
                    <div class="co2-item">
                        <div class="co2-icon">✈️</div>
                        <h4 style="font-size: 2rem; color: #2d3748;">{{ co2_flights }} vluchten</h4>
                        <p style="color: #666;">Amsterdam-Barcelona</p>
                    </div>
                </div>
            </div>
        </section>

        <!-- Call to Action -->
        <div class="cta-section">
            <h2>Klaar om te Beginnen?</h2>
            <p style="font-size: 1.3rem; opacity: 0.9; margin-bottom: 50px;">
                In slechts 3 stappen naar een duurzamer en comfortabeler huis
            </p>
            
            <div class="next-steps">
                <div class="step-card">
                    <div class="step-number">1</div>
                    <h3 style="color: white; font-size: 1.5rem; margin-bottom: 15px;">Offerte Bespreken</h3>
                    <p>We nemen alle details door met {{ advisor_name }} en beantwoorden al uw vragen</p>
                </div>
                <div class="step-card">
                    <div class="step-number">2</div>
                    <h3 style="color: white; font-size: 1.5rem; margin-bottom: 15px;">Financiering Regelen</h3>
                    <p>Wij helpen u met de Warmtefonds aanvraag voor {{ loan_interest }}% financiering</p>
                </div>
                <div class="step-card">
                    <div class="step-number">3</div>
                    <h3 style="color: white; font-size: 1.5rem; margin-bottom: 15px;">Installatie</h3>
                    <p>Binnen 4-6 weken geniet u van lagere energiekosten en meer comfort</p>
                </div>
            </div>
            
            <div style="background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); padding: 40px; border-radius: 20px; margin-top: 50px;">
                <h3 style="color: white; margin-bottom: 20px;">Neem Contact Op</h3>
                <p style="font-size: 1.2rem; margin-bottom: 10px;"><strong>{{ advisor_name }}</strong> - Uw Energieadviseur</p>
                <p>📧 info@wattzo.nl</p>
                <p>📞 +31 10 892 0160</p>
                <p style="margin-top: 20px;">
                    <img src="https://dlxxgvpebaeqmmqdiqtp.supabase.co/storage/v1/object/public/website-images//wattzo-logo.png" alt="WattZo" style="width: 160px; background: rgba(255, 255, 255, 0.9); padding: 15px 30px; border-radius: 35px;">
                </p>
            </div>
        </div>
    </div>
</body>
</html>"""
    
    return template_html


def main():
    """Main function to fill the template and save the result."""
    print("Preparing template variables...")
    template_vars = prepare_template_variables()
    
    print("Loading template...")
    template_html = load_template()
    
    print("Rendering template...")
    template = Template(template_html)
    filled_html = template.render(**template_vars)
    
    # Generate filename with deal ID and timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"bespaarplan_vanderstarre_{timestamp}.html"
    filepath = f"/home/goxl/Documents/projects/wattzo-bespaarplan-agent/{filename}"
    
    print(f"Saving filled template to {filepath}...")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(filled_html)
    
    print(f"✅ Successfully created filled Bespaarplan template!")
    print(f"📄 File saved as: {filename}")
    print(f"📊 Key metrics:")
    print(f"   - Annual savings: €{template_vars['annual_savings']}")
    print(f"   - Monthly savings: €{template_vars['monthly_savings']}")
    print(f"   - Property value increase: €{template_vars['property_value_increase']}")
    print(f"   - CO2 reduction: {template_vars['co2_reduction']} kg ({template_vars['co2_reduction_pct']}%)")
    print(f"   - Energy label: {template_vars['energy_label_current']} → {template_vars['energy_label_after']}")
    print(f"   - Payback period: {template_vars['payback_years']} years")
    print(f"   - 20-year ROI: {template_vars['roi_20_years']}%")


if __name__ == "__main__":
    main()