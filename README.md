# FRED MCP Server

An MCP server for the Federal Reserve Economic Data (FRED) API.

## Features

- Search for economic data series.
- Retrieve data points for series.
- Explore Categories, Releases, Sources, and Tags.
- Pagination support for large datasets.
- Option to save data as JSON files.

## Configuration

Set the `FRED_API_KEY` environment variable to your FRED API key.

## Usage

Run with `uvx` (if published):
```bash
uvx fred-mcp
```

### Installation from PyPI

Once published, you can install and run directly:
```bash
pip install fred-mcp
# or
uvx fred-mcp
```


## Claude Desktop Configuration

To use this server with the Claude Desktop app, add the following to your `claude_desktop_config.json`:

### Published Package (Recommended)
If you have published the package to PyPI, you can key off the package name directly:
```json
{
  "mcpServers": {
    "fred": {
      "command": "uvx",
      "args": [
        "fred-mcp"
      ],
      "env": {
        "FRED_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### Local Development
If you are running from the source code repository:
```json
{
  "mcpServers": {
    "fred": {
      "command": "uvx",
      "args": [
        "--from",
        "/absolute/path/to/fred-mcp",
        "fred-mcp"
      ],
      "env": {
        "FRED_API_KEY": "your_api_key_here"
      }
    }
  }
}
```
Replace `/absolute/path/to/fred-mcp` with the actual path to this repository.

