#!/bin/bash

# Run MCP Inspector for FRED Data MCP Server
# Ensure FRED_API_KEY is set in your environment

if [ -z "$FRED_API_KEY" ]; then
    echo "Error: FRED_API_KEY environment variable is not set."
    echo "Please set it using: export FRED_API_KEY='your_key_here'"
    exit 1
fi

echo "Starting MCP Inspector..."
npx @modelcontextprotocol/inspector uv run fred-data-mcp
