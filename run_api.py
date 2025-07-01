#!/usr/bin/env python3
"""
Startup script for the Wattzo Bespaarplan API
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

if __name__ == "__main__":
    # Check for required environment variables
    required_env = [
        "ANTHROPIC_API_KEY",
        "OPENROUTER_API_KEY", 
        "SUPABASE_URL",
        "SUPABASE_SERVICE_KEY"
    ]
    
    missing_env = [var for var in required_env if not os.getenv(var)]
    
    if missing_env:
        print("❌ Missing required environment variables:")
        for var in missing_env:
            print(f"  - {var}")
        print("\n📝 Please copy .env.example to .env and fill in the values")
        print("   cp .env.example .env")
        print("   nano .env  # or use your preferred editor")
        sys.exit(1)
    
    # Import and run the API
    import uvicorn
    
    # IMPORTANT: Use PORT env var for Render, fallback to API_PORT or 8000
    port = int(os.getenv("PORT", os.getenv("API_PORT", 8000)))
    
    # Detect if running in production (Render sets RENDER env var)
    is_production = os.getenv("RENDER") is not None
    
    print(f"🚀 Starting Wattzo Bespaarplan API on port {port}")
    if not is_production:
        print(f"📚 API Documentation: http://localhost:{port}/docs")
        print(f"📖 Alternative docs: http://localhost:{port}/redoc")
    print("\nPress CTRL+C to stop the server")
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",  # Required for Docker/container environments
        port=port,
        reload=not is_production,  # Disable reload in production
        log_level="info"
    )