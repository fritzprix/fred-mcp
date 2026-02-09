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
uvx fred-data-mcp
```

### Installation from PyPI

Once published, you can install and run directly:
```bash
pip install fred-data-mcp
# or
uvx fred-data-mcp
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
        "fred-data-mcp"
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
        "fred-data-mcp"
      ],
      "env": {
        "FRED_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## Development

### Running the MCP Inspector
To test the server locally with the MCP Inspector:

**Windows (PowerShell):**
```powershell
$env:FRED_API_KEY = "your_api_key_here"
.\run-inspector.ps1
```

**Bash:**
```bash
export FRED_API_KEY="your_api_key_here"
./run-inspector.sh
```

Alternatively, run the command directly:
```bash
npx @modelcontextprotocol/inspector uv run fred-data-mcp

## Publication

### Publishing to PyPI
A helper script `publish.ps1` is provided to automate version bumping and publication.

**Requirements:**
- `uv` installed.
- PyPI credentials configured (e.g., via `~/.pypirc` or environment variables `TWINE_USERNAME` and `TWINE_PASSWORD`).


**Usage (Windows PowerShell):**
```powershell
# Bump patch version and publish
.\publish.ps1 patch
```

**Usage (Bash):**
```bash
# Bump patch version and publish
./publish.sh patch
```

To test the build process without uploading, use the `-DryRun` (PS) or `--dry-run` (Bash) flag:
```powershell
.\publish.ps1 patch -DryRun
# or
./publish.sh patch --dry-run
```

