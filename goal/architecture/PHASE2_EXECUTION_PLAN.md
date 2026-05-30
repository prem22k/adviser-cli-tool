# System Design Session: Phase 2 Execution Plan for Adviser-CLI

*   **Date**: Friday, May 29, 2026
*   **Context**: Principal Architect Deep-Dive System Design Session (Claude.ai)
*   **Target Core Version**: Adviser-CLI v0.2.0-spec
*   **Status**: APPROVED / DESIGN SIGN-OFF

---

## Executive Summary

Adviser-CLI has successfully locked down its Phase 1 MVP, delivering a local-first, zero-infrastructure RAG pipeline combining paragraph-aware chunking, persistent local ChromaDB indexing, and priority-cascade LLM routing with automated circuit-breaker safety. 

To transition Adviser-CLI into a highly proactive developer workspace assistant, Phase 2 implements a two-fold architectural expansion:
1.  **Model Context Protocol (MCP) Server**: A standard-compliant, asynchronous, Stdio-based JSON-RPC context server allowing IDE agents (e.g., Cursor, Claude Code, Windsurf) to query local knowledge bases and source files securely.
2.  **Layout-Aware VisionRAG Pipeline**: A vision-language vector index utilizing ColPali to rasterize multi-column specs and financial tables into contextualized patch tensors, completely bypassing lossy text parsers.

This document outlines the first-principles engineering plans and JSON schemas for executing these core features cleanly within the existing Adviser-CLI codebase layout.

---

## 1. Model Context Protocol (MCP) Server Foundation

### 1.1 Architectural Overview
The Model Context Protocol (MCP) provides a standard JSON-RPC 2.0 communication layer between host applications (AI IDEs/Clients) and local context servers. 

To integrate natively into the `adviser/` package, we will build a standard-compliant, asynchronous server using `mcp.server` and standard Stdio transport. Because the IDE client spawns the MCP server as a subprocess, the transport utilizes standard I/O:
*   **`stdout`**: Reserved strictly for valid JSON-RPC 2.0 frames (inputs, call responses, notifications).
*   **`stderr`**: Utilized for standard system logs, warnings, and Rich progress feedback to prevent stream corruption.

```text
  [ Cursor / IDE Client ]
            │
            ├── Spawn Subprocess (python -m adviser.mcp.server)
            │
            ├── stdio (stdout) ─── [ JSON-RPC Requests ] ───► [ StdioServer ] (adviser.mcp)
            │                                                      │
            │                                                      ├── Initialize HybridRetriever
            │                                                      └── Query chroma_db (Read-Only)
            │
            └── stdio (stderr) ◄── [ Logger & Diagnostics ] ───────┘
```

### 1.2 Module Design (`adviser/mcp/server.py`)
We will scaffold the server inside a new module `adviser/mcp/server.py`. It imports the asynchronous `mcp` SDK, initializes the `HybridRetriever` on start, and registers tools for index querying and document sourcing.

```python
"""
adviser/mcp/server.py
Asynchronous Stdio-based Model Context Protocol (MCP) context server.
"""

import sys
import asyncio
import logging
from typing import Any, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from adviser.retrieval.retriever import HybridRetriever

# Standard out is reserved for JSON-RPC. Redirect loggers to stderr.
logging.basicConfig(level=logging.ERROR, stream=sys.stderr)
logger = logging.getLogger("adviser-mcp")

server = Server("adviser-mcp-server")
retriever: Optional[HybridRetriever] = None
```

### 1.3 Tool JSON Schemas
To expose context tools cleanly, the MCP server registers formal schemas describing the functions available to Cursor and Claude Code.

#### Tool 1: `query_local_vector_index`
Allows the IDE agent to execute a hybrid vector-keyword retrieval pass over the active profile's local persistent database.

```json
{
  "name": "query_local_vector_index",
  "description": "Perform a hybrid semantic and keyword search over the local document database.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "The natural language query or keyword term to search for."
      },
      "top_k": {
        "type": "integer",
        "description": "Number of high-relevance chunks to return.",
        "default": 5
      }
    },
    "required": ["query"]
  }
}
```

#### Tool 2: `fetch_document_source`
Allows the IDE agent to retrieve the entire raw source content of a specific file once a chunk match is identified, enabling broad multi-file synthesis.

```json
{
  "name": "fetch_document_source",
  "description": "Retrieve the complete un-chunked source text of an indexed file.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "source_name": {
        "type": "string",
        "description": "The exact name or path of the target document (e.g. security_policy.md)."
      }
    },
    "required": ["source_name"]
  }
}
```

### 1.4 Non-Blocking Read-Only ChromaDB Sessions
A critical failure vector in local developer tools is multi-process locking. SQLite (the storage backend for ChromaDB) will raise `database is locked` errors if the IDE client attempts to read from the vector database while a user is running a parallel terminal chat or document ingestion job.

