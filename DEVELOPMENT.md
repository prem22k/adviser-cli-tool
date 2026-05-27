# Project Development History

### 2025-07-15 09:50
- chore: initial project layout and setup

### 2025-07-15 11:53
- chore: define core dependencies in pyproject.toml

### 2025-07-15 13:14
- feat: add .gitignore and project structure

### 2025-07-15 13:52
- docs: initial project README

### 2025-07-15 14:45
- feat: implement base settings loader with python-dotenv

### 2025-07-15 15:16
- feat: add support for local profiles and YAML config

### 2025-07-15 15:46
- feat: start hardware detection module

### 2025-07-15 16:14
- feat: implement CPU and RAM detection logic

### 2025-07-15 16:34
- feat: add GPU detection for NVIDIA cards

### 2025-07-15 17:10
- feat: define hardware performance tiers (LOW to VERY HIGH)

### 2025-07-15 17:20
- feat: implement hardware-based model size estimation

### 2025-07-15 17:23
- feat: add profile creation wizard in CLI

### 2025-07-15 18:22
- feat: implement multi-profile management

### 2025-07-15 18:32
- refactor: structure config/ directory for modular settings

### 2025-07-15 19:00
- feat: implement base document loader for .txt files

### 2025-07-15 20:03
- feat: add support for PDF extraction using pdfplumber

### 2025-07-15 20:55
- feat: add support for DOCX extraction

### 2025-07-15 21:12
- feat: implement smart_chunking with paragraph detection

### 2025-07-15 21:58
- feat: add chunk overlap logic for context preservation

### 2025-07-15 22:58
- feat: implement content-based chunk ID generation (MD5)

### 2025-08-10 09:40
- feat: add incremental indexing to skip existing chunks

### 2025-08-10 09:48
- feat: integrate local SentenceTransformers for embeddings

### 2025-08-10 14:54
- feat: implement local ChromaDB persistent storage

### 2025-08-10 16:15
- feat: add rich progress bars for ingestion process

### 2025-08-10 22:16
- refactor: optimize batch ingestion performance

### 2025-09-20 10:05
- feat: build base LLM client with multi-provider support

### 2025-09-20 12:31
- feat: implement automatic failover for API providers

### 2025-09-20 14:22
- feat: add support for Groq Llama 3/4

### 2025-09-20 16:01
- feat: add support for Google Gemini Flash

### 2025-09-20 20:03
- feat: integrate GitHub Models API support

### 2025-09-20 22:07
- feat: implement local LLM support via Ollama

### 2025-12-25 09:02
- feat: add AirLLM provider for layer-wise execution

### 2025-12-25 12:43
- feat: implement circuit breaker for failed API providers

### 2025-12-25 13:03
- feat: add conversation memory and rolling history window

### 2025-12-25 14:59
- feat: implement context injection in user messages

### 2025-12-25 15:02
- feat: build HybridRetriever with Vector + BM25 search

### 2025-12-25 15:52
- feat: implement Reciprocal Rank Fusion (RRF) for search merging

### 2025-12-25 16:25
- feat: add configurable weighting for keyword vs semantic search

### 2025-12-25 16:53
- feat: implement source tracking in retrieval hits

### 2025-12-25 17:24
- feat: add debug mode to visualize retrieved chunks and scores

### 2025-12-25 17:40
- refactor: optimize retrieval latency for large indexes

### 2025-12-25 17:52
- feat: initialize Map-Reduce document digest engine

### 2025-12-25 18:46
- feat: implement recursive summarization for massive corpora

### 2025-12-25 18:54
- feat: add chapter-based analysis logic

### 2025-12-25 18:56
- feat: implement resume-from-last-chapter for digest jobs

### 2025-12-25 19:11
- feat: add plan mode for digest cost/time estimation

### 2025-12-25 19:27
- feat: build main CLI entrypoint with Typer

### 2025-12-25 19:40
- feat: implement interactive chat loop with rich.console

### 2025-12-25 20:38
- feat: add pretty-printing for RAG responses and context

### 2025-12-25 21:04
- feat: implement 'clear' and 'exit' commands in chat

### 2025-12-25 21:24
- feat: add 'sources' command to list indexed files

### 2025-12-25 21:44
- feat: initialize MCP server for IDE integration

### 2025-12-25 22:26
- feat: implement 'retrieve' tool for MCP

### 2026-02-20 09:15
- feat: add support for context fetching in Cursor and Windsurf

### 2026-02-20 10:03
- feat: implement VisionRAG visual indexing for PDFs

### 2026-02-20 12:26
- feat: add ColPali embedding support for visual layout

### 2026-02-20 16:27
- feat: implement visual search fusion in HybridRetriever

### 2026-02-20 18:42
- refactor: modularize CLI commands into sub-tools

### 2026-02-20 20:14
- feat: add hardware-aware setup wizard

### 2026-03-10 16:05
- test: initialize test suite with pytest

### 2026-03-10 17:51
- test: add unit tests for hardware detection logic

### 2026-03-10 18:34
- test: add unit tests for document loaders

### 2026-03-10 20:27
- test: add unit tests for LLM failover and circuit breaker

### 2026-03-10 21:02
- test: add unit tests for RRF fusion scoring

### 2026-05-10 10:13
- test: add unit tests for profile management

### 2026-05-10 15:57
- test: add integration tests for MCP server tools

### 2026-05-10 16:01
- test: add unit tests for digest engine

### 2026-05-10 18:11
- refactor: apply strict type hints to core modules

### 2026-05-10 22:23
- refactor: optimize retrieval metadata handling

### 2026-05-16 10:49
- chore: add mypy and type stubs to dev dependencies

### 2026-05-16 11:02
- refactor: fix union attribute access in LLM client

### 2026-05-16 11:47
- refactor: fix dictionary type arguments for mypy --strict

### 2026-05-16 13:07
- refactor: harden MCP server type safety

### 2026-05-16 13:33
- refactor: improve vision indexing type annotations

### 2026-05-16 13:57
- test: fix regressions in RRF and Digest tests

### 2026-05-16 15:40
- docs: complete README rewrite with CLI and hardware guides

### 2026-05-16 16:52
- docs: add execution plan for project audit

### 2026-05-16 19:35
- docs: finalize VISION.md and project roadmap

### 2026-05-16 19:37
- chore: final polish and type integrity audit

### 2026-05-16 19:42
- refactor: improve provider chain validation

### 2026-05-16 20:18
- feat: add support for custom persona overrides

### 2026-05-16 22:36
- perf: optimize ChromaDB index loading speed

### 2026-05-16 22:41
- fix: resolve race condition in concurrent ingestion

### 2026-05-16 22:57
- docs: update installation guides for vision and local extras
- docs: integrate May 2026 Google Gemini 3.5 Flash and Llama 3.3 standards
