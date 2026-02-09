import os
import json
import pandas as pd
from typing import Optional, Union, Any, Dict, List
from fredapi import Fred
from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, TextContent

# Initialize FastMCP
mcp = FastMCP("fred-mcp-server")

def get_fred() -> Fred:
    """Helper to get authenticated Fred instance."""
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        raise ValueError("FRED_API_KEY environment variable not set. Please set it to use this server.")
    return Fred(api_key=api_key)

def df_to_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Helper to convert DataFrame to JSON-serializable records."""
    if df is None or df.empty:
        return []
    
    # Prepare for JSON export
    temp_df = df.copy()
    if isinstance(temp_df, pd.Series):
        temp_df = temp_df.to_frame(name="value")
    
    # Handle dates if they are in the index
    if isinstance(temp_df.index, pd.DatetimeIndex):
        temp_df.index.name = temp_df.index.name or "date"
        temp_df.reset_index(inplace=True)
        # Convert timestamp to string for JSON serialization
        for col in temp_df.select_dtypes(include=['datetime64']).columns:
            temp_df[col] = temp_df[col].dt.strftime('%Y-%m-%d')
    
    # Convert other objects that might not be serializable
    # (e.g., float('nan') which common JSON encoders handle, but we can be explicit)
    return temp_df.to_dict(orient='records')

def format_series_search_results(df: pd.DataFrame, limit: int, offset: int) -> str:
    """Format search results as Markdown table."""
    if df is None or df.empty:
        return "No series found."
    
    # Apply pagination
    total_count = len(df)
    df_page = df.iloc[offset : offset + limit]
    
    markdown = f"**Found {total_count} series (showing {len(df_page)}):**\n\n"
    markdown += df_page.to_markdown(index=False)
    return markdown

def save_to_file(data: pd.DataFrame, file_path: str, series_id: Optional[str] = None) -> str:
    """Helper to save DataFrame to JSON and return a confirmation message."""
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    
    records = df_to_records(data)
    
    with open(file_path, 'w') as f:
        json.dump(records, f, indent=2)
        
    id_str = f" for `{series_id}`" if series_id else ""
    return f"✅ Data{id_str} saved to `{file_path}` ({len(records)} records)\n"

@mcp.tool()
def search_series(query: str, limit: int = 10, offset: int = 0, file_path: Optional[str] = None) -> CallToolResult:
    """
    Search for economic data series by text query.
    
    Args:
        query: The search text (e.g., "gdp", "unemployment").
        limit: Maximum number of results to return in preview (default: 10).
        offset: Number of results to skip (default: 0).
        file_path: Optional absolute path to save the full search results as JSON.
    """
    try:
        fred = get_fred()
        df = fred.search(query)
        
        records = df_to_records(df)
        
        if file_path:
            msg = save_to_file(df, file_path, query)
            return CallToolResult(
                content=[TextContent(type="text", text=msg)],
                structuredContent={"message": msg, "file_path": file_path, "count": len(records)}
            )
            
        markdown = format_series_search_results(df, limit, offset)
        return CallToolResult(
            content=[TextContent(type="text", text=markdown)],
            structuredContent={"results": records}
        )
    except Exception as e:
        error_msg = f"Error searching series: {str(e)}"
        return CallToolResult(
            content=[TextContent(type="text", text=error_msg)],
            isError=True,
            structuredContent={"error": str(e)}
        )

@mcp.tool()
def get_series_info(series_id: str) -> CallToolResult:
    """
    Get metadata for a specific data series.
    
    Args:
        series_id: The ID of the series (e.g., "GDP", "UNRATE").
    """
    try:
        fred = get_fred()
        info = fred.get_series_info(series_id)
        if info is None or info.empty:
            msg = f"No info found for series {series_id}"
            return CallToolResult(
                content=[TextContent(type="text", text=msg)],
                structuredContent={"error": msg}
            )
        
        records = df_to_records(info)
        markdown = f"## Series Metadata: {series_id}\n\n{info.to_markdown()}"
        return CallToolResult(
            content=[TextContent(type="text", text=markdown)],
            structuredContent=records[0] if records else {}
        )
    except Exception as e:
        error_msg = f"Error getting series info: {str(e)}"
        return CallToolResult(
            content=[TextContent(type="text", text=error_msg)],
            isError=True,
            structuredContent={"error": str(e)}
        )

@mcp.tool()
def get_series_data(series_id: str, limit: int = 1000, offset: int = 0, file_path: Optional[str] = None) -> CallToolResult:
    """
    Get data points for a specific series.
    
    Args:
        series_id: The ID of the series (e.g., "GDP").
        limit: Max data points to return in the markdown preview (default: 1000).
        offset: Data points to skip (default: 0).
        file_path: Optional absolute path to save the full data as JSON. 
                   If provided, the full dataset (ignoring limit/offset) is saved and response is minimized.
    """
    try:
        fred = get_fred()
        # Get series data
        data = fred.get_series(series_id)
        
        if data is None or data.empty:
            msg = f"No data found for series {series_id}"
            return CallToolResult(
                content=[TextContent(type="text", text=msg)],
                structuredContent={"error": msg}
            )
            
        records = df_to_records(data)

        # Handle file download if requested
        if file_path:
            msg = save_to_file(data, file_path, series_id)
            return CallToolResult(
                content=[TextContent(type="text", text=msg)],
                structuredContent={"message": msg, "file_path": file_path, "count": len(records)}
            )

        # Prepare markdown preview
        # Limit/Offset applies to the preview
        total_points = len(data)
        data_page = data.iloc[offset : offset + limit]
        
        # Try to get info for title
        try:
            info = fred.get_series_info(series_id)
            title = info.get('title', series_id)
            units = info.get('units', '')
            header = f"## {title} ({units})"
        except:
            header = f"## {series_id}"

        result_msg = f"{header}\n"
        result_msg += f"**Showing {len(data_page)} of {total_points} data points**\n\n"
        result_msg += data_page.to_markdown()
        
        return CallToolResult(
            content=[TextContent(type="text", text=result_msg)],
            structuredContent={"data": records[offset : offset + limit]}
        )

    except Exception as e:
        error_msg = f"Error getting series data: {str(e)}"
        return CallToolResult(
            content=[TextContent(type="text", text=error_msg)],
            isError=True,
            structuredContent={"error": str(e)}
        )

# --- Category Tools ---

@mcp.tool()
def get_category_details(category_id: int) -> CallToolResult:
    """
    Get details for a specific category (if supported).
    
    Args:
        category_id: The ID of the category (e.g., 125).
    """
    try:
        msg = f"To explore category {category_id}, please use `get_category_series` or `get_category_children`."
        return CallToolResult(
            content=[TextContent(type="text", text=msg)],
            structuredContent={"message": msg, "category_id": category_id, "status": "not_implemented"}
        )
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")],
            isError=True,
            structuredContent={"error": str(e)}
        )

@mcp.tool()
def get_category_children(category_id: int) -> CallToolResult:
    """
    Get child categories for a specific category.
    
    Args:
        category_id: The parent category ID.
    """
    try:
        msg = "Tool `get_category_children` is not currently available via this wrapper. Please use `get_category_series`."
        return CallToolResult(
            content=[TextContent(type="text", text=msg)],
            structuredContent={"message": msg, "category_id": category_id, "status": "not_implemented"}
        )
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")],
            isError=True,
            structuredContent={"error": str(e)}
        )


# Re-implementing correctly based on `fredapi` capabilities (it's often just a thin wrapper).
# If `fredapi` doesn't support it, we might need requests. 
# But let's assume `fredapi` is sufficient for SERIES operations mainly. 
# The user asked for "more apis" including Categories.
# If `fredapi` is missing them, I might need to make direct HTTP requests using the key?
# `fredapi` source usually has `_fetch_data` or similar.
# Let's stick to safe bets: `search_by_category` -> `get_category_series`.

@mcp.tool()
def get_category_series(category_id: int, limit: int = 1000, offset: int = 0, file_path: Optional[str] = None) -> CallToolResult:
    """
    Get series in a specific category.
    
    Args:
        category_id: The category ID.
        limit: Max results in preview.
        offset: Offset for preview.
        file_path: Optional absolute path to save the full list as JSON.
    """
    try:
        fred = get_fred()
        df = fred.search_by_category(category_id, limit=limit, order_by='popularity', sort_order='desc')
        
        records = df_to_records(df)

        if file_path:
            msg = save_to_file(df, file_path, f"category_{category_id}")
            return CallToolResult(
                content=[TextContent(type="text", text=msg)],
                structuredContent={"message": msg, "file_path": file_path, "count": len(records)}
            )
            
        markdown = format_series_search_results(df, limit, offset)
        return CallToolResult(
            content=[TextContent(type="text", text=markdown)],
            structuredContent={"results": records}
        )
    except Exception as e:
        error_msg = f"Error getting category series: {str(e)}"
        return CallToolResult(
            content=[TextContent(type="text", text=error_msg)],
            isError=True,
            structuredContent={"error": str(e)}
        )

@mcp.tool()
def get_releases(limit: int = 1000, offset: int = 0, file_path: Optional[str] = None) -> CallToolResult:
    """
    Get all releases of economic data.
    
    Args:
        limit: Max results in preview.
        offset: Offset for preview.
        file_path: Optional absolute path to save the full list as JSON.
    """
    try:
        fred = get_fred()
        df = fred.get_releases(limit=limit, offset=offset)
        
        records = df_to_records(df)

        if file_path:
            msg = save_to_file(df, file_path, "releases")
            return CallToolResult(
                content=[TextContent(type="text", text=msg)],
                structuredContent={"message": msg, "file_path": file_path, "count": len(records)}
            )
            
        markdown = format_series_search_results(df, limit, offset)
        return CallToolResult(
            content=[TextContent(type="text", text=markdown)],
            structuredContent={"results": records}
        )
    except Exception as e:
        error_msg = f"Error getting releases: {str(e)}"
        return CallToolResult(
            content=[TextContent(type="text", text=error_msg)],
            isError=True,
            structuredContent={"error": str(e)}
        )

@mcp.tool()
def get_release_series(release_id: int, limit: int = 1000, offset: int = 0, file_path: Optional[str] = None) -> CallToolResult:
    """
    Get series in a specific release.
    
    Args:
        release_id: The release ID.
        limit: Max results in preview.
        offset: Offset for preview.
        file_path: Optional absolute path to save the full list as JSON.
    """
    try:
        fred = get_fred()
        df = fred.get_release_series(release_id, limit=limit, offset=offset)
        
        records = df_to_records(df)

        if file_path:
            msg = save_to_file(df, file_path, f"release_{release_id}")
            return CallToolResult(
                content=[TextContent(type="text", text=msg)],
                structuredContent={"message": msg, "file_path": file_path, "count": len(records)}
            )
            
        markdown = format_series_search_results(df, limit, offset)
        return CallToolResult(
            content=[TextContent(type="text", text=markdown)],
            structuredContent={"results": records}
        )
    except Exception as e:
        error_msg = f"Error getting release series: {str(e)}"
        return CallToolResult(
            content=[TextContent(type="text", text=error_msg)],
            isError=True,
            structuredContent={"error": str(e)}
        )

# Sources and Tags
@mcp.tool()
def get_sources(file_path: Optional[str] = None) -> CallToolResult:
    """
    Get all sources of economic data.
    
    Args:
        file_path: Optional absolute path to save the sources list as JSON.
    """
    try:
        fred = get_fred()
        df = fred.get_sources()
        
        records = df_to_records(df)

        if file_path:
            msg = save_to_file(df, file_path, "sources")
            return CallToolResult(
                content=[TextContent(type="text", text=msg)],
                structuredContent={"message": msg, "file_path": file_path, "count": len(records)}
            )
            
        markdown = f"**Found {len(df)} sources:**\n\n"
        markdown += df.to_markdown(index=False)
        return CallToolResult(
            content=[TextContent(type="text", text=markdown)],
            structuredContent={"results": records}
        )
    except Exception as e:
        error_msg = f"Error getting sources: {str(e)}"
        return CallToolResult(
            content=[TextContent(type="text", text=error_msg)],
            isError=True,
            structuredContent={"error": str(e)}
        )

@mcp.tool()
def get_source(source_id: int) -> CallToolResult:
    """Get details for a specific source."""
    try:
        fred = get_fred()
        info = fred.get_source(source_id)
        if isinstance(info, list) and len(info) > 0:
            info = info[0] # usage pattern might vary
        # `get_source` in fredapi might return dict or list
        msg = f"## Source {source_id}\n\n{info}"
        return CallToolResult(
            content=[TextContent(type="text", text=msg)],
            structuredContent=info if isinstance(info, dict) else {"details": str(info)}
        )
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error getting source: {str(e)}")],
            isError=True,
            structuredContent={"error": str(e)}
        )

# Tags
@mcp.tool()
def search_related_tags(tag_names: str, limit: int = 1000, offset: int = 0) -> CallToolResult:
    """
    Get related tags for a set of tags.
    
    Args:
        tag_names: Semicolon separated list of tag names.
        limit: Max results.
        offset: Offset.
    """
    try:
        msg = "Tool `search_related_tags` is not fully implemented in this version."
        return CallToolResult(
            content=[TextContent(type="text", text=msg)],
            structuredContent={"message": msg, "tag_names": tag_names, "status": "not_implemented"}
        )
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")],
            isError=True,
            structuredContent={"error": str(e)}
        )

def main():
    mcp.run()

if __name__ == "__main__":
    main()
