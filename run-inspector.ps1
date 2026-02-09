# Run MCP Inspector for FRED Data MCP Server
# Ensure FRED_API_KEY is set in your environment


Write-Host "Starting MCP Inspector..." -ForegroundColor Cyan
npx @modelcontextprotocol/inspector uv run fred-data-mcp
