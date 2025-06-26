# Wattzo Bespaarplan Agent

AI-powered energy savings plan (Bespaarplan) generator using MCP servers for Dutch homeowners. Creates personalized sustainability reports with financial calculations and environmental impact.

## Overview

This project consists of three MCP (Model Context Protocol) servers that work together to generate comprehensive energy savings plans:

- **Energy Data Server**: Provides customer profiles, property information, and quote details
- **Calculation Engine**: Performs financial calculations, energy savings projections, and environmental impact assessments
- **Template Provider**: Serves HTML templates and enables dynamic content generation

## Features

- 🏠 Personalized energy savings calculations based on property characteristics
- 💰 Detailed financial projections including ROI, payback period, and subsidy calculations
- 🌱 Environmental impact assessment with CO2 reduction equivalents
- 📊 Energy label improvement calculations with realistic constraints
- 📄 Magazine-style HTML reports with dynamic content
- 🎯 Customer profile-based personalization

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Energy Data    │────▶│   Calculation    │────▶│    Template      │
│     Server      │     │     Engine       │     │    Provider      │
└─────────────────┘     └──────────────────┘     └──────────────────┘
        │                        │                         │
        └────────────────────────┴─────────────────────────┘
                                 │
                         ┌───────▼────────┐
                         │  Claude Agent  │
                         │  (Orchestrator)│
                         └────────────────┘
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/wattzo-bespaarplan-agent.git
cd wattzo-bespaarplan-agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.local.example .env.local
# Edit .env.local with your configuration
```

## Usage

### Running the MCP Servers

Each server can be run independently:

```bash
# Energy Data Server
cd mcp-servers/energy-data
python server.py

# Calculation Engine
cd mcp-servers/calculation-engine
python server.py

# Template Provider
cd mcp-servers/template-provider
python server.py
```

### Generating a Bespaarplan

Use Claude with the provided prompt:

```bash
claude chat --mcp energy-data,calculation-engine,template-provider < .claude/prompts/generate-bespaarplan.md
```

## Project Structure

```
wattzo-bespaarplan-agent/
├── .claude/
│   ├── prompts/           # Agent prompts
│   └── CLAUDE.md          # Project-specific Claude instructions
├── mcp-servers/
│   ├── energy-data/       # Customer and property data server
│   ├── calculation-engine/# Financial and energy calculations
│   └── template-provider/ # HTML template generation
├── README.md
├── requirements.txt
└── .env.local.example
```

## Key Components

### Energy Label Calculation

The system uses a sophisticated multi-factor scoring system for realistic energy label improvements:
- 40% Energy impact (actual consumption reduction)
- 30% Building transformation (insulation, systems)
- 30% Future-readiness (solar, heat pumps)

### Financial Calculations

- Net Present Value (NPV) with inflation adjustment
- Dynamic payback period calculations
- Subsidy integration (ISDE)
- Property value increase projections

### Personalization Engine

- Customer profile analysis (motivation, personality, life situation)
- Dynamic narrative generation
- Context-aware messaging
- Emphasis adaptation based on priorities

## Development

### Adding New Features

1. **New Calculations**: Add to `calculation-engine/server.py`
2. **New Data Fields**: Update `energy-data/server.py`
3. **Template Changes**: Modify `template-provider/templates/`
4. **Personalization**: Enhance `.claude/prompts/generate-bespaarplan.md`

### Testing

```bash
# Run with test deal ID
python test_calculation.py --deal-id 60f6f68f-a8e6-47d7-b8a8-310d3a3cb057
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is proprietary software owned by Wattzo.

## Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp) framework
- Uses Claude AI for intelligent orchestration
- Energy calculations based on Dutch CBS standards