# Bespaarplan Generator Prompts

This directory contains prompts for generating personalized energy savings plans (Bespaarplans) for WattZo customers.

## Files

- `bespaarplan_generator.md` - Main prompt for generating complete Bespaarplan HTML reports

## Important Updates

### Customer Greeting Format (Updated: December 2024)

The customer greeting must include the full last name, not just the title:

**Correct format:**
- "Beste Mevrouw Van der Starre," ✅
- "Beste Meneer Datta," ✅

**Incorrect format:**
- "Beste Mevrouw," ❌
- "Beste Meneer," ❌

### Implementation

When filling the template, set `customer_salutation` as follows:
```
customer_salutation: "Mevrouw [Last Name]" for female, "Meneer [Last Name]" for male
```

Extract the last name from the full customer name in the deal data and append it to the appropriate title.

## Usage

1. Copy the prompt from `bespaarplan_generator.md`
2. Replace `[INSERT_DEAL_ID_HERE]` with the actual deal ID
3. Follow all steps in order to generate a complete Bespaarplan
4. The HTML will be saved to the template-provider outputs directory

## Example Output

See `/mcp-servers/template-provider/outputs/bespaarplan_mevrouw_van_der_starre.html` for a correctly formatted example with "Beste Mevrouw Van der Starre," as the greeting.