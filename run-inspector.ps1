# Run MCP Inspector for FRED Data MCP Server
# Ensure FRED_API_KEY is set in your environment

if (-not $env:FRED_API_KEY) {
    Write-Host "Error: FRED_API_KEY environment variable is not set." -ForegroundColor Red
    Write-Host "Please set it using: `$env:FRED_API_KEY = 'your_key_here'" -ForegroundColor Yellow
    exit 1
}

Write-Host "Starting MCP Inspector..." -ForegroundColor Cyan
npx @modelcontextprotocol/inspector uv run fred-data-mcp
