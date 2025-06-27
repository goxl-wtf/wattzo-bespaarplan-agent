# Bespaarplan Generator Prompt - Hybrid Parallel/Sequential Approach

Generate a complete, personalized energy savings plan (Bespaarplan) using parallel processing where possible while maintaining narrative consistency.

## Workflow Overview

```
Step 1: Get Deal Data
           ↓
    ┌──────┴──────┐
    ↓             ↓
Step 2A        Step 2B     [PARALLEL]
Calculate      Get Template
Metrics        
    ↓             ↓
    └──────┬──────┘
           ↓
Step 3: Fill Template      [SEQUENTIAL]
           ↓
Step 4: Save via MCP
```

## Detailed Process

### Step 1: Retrieve Deal Data
Use the `get_comprehensive_deal_data` tool from the energy-data MCP server.

**Output**: Store `comprehensive_data` in memory for parallel tasks.

### Step 2: Parallel Execution
Launch two tasks simultaneously using multiple tool calls in a single message:

#### Task 2A: Calculate Metrics
- Tool: `calculate_from_deal_data` from calculation-engine MCP
- Input: `comprehensive_data` from Step 1
- Output: Store `calculated_metrics` in memory

#### Task 2B: Get Template
- Tool: `get_bespaarplan_template` from template-provider MCP
- Input: None required
- Output: Store `template_html` in memory

**Important**: Both tasks must complete before proceeding to Step 3.

### Step 3: Sequential Template Filling
With both `calculated_metrics` and `template_html` available, fill the template IN MEMORY.

**Why Sequential**: This ensures:
- Consistent narrative voice throughout
- Proper cross-references between sections
- Unified emphasis styling
- Coherent storytelling arc

**Process**:
1. Extract all required values from deal data and calculations
2. Apply Dutch formatting rules (see detailed rules below)
3. Generate ALL narratives with consistent tone:
   - Energy situation narrative
   - Personal savings story  
   - Property value narrative
   - Environmental impact story
4. Apply dynamic emphasis class based on motivation
5. Replace all placeholders in one pass
6. **Store filled HTML in memory** (do not write to file)

#### Dutch Number Formatting Rules
When filling in the template, you MUST format all numbers according to Dutch conventions:

1. **Currency amounts**: Use dots as thousand separators
   - €1090 → €1.090
   - €43550 → €43.550
   - €17498 → €17.498
   - €335000 → €335.000

2. **Energy usage numbers**: Use dots as thousand separators
   - 2005 kWh → 2.005 kWh
   - 1845 kWh → 1.845 kWh
   - 12808 km → 12.808 km
   - 30740 kg → 30.740 kg

3. **Property values**: Use dots as thousand separators
   - €335000 → €335.000
   - €378550 → €378.550

4. **Do NOT add thousand separators to**:
   - Numbers under 1000 (e.g., 825 m³, 76 m²)
   - Percentages (e.g., 17%, 165%)
   - Years (e.g., 1995, 2025)
   - Small quantities (e.g., 5 stuks, 11 jaar)

### Step 4: Save Using MCP
Pass the filled HTML string directly to `save_filled_template`.

**Input**: The complete filled HTML from Step 3
**Output**: File path from MCP tool

## Parallel Optimization Benefits

### Time Savings
- **Sequential approach**: ~3-4 seconds total
  - Deal data: 1s
  - Calculate: 1s
  - Template: 1s
  - Fill: 0.5s
  - Save: 0.5s

- **Hybrid approach**: ~2.5-3.5 seconds total
  - Deal data: 1s
  - Calculate + Template (parallel): 1s
  - Fill: 0.5s
  - Save: 0.5s

**Estimated improvement**: 25-30% faster

### Resource Utilization
- Better use of API rate limits
- Reduced total wait time
- More efficient MCP server usage

## Key Implementation Notes

### For Parallel Execution
```
When executing Step 2, use a single message with multiple tool calls:
- First tool call: calculate_from_deal_data
- Second tool call: get_bespaarplan_template
Both will execute simultaneously.
```

### Memory Management
- Keep all data in variables between steps
- Never write intermediate files
- Pass data directly between steps

### Error Handling
If either parallel task fails:
- Do not proceed to template filling
- Report which task failed
- Retry the failed task individually

## Why Not Full Parallelization?

### Template Section Dependencies
While tempting to fill sections in parallel, avoid this because:

1. **Narrative Flow**: The personal savings story should reference specific numbers that appear earlier
2. **Emphasis Consistency**: The CSS emphasis class affects multiple sections
3. **Cross-References**: Later sections reference earlier calculations
4. **Tone Unity**: A single voice should tell the complete story

### Quality Over Speed
The 0.5s saved by parallel section filling isn't worth the risk of:
- Disjointed narratives
- Inconsistent formatting
- Repeated information
- Conflicting emphasis

## Success Metrics

✅ **Performance**: 25-30% faster than sequential
✅ **Quality**: Maintains narrative consistency
✅ **Reliability**: Clear dependency management
✅ **Simplicity**: Easy to debug and maintain

## Common Pitfalls to Avoid

❌ Don't parallelize template filling into sections
❌ Don't write files manually at any step
❌ Don't proceed if any parallel task fails
❌ Don't mix customer data between parallel runs
✅ Do verify both parallel tasks complete before filling
✅ Do maintain all data in memory
✅ Do use single MCP tool for file saving