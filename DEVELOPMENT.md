# Project Development History

### 2026-05-26 16:55
- feat: scaffold adviser cli foundation

### 2026-05-26 16:58
- feat: implement ingestion pipeline

### 2026-05-26 17:02
- feat: add retrieval and llm orchestration

### 2026-05-26 17:08
- feat: wire digest workflows and cli shell

### 2026-05-26 17:16
- fix: align provider validation and failover behavior

### 2026-05-26 17:21
- fix: tighten digest resume and cli spec details

### 2026-05-26 17:25
- fix: finalize strict digest workflow compliance

### 2026-05-26 17:33
- refactor: align day-one text loader with ingestion spec

### 2026-05-26 17:38
- refactor: match day-one chroma ingestion workflow

### 2026-05-27 02:10
- chore: clean re-initialization of project root

### 2026-05-28 00:09
- chore: ignore virtual environment, local egg-info, and test databases

### 2026-05-28 00:21
- feat: integrate hardware auto-detection module and recommended ollama models

### 2026-05-28 00:29
- feat: integrate AirLLM local memory-efficient inference provider

### 2026-05-28 00:30
- chore: ignore agent and codex hidden cache directories

### 2026-05-28 00:34
- feat: prompt to install Ollama if missing and recommend local LLM pull commands based on hardware tier

### 2026-05-28 00:38
- chore: update default Gemini model to flagship gemini-3.5-flash for May 2026 standard

### 2026-05-28 00:45
- feat: allow users to pick specific Gemini and Groq models in setup wizard and save to profile

### 2026-05-28 00:47
- docs: add VISION.md, DEVELOPMENT.md, and CONTRIBUTING.md based on current project directory

### 2026-05-28 01:20
- feat: add stream-based Kaggle Enron email dataset extraction and filtering script in `scratch/process_enron.py`
- feat: implement high-precision word boundary regular expression matching for Enron corporate keyword retrieval

### 2026-05-28 01:30
- refactor: polish ingestion terminal UI, suppressing verbose transformers weights loading and HuggingFace hub unauthenticated warnings
- refactor: consolidate duplicate ingestion summary panels into a single, elegant Centered Statistics Panel
- UI: streamline progress bar descriptions ('File Scanning', 'Chunking', 'Embedding') and enhance with sleek, smooth, and consistent color styling

### 2026-05-28 01:35
- Refine and polish ingestion UI, suppressing progress bar/auth warnings and consolidating summary panels

### 2026-05-28 14:07
- feat: implement premium zero-infrastructure `install.sh` bash script to automate environment provisioning and setup
- docs: document 1-Command Express Installer in root `README.md`

### 2026-05-28 14:09
- feat: implement native Windows PowerShell installer `install.ps1` for 100% cross-platform 1-click installations
- docs: add Windows PowerShell installation instructions to `README.md`

### 2026-05-28 14:18
- feat: scaffold high-quality mock test data under `./demo_corpus/` containing three markdown developer files (`architecture_spec.md`, `security_policy.md`, `api_contract.md`)
- refactor: rename and standardize screenshot assets to (`init.png`, `ingest.png`, `chat_1.png`, `chat_2.png`) inside `./assets/`
- docs: map standardized screenshots in `README.md` visual walkthrough and add explicit Kaggle Enron email data provenance links
- release: lock down stable baseline milestone with git tag `v0.1.0-mvp`

### 2026-05-30 12:40
- docs: conduct premium systems architecture design session and compile `goal/architecture/PHASE2_EXECUTION_PLAN.md` mapping out async Stdio JSON-RPC MCP Server interfaces and layout-aware VisionRAG ColPali embedding pipelines

### 2026-05-30 15:25
- refactor: design and implement hyper-smooth Claude-Style token streaming print loops with dedicated Live manager, Group layout containers, and latency dots spinner animation
- feat: upgrade CLI prompt loop with advanced prompt_toolkit stylesheets, royal blue / cyan colored token pairings, command history auto-suggestions, and visually isolated inline spacer layouts
- release: register and publish adviser-cli@0.2.0 package to the public NPM registry, enabling global zero-dependency node installations

### 2026-05-30 15:30
- test: complete the comprehensive Phase 2 systems test suite (`scratch/test_mcp_server.py`) validating core protocol and concurrency safety layers
- test: achieve full verification of key architectural validation criteria:
  *   **Stdio-Transport Conformance**: Asynchronous stdio-based JSON-RPC v2.0 message parsing, schema validation for `query_local_vector_index` and `fetch_document_source`, and client connection lifecycle management.
  *   **SQLite WAL Concurrency**: Write-Ahead Logging (WAL) database transactions successfully verified under concurrent multi-process environments using read-only shared cache connections (`mode=ro`), completely eliminating locking exceptions.
  *   **VisionRAG Lazy-Loading Fallback**: Lazy-loading module fallback engine mechanics for visual layout-aware embeddings via ColPali (`vidore/colpali-v1.2`), verifying torch dependency guards, signature conformance, and high-fidelity runtime warning pipelines.

### 2026-05-31 20:30
- feat: expand cloud LLM API providers adding Anthropic Claude Messages SDK, OpenAI, DeepSeek V3.2, Mistral AI, OpenRouter, Together AI, and Fireworks AI, integrating them into the unified circuit-broken router.
- feat: refactor setup wizard `adviser init` to employ premium prompt-toolkit interactive TUI checkbox and radio select dialog interfaces.
- fix: implement dynamic document directory bootstrapping and sample corpus auto-seeding inside `adviser ingest` to prevent unhandled FileNotFoundError tracebacks.
- docs: capture and replace visual walkthrough screenshots with high-fidelity, authentic terminal run captures (`assets/init.png`, `assets/ingest.png`, `assets/chat_1.png`, `assets/mcp_synergy.png`).
- release: bump version to `0.3.0` across all metadata files (`package.json`, `pyproject.toml`, and `adviser/__init__.py`) and register git release tag `v0.3.0`.