To achieve non-blocking concurrent access, the MCP server initializes its persistent ChromaDB client using a strict read-only pipeline:
1.  **WAL Mode Enablement**: The SQLite database underlying ChromaDB is automatically configured to use Write-Ahead Logging (`journal_mode=WAL`). This allows multiple concurrent reader processes (e.g. the MCP server running in the background) to execute queries even while a writer process (e.g., `adviser ingest`) is actively updating indexes.
2.  **Shared-Cache Connection Options**: The SQLite connector is initialized with `cache=shared` and `mode=ro` (read-only) options:
    ```python
    import sqlite3
    # Enforces read-only file handlers for SQLite
    conn = sqlite3.connect("file:chroma.sqlite3?mode=ro", uri=True)
    ```
3.  **Metadata Cache Preservation**: The MCP server loads a cached mapping of indexed files (`stats.json`) at startup, completely bypassing disk access for static file lists and avoiding I/O overhead.

---

## 2. Layout-Aware VisionRAG Pipeline (ColPali Integration Blueprint)

### 2.1 Limitations of Traditional Text-Based Chunking
Standard text parsing workflows (using loaders like PDFPlumber or python-docx) extract text linearly. This completely flattens and corrupts complex document layouts:
*   **Tables**: Cell borders are stripped, causing column data to merge into unreadable strings.
*   **Multi-Column Grids**: Side-by-side blocks are parsed horizontally, combining separate paragraphs.
*   **Visual Data**: Diagrams, system architecture flowcharts, and corporate financial graphs are discarded entirely.

### 2.2 Visual Rasterization & PaliGemma Tokenizer Flow
VisionRAG addresses this by shifting document ingestion from text extraction to **direct image-based embeddings** using the **ColPali** engine (`vidore/colpali-v1.2`).

```text
 [ PDF Document ] 
        │
        ▼ (High-DPI Rasterization)
 [ Page Image Tensor ] (Pillow / pdf2image)
        │
        ▼ (PaliGemma Vision Encoder)
 [ Contextual Patch Tokens ] (32x32 Image Grid)
        │
        ▼ (Multi-Vector Matrix)
 [ ColPali Embedding ] ➔ Stored in ChromaDB metadata or custom index
```

#### Step 1: High-DPI Page Rasterization
During ingestion of complex assets (e.g. PDFs containing blueprints or tables), the text parser is bypassed. The system uses `pdf2image` to rasterize each page to a high-fidelity image tensor:
*   **DPI Target**: 150 DPI (optimal balance between structural clarity and memory conservation).
*   **Format**: RGB JPEG stored in a secure local cache directory (`~/.local/share/adviser/vision_cache/`).

#### Step 2: ColPali Multi-Vector Processing
The page image is passed through ColPali's PaliGemma-based vision-language processor:
*   The page is tokenized into a grid of 32x32 patches (1024 visual tokens).
*   The PaliGemma vision transformer projects each visual token into a high-dimensional contextualized patch embedding.
*   Unlike typical single-vector CLIP models, ColPali produces a **multi-vector matrix** representing the entire visual and semantic layout of the page.

### 2.3 Vector Dimension Alignment & Retrieval Integration
Standard vector databases (like ChromaDB) are optimized for single-vector retrieval (e.g., mapping a text query to a single 384-dimension vector). Storing and searching raw ColPali matrices natively requires MaxSim calculation over thousands of patch vectors. 

To bridge this within the Adviser-CLI layout, we define two architectural options:

#### Path A: Single-Vector Mean Pooling (Standard Index Compatibility)
For baseline deployment on resource-constrained machines (our 8GB RAM profile), the 1024 patch vectors are average-pooled along the patch dimension, resulting in a single, high-fidelity **1280-dimension vector** per page. This pooled embedding fits directly within standard ChromaDB collections, allowing standard cosine distance queries to run at maximum speed.

#### Path B: Multi-Vector MaxSim Fusion (Advanced Search)
For high-performance GPU environments, the raw visual token patch matrix is stored inside a compressed file cache, and the pooled embedding is indexed in ChromaDB. 
*   **Stage 1 Retrieval**: ChromaDB filters the top 50 candidate pages using the pooled query vector.
*   **Stage 2 Reranking**: The system loads the raw patch matrices for those 50 candidates from the local file cache and executes a lightning-fast **MaxSim** matrix dot-product pass in PyTorch to output exact visual alignment scores.

```python
# Custom MaxSim Retrieval Scoring
import torch

def maxsim_score(query_embeddings: torch.Tensor, document_embeddings: torch.Tensor) -> float:
    # Query shape: [num_query_tokens, dim]
    # Doc shape: [num_doc_patches, dim]
    # Calculate pairwise cosine similarities
    similarity_matrix = torch.matmul(query_embeddings, document_embeddings.T)
    # Return sum of maximum patch similarities
    return float(similarity_matrix.max(dim=1).values.sum().item())
```

### 2.4 Reciprocal Rank Fusion (RRF) Integration
To provide a unified search output, the scores of the visual retrieval pass (whether Path A or Path B) are merged alongside our traditional dense and sparse text indexes using Reciprocal Rank Fusion (RRF). 

This ensures that whether a user queries a text keyword ("bankruptcy risk") or describes a visual diagram ("Istio network mesh flowchart"), the Hybrid Retriever correctly returns the highest-scoring layout chunks and page images at the top of the context panel.
