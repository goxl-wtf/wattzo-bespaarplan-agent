# Bespaarplan Generator Prompt - Improved Version

Generate a complete, personalized energy savings plan (Bespaarplan) for a WattZo customer using their deal data.

## Important Workflow Notes

**Data Flow**: This process follows a pipeline pattern where data flows through memory between steps:
```
Deal Data → Calculate → Template → Fill (in memory) → Save (MCP)
                                         ↑              ↓
                                    [Keep in memory]  [File created here]
```

**Common Mistakes to Avoid**:
- ❌ Do NOT use Write tool to create the HTML file
- ❌ Do NOT save the filled template manually
- ❌ Do NOT read files back after writing them
- ✅ Keep the filled HTML content in memory between steps
- ✅ Only use the MCP save_filled_template tool for file creation

## Step-by-Step Process

### Step 1: Retrieve Deal Data
Use the `get_comprehensive_deal_data` tool from the energy-data MCP server with the provided deal ID.

**Store in memory**: Keep the comprehensive_data response for use in subsequent steps.

### Step 2: Calculate All Metrics
Pass the comprehensive data to `calculate_from_deal_data` from the calculation-engine MCP.

**Store in memory**: Keep the calculated_metrics response for template filling.

### Step 3: Get the HTML Template
Retrieve the Bespaarplan template using `get_bespaarplan_template` from the template-provider MCP.

**Store in memory**: Keep the template HTML for filling in the next step.

### Step 4: Fill the Template IN MEMORY
Replace all placeholders in the template with actual values from the deal data and calculations.

**Important**: This step happens entirely in memory. Do not save to file yet!

**Key tasks**:
1. Replace all `{{ variable }}` placeholders with calculated values
2. Generate personalized narratives based on customer profile
3. Apply Dutch number formatting
4. Create dynamic emphasis classes
5. **Store the filled HTML string in a variable** - this will be passed to Step 5

### Step 5: Save Using MCP Tool
Pass the filled HTML content (from Step 4) directly to the `save_filled_template` tool.

**Input**: The filled HTML string from Step 4 (not a file path!)
**Output**: The MCP tool will create the file and return the path

### Step 6: Confirm Success
Report the saved file location to the user.

## Template Filling Guidelines

### Dutch Number Formatting
- Thousands: Use periods (1.200 not 1,200)
- Currency: No decimals for whole amounts (€3.445 not €3.445,00)
- Percentages: Include % symbol (15% not 0.15)

### Dynamic Emphasis Classes
Based on `customer_motivation`:
- `cost_savings` → `emphasis-savings`
- `comfort` → `emphasis-comfort`
- `green` → `emphasis-green`

### Personalized Narratives

#### Energy Situation Narrative
Craft based on current consumption patterns:
- High gas usage (>1500m³): Focus on heating inefficiency
- Low gas usage (<1000m³): Compliment current efficiency
- Solar potential: Emphasize self-sufficiency opportunity

#### Personal Savings Story
Match customer personality and motivation:
- **Analytical + Cost Savings**: Use concrete numbers and ROI
- **Big Picture + Green**: Focus on environmental impact
- **Practical + Comfort**: Emphasize daily life improvements

#### Property Value Narrative
Include neighborhood context:
- Reference local property market trends
- Compare to similar homes in the area
- Mention appeal to future buyers

## Data Mapping Reference

### Hero Section
- `annual_savings`: metrics.financial.annual_savings
- `co2_reduction_pct`: metrics.environmental.co2_reduction_percentage
- `property_value_increase`: metrics.property.value_increase

### Customer Information
- `customer_name`: deal_data.customer.first_name + last_name
- `customer_salutation`: Based on gender (Dhr./Mevr.)
- `advisor_name`: deal_data.advisor.name

### Energy Metrics
- Current usage from deal_data.energy_profile
- After usage from metrics.energy
- Costs from metrics.financial

### Financial Calculations
- Investment details from metrics.financial
- Loan terms from deal_data.quote.financing
- ROI and payback from metrics.financial

### Environmental Impact
- CO2 data from metrics.environmental
- Equivalents (trees, car km, flights) from metrics

## Success Criteria
- ✅ All placeholders replaced with actual values
- ✅ Personalized narratives match customer profile
- ✅ Dutch formatting applied correctly
- ✅ File saved via MCP tool only
- ✅ Single file output with complete HTML