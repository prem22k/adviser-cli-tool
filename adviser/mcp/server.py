"""
adviser/mcp/server.py
Asynchronous Stdio-based Model Context Protocol (MCP) context server for IDE integration.
"""

import os
import sys
import asyncio
import logging
import sqlite3
from pathlib import Path
from typing import Any, Optional

from rich.console import Console
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from adviser.config import settings
from adviser.retrieval.retriever import HybridRetriever

# Standard out is reserved for JSON-RPC. Redirect standard logging and Rich console to stderr.
logging.basicConfig(level=logging.ERROR, stream=sys.stderr)
logger = logging.getLogger("adviser-mcp")
console = Console(stderr=True)

server = Server("adviser-mcp-server")
retriever: Optional[HybridRetriever] = None


@server.list_tools()  # type: ignore
async def list_tools() -> list[types.Tool]:
    """Expose formal RAG context retrieval and document sourcing tools."""
    return [
        types.Tool(
            name="query_local_vector_index",
            description="Perform a hybrid semantic and keyword search over the local document database.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to match against the corpus.",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of high-relevance chunks to return.",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="fetch_document_source",
            description="Retrieve the complete un-chunked source text of an indexed file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_name": {
                        "type": "string",
                        "description": "The exact name or path of the target document (e.g. security_policy.md).",
                    }
                },
                "required": ["source_name"],
            },
        ),
    ]


@server.call_tool()  # type: ignore
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    """Handle MCP tool execution calls from agentic IDE clients."""
    if not retriever:
        return [types.TextContent(type="text", text="Error: Retriever not initialized.")]

    try:
        if name == "query_local_vector_index":
            query = arguments["query"]
            top_k = arguments.get("top_k", 5)
            # Perform RRF hybrid search
            hits = retriever.search(query, top_k=top_k)
            context = retriever.format_context(hits)
            return [types.TextContent(type="text", text=context)]

        elif name == "fetch_document_source":
            source_name = arguments["source_name"]
            
            # Resolve target path under the active profile's DATA_PATH
            source_path = settings.DATA_PATH / source_name
            if not source_path.exists():
                # Search recursively inside DATA_PATH
                for path in settings.DATA_PATH.rglob("*"):
                    if path.is_file() and path.name == source_name:
                        source_path = path
                        break

            if source_path.exists() and source_path.is_file():
                text = source_path.read_text(encoding="utf-8", errors="replace")
                return [types.TextContent(type="text", text=text)]
            else:
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: Source document '{source_name}' not found under data path: {settings.DATA_PATH}"
                    )
                ]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as exc:
        return [
            types.TextContent(
                type="text",
                text=f"Error executing {name}: {str(exc)}"
            )
        ]


async def _main() -> None:
    """Asynchronous entrypoint running stdio transport loop."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def start_server(profile_name: Optional[str] = None) -> None:
    """
    Synchronously initialize the retriever in read-only mode and launch the async loop.
    """
    global retriever
    
    # 1. Enforce SQLite Write-Ahead Logging (WAL) and Shared-Cache read-only mode options
    db_file = Path(settings.DB_PATH) / "chroma.sqlite3"
    if db_file.exists():
        try:
            # Connect in read-write mode briefly to enable WAL mode persistently
            conn = sqlite3.connect(str(db_file))
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.close()
        except Exception as exc:
            logger.warning(f"Failed to enable SQLite WAL journal mode: {exc}")

    # 2. Load the Hybrid Retriever client
    try:
        retriever = HybridRetriever()
        retriever.load()
    except Exception as exc:
        console.print(f"[red]Error loading database for profile '{profile_name}':[/red] {exc}")
        sys.exit(1)

    # 3. Launch async loop
    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        pass
