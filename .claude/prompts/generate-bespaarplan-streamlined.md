# Bespaarplan Generator - Streamlined Version

Generate a personalized energy savings plan (Bespaarplan) for the given deal ID.

## Process Steps

### 1. Get Deal Data
Use `get_comprehensive_deal_data` from energy-data MCP with the deal ID.

### 2. Parallel Processing
Execute these simultaneously in a single message:
- `calculate_from_deal_data` (calculation-engine MCP) with the deal data
- `get_bespaarplan_template` (template-provider MCP) with no parameters

### 3. Fill Template
Replace all placeholders in the template with values from:
- The comprehensive deal data (customer info, property details, energy usage)
- The calculated metrics (savings, ROI, CO2 reduction, property value)

**Data Usage Rules**:
- Only use information explicitly provided in the deal data
- Do NOT infer age, family composition, or lifestyle from limited data
- Treat `lifeSituation` and similar fields as advisor notes, not verified facts
- When demographic data is missing, use neutral language:
  - "uw huishouden" instead of specific family references
  - "u" instead of age-specific pronouns
  - Focus on property and savings, not lifestyle assumptions

**Number Formatting**: Apply Dutch formatting to numbers ≥1000:
- 1200 → 1.200
- 45500 → 45.500
- Exclude: percentages, years, quantities <1000

**Narratives**: Generate these four narratives based on VERIFIED data:
1. **Energy situation**: Current usage vs. future state (use actual consumption data)
2. **Personal savings**: Monthly/yearly financial benefits (avoid lifestyle assumptions)
3. **Property value**: Market context and value increase (focus on property facts)
4. **Environmental**: CO2 reduction and climate contribution (universal benefits)

**Narrative Guidelines**:
- Write for any household type - couple, family, single person, etc.
- Focus on universal benefits: comfort, savings, sustainability
- Use property characteristics (year, size, location) rather than assumed demographics
- Keep language inclusive and professional

**Dynamic Emphasis**: Set CSS class based on primary motivation:
- `cost_savings` → `emphasis-savings`
- `comfort` → `emphasis-comfort`
- `environment` → `emphasis-green`

### 4. Save Result
Use `save_filled_template` with:
- The filled HTML content
- Filename: `bespaarplan_[full_name_lowercase]` (e.g., `bespaarplan_john_jodhabier`)

## Expected Data Structure

The MCP tools provide pre-calculated values including:
- All financial metrics (annual_savings, monthly_savings, ROI, payback)
- Energy calculations (usage reduction, solar production)
- Environmental impact (CO2 reduction, equivalents)
- Property value increase
- Energy label improvement

## Notes
- Trust MCP calculations - don't recalculate values
- Generate all content in Dutch
- Maintain consistent narrative voice throughout
- Include all products from the quote with their subsidies