# Wattzo Bespaarplan Agent System

A production-ready fast-agent system that generates personalized energy savings plans (Bespaarplan) for customers, with CRM API integration and Supabase storage.

## 🚀 Features

- **Automated Bespaarplan Generation**: Complete workflow from deal ID to finished HTML report
- **Hybrid AI Model Strategy**: Uses Claude Sonnet 4 for complex tasks, Gemini 2.5 Flash for simple operations
- **API Integration**: FastAPI endpoints for CRM system integration
- **Cloud Storage**: Supabase bucket storage with CDN delivery for customer portal
- **Quality Assurance**: Built-in evaluator-optimizer pattern ensures high-quality output
- **Cost Optimized**: ~70% cheaper model usage while maintaining quality
- **MCP Architecture**: Leverages existing MCP servers for data, calculations, and templates

## 📋 Prerequisites

- Python 3.10+
- Active MCP servers (energy-data, calculation-engine, template-provider)
- Anthropic API key (for Claude Sonnet 4)
- OpenRouter API key (for Gemini 2.5 Flash)
- Supabase project with appropriate permissions

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/goxl-wtf/wattzo-bespaarplan-agent.git
   cd wattzo-bespaarplan-agent
   git checkout feature/fast-agent-bespaarplan-api
   ```

2. **Install dependencies**
   ```bash
   uv sync  # or: pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

4. **Run MCP servers** (in separate terminals)
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

## 🚦 Quick Start

### Test Generation (CLI)
```bash
# Test with a known working deal ID
python test_generation.py
```

### Run API Server
```bash
# Start the API server
python run_api.py

# API will be available at:
# - http://localhost:8000
# - Docs: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
```

### Generate via API
```bash
# Generate a bespaarplan
curl -X POST "http://localhost:8000/api/v1/generate-bespaarplan" \
  -H "Content-Type: application/json" \
  -d '{
    "deal_id": "2b3ddc42-72e8-4d92-85fb-6b1d5440f405",
    "priority": "normal",
    "notify_customer": true
  }'
```

## 📁 Project Structure

```
wattzo-bespaarplan-agent/
├── agents/               # Fast-agent implementations
│   ├── main.py          # Main orchestrator and workflow
│   └── storage/         # Supabase storage implementation
├── api/                 # FastAPI application
│   └── main.py          # API endpoints and handlers
├── config/              # Configuration files
├── tests/               # Test suites
├── mcp-servers/         # MCP server implementations
│   ├── energy-data/     # Customer and property data
│   ├── calculation-engine/ # Financial calculations
│   └── template-provider/  # HTML template generation
├── fastagent.config.yaml # Fast-agent configuration
└── .env.example         # Environment template
```

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Energy Data    │────▶│   Calculation    │────▶│    Template      │
│   MCP Server    │     │  Engine MCP      │     │  Provider MCP    │
└─────────────────┘     └──────────────────┘     └──────────────────┘
        │                        │                         │
        └────────────────────────┴─────────────────────────┘
                                 │
                         ┌───────▼────────┐
                         │  Fast-Agent    │
                         │  Orchestrator  │
                         └───────┬────────┘
                                 │
                         ┌───────▼────────┐
                         │  FastAPI       │
                         │  CRM Interface │
                         └───────┬────────┘
                                 │
                         ┌───────▼────────┐
                         │   Supabase     │
                         │  Storage/DB    │
                         └────────────────┘
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