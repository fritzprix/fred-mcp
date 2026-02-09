#!/bin/bash

# Run MCP Inspector for FRED Data MCP Server
# Ensure FRED_API_KEY is set in your environment

echo "Starting MCP Inspector..."
npx @modelcontextprotocol/inspector uv run fred-data-mcp
