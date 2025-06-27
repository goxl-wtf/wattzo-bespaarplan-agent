#!/bin/bash
# Script to start all MCP servers for development

echo "🚀 Starting MCP Servers..."

# Function to cleanup on exit
cleanup() {
    echo -e "\n🛑 Stopping all MCP servers..."
    kill $(jobs -p) 2>/dev/null
    exit 0
}

# Set trap to cleanup on CTRL+C
trap cleanup INT

# Start energy-data server
echo "📊 Starting energy-data server..."
cd mcp-servers/energy-data && python server.py &
ENERGY_PID=$!
cd ../..

# Start calculation-engine server
echo "🧮 Starting calculation-engine server..."
cd mcp-servers/calculation-engine && python server.py &
CALC_PID=$!
cd ../..

# Start template-provider server
echo "📝 Starting template-provider server..."
cd mcp-servers/template-provider && python server.py &
TEMPLATE_PID=$!
cd ../..

echo -e "\n✅ All MCP servers started!"
echo "   - Energy Data: PID $ENERGY_PID"
echo "   - Calculation Engine: PID $CALC_PID"
echo "   - Template Provider: PID $TEMPLATE_PID"
echo -e "\nPress CTRL+C to stop all servers"

# Wait for all background processes
wait