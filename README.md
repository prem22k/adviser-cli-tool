# Adviser-CLI

> **A terminal-native, zero-infrastructure local RAG pipeline and intelligence hub for privacy-first developers.**

Adviser-CLI is a terminal-native, zero-infrastructure Retrieval-Augmented Generation (RAG) assistant designed to search, query, and summarize large collections of private text and markdown documents. By combining local dense-sparse retrieval with priority-cascade LLM routing, active hardware auto-detection, and circuit-breaker safety, Adviser brings private, fast, and resilient intelligence straight to your command line.

*   🔒 **100% Local Privacy**: Your proprietary source code, system documentation, and secure corporate records never leave your local hardware.
*   ⚡ **Zero DevOps Overhead**: Go from `pip install` to interactive context chatting in under 60 seconds with no complex database hosting or server management.
*   🤖 **Agentic IDE Integration via MCP**: Integrates seamlessly with the Model Context Protocol (MCP) to supply high-fidelity local context directly to advanced IDE agents like Cursor, Claude Code, and Windsurf.

---

## 🎯 The Problem & Data-Backed Validation

Modern software engineering teams face two massive, compounding productivity bottlenecks when attempting to leverage standard browser-based generative AI systems:

### 1. The 40% Focus Loss Drain
Context-switching is the silent killer of engineering productivity. Copying and pasting code blocks or documentation out of the terminal and IDE into browser-based AI portals forces developers out of their primary environments, causing a **40% focus loss drain**. Industry telemetry shows that once interrupted by a context switch, a developer requires **20 to 30 minutes** of cognitive recalibration to recover deep flow states. By embedding RAG search directly into the terminal, Adviser-CLI eliminates this friction completely.

### 2. The Enterprise Security Risk
Uploading proprietary source code, internal APIs, or confidential data structures to cloud AI wrappers constitutes an existential security risk. Independent studies show that **11% to 12% of data pasted into public LLM interfaces contains highly sensitive information**—including intellectual property, hardcoded API keys, private credentials, and financial metrics. This security threat has forced major global corporations to outright ban external AI wrappers. Adviser-CLI addresses this vulnerability by keeping all semantic vectors, metadata, and database execution strictly isolated on local hardware.

---

## 💡 The Solution (Adviser-CLI Approach)

Adviser-CLI solves these issues by acting as a lightweight, secure local brain. It scans your document directories concurrently, builds a paragraph-aware smart semantic chunk index, and runs all vector calculations on your local machine. You retain absolute control over where your data flows: run fully private local models offline (via Ollama or sequential layer-wise AirLLM execution), or configure highly secure, circuit-broken API failover paths.

---

## 🏗️ Production-Grade Architecture

Adviser-CLI is engineered for performance, resilience, and maximum resource utilization. The application follows a strict modular, layer-by-layer layout:

```text
adviser-cli-tool/
├── assets/                     # Live MVP Proof Screenshots
├── pyproject.toml              # Packaging and dependency declarations
├── README.md                   # Complete architectural guide
└── adviser/
    ├── __init__.py
    ├── cli.py                  # CLI commands, setup wizards, and loops
    ├── config/
    │   ├── settings.py         # Source-of-truth configuration properties
    │   ├── profiles.py         # Multi-profile configurations management
    │   └── snapshots.py        # Compressed tarball backup utilities
    ├── digest/
    │   ├── engine.py           # Map-reduce digest summarizer
    │   └── planner.py          # Digest token & ETA plan estimator
    ├── ingestion/
    │   ├── loaders.py          # Concurrent document scanners
    │   └── ingest.py           # Smart chunk splitters & vector storages
    ├── retrieval/
    │   └── retriever.py        # Hybrid dense/sparse RRF retriever
    ├── hardware/
    │   ├── detector.py         # CPU, RAM, and GPU scanner
    │   └── models.py           # VRAM sizing recommended formulas
    └── llm/
        ├── client.py           # Unified model client calls
        ├── router.py           # Circuit breaker failover routes
        └── memory.py           # Rolling conversational window bounds
```

### Technical Stack Breakdown

*   **Core AI Engine & Context Synthesis**: Powered by frontier and open-weight reasoning models (including Anthropic Claude 3.5 Sonnet, OpenAI GPT-5.4-mini, DeepSeek V3.2, Mistral AI, Gemini, and Groq/Llama-3.3) combined with persistent ChromaDB dense-sparse RAG search to deliver fast, highly accurate, and secure document context analysis.
*   **CLI & Rich Terminal Rendering**: Powered by **Python + Typer + Rich**, presenting a stunning, highly responsive terminal UI with micro-animations, clean progress bars, and beautifully framed panels.
*   **Local Persistent Vector Store**: Driven by a local **Persistent ChromaDB** client running semantic embeddings (`BAAI/bge-small-en-v1.5`) alongside classical keyword search (**Rank-BM25Okapi**).
*   **Hybrid Reciprocal Rank Fusion (RRF)**: Algebraically fuses dense vector distances and sparse keyword BM25 ranks using customizable weights (`BM25_WEIGHT` vs `VECTOR_WEIGHT`) for elite context relevance.
*   **Resilience Stack**: Session-aware **circuit breakers** actively monitor and cool down unstable endpoints (throttling HTTP 429/503 errors), cascading queries down a priority chain (Gemini 3.5 Flash / Claude Sonnet 4.6 ➔ Groq Llama 3.3 ➔ Local Ollama).

---

## 📸 Visual Walkthrough & Live MVP Proof

This section showcases a live visual walkthrough of our Phase 1 MVP in action, verifying the mathematical and algorithmic correctness of all core layers:

### Step 1: Intelligent Environment Initialization
![Intelligent Environment Initialization](https://github.com/prem22k/adviser-cli-tool/raw/main/assets/init.png)
> **Explanation**: Executing `adviser init` launches our hardware-aware setup wizard. Rather than acting as a blind API wrapper, the system automatically profiles the local system architecture (detecting 6 CPU cores, 7.4 GB RAM, and the hardware tier), verifies if the Ollama daemon is installed, and mathematically recommends model sizes that can run safely within a strict memory footprint.

---

### Step 2: Local Vector Ingestion & Chunking
![Local Vector Ingestion & Chunking](https://github.com/prem22k/adviser-cli-tool/raw/main/assets/ingest.png)
> **Explanation**: Showcases the high-performance execution of `adviser ingest` on 50 highly complex, confidential corporate crisis emails.
>
> **Data Provenance**: The test document corpus is sourced directly from the official [Kaggle Enron Email Dataset](https://www.kaggle.com/datasets/wcukierski/enron-email-dataset) benchmark corpus containing over 500,000 documents. The live walkthrough targets exactly 50 highly confidential crisis emails extracted from this massive corpus to verify the precision and latency of our hybrid dense-sparse vector ranking pipelines under complex multi-document corporate environments.
>
> The loader reads files concurrently, strips markdown frontmatter, applies the paragraph-aware chunk splitter, embeds the text using `BAAI/bge-small-en-v1.5`, and writes exactly 750 vector chunks to the persistent ChromaDB database—rendered in a consolidated, noise-free Rich progress UI.

---

### Step 3: Direct Knowledge Retrieval & Financial Analysis
![Direct Knowledge Retrieval & Financial Analysis](https://github.com/prem22k/adviser-cli-tool/raw/main/assets/chat_1.png)
> **Explanation**: Showcases the interactive `adviser chat` performing granular semantic extractions from the ingested corpus. The interface utilizes a highly responsive, fluid layout paradigm operating as an integrated, reactive 3-line inline block:
> *   **Line 1**: The active user input prompt featuring an advanced `prompt_toolkit` style sheet, displaying a cyan `> ` prefix paired with a bold royal_blue `User ❯ ` prompt string, where typed text is rendered in clean white.
> *   **Line 2**: Exactly one (1) blank empty line breakout spacer to isolate the input field from status components.
> *   **Line 3**: An inline text-styled shortcuts status bar (`? for shortcuts | /exit to quit | /clear to reset`) featuring real-time, right-aligned provider tracking (`anthropic` / `gemini` / `openai` / `groq` / `deepseek` / `mistral` / `openrouter` / `together` / `fireworks`).
> 
> In this run, the hybrid dense-sparse retriever extracts portfolio restructuring strategies and tracks market analyst upgrades and downgrades directly from internal corporate records, bypassing public wrappers. Crucially, as the conversation history scales, the entire 3-line interactive block scrolls fluidly within the console stream rather than remaining pinned or detached at the bottom of the physical monitor window, completely preventing cursor flickering or full-screen redraw jitter.

---

### Step 4: Enterprise RAG Capabilities & Structural Analysis
![Enterprise RAG Capabilities & Structural Analysis](https://github.com/prem22k/adviser-cli-tool/raw/main/assets/chat_2.png)
> **Explanation**: Our multi-document synthesis in action, running within the fluid, inline-scrolling CLI prompt loop. The layout engine isolates the active input interaction space from the historical scrollback frames using vertical spacer lines, which are cleanly cleared upon submission via ANSI escape sequences to preserve a pristine terminal log. 
> 
> The tool navigates deep, multi-threaded corporate exchanges to formulate a concise 5-point analysis of structural and bankruptcy risks during energy volatility crises. It prints the exact local persistent chunk locations directly in the shell for immediate code audibility, cleanly bounded by dim horizontal separator lines `─` that mark the completion of each response turn without duplication.

---

### Step 5: Model Context Protocol (MCP) IDE Synergy
![Model Context Protocol (MCP) IDE Synergy](https://github.com/prem22k/adviser-cli-tool/raw/main/assets/mcp_synergy.png)
> **Explanation**: Showcases the agentic integration of Adviser-CLI running as an active local Model Context Protocol (MCP) server inside your development environment.
> 
> Executing `adviser mcp-install` launches our interactive TUI selection wizard, programmatically registering the stdio-transport server with your Cursor IDE, Claude Desktop, Windsurf, or Cline extensions. Once active, advanced developer agents (like Cursor Composer or Claude Code) natively call Adviser's tools—such as `query_local_vector_index` and `fetch_document_source`—to retrieve proprietary semantic context and workspace records in real-time, providing unified private RAG capabilities straight to your coding workflow.

---

## 🛠️ Zero-Friction Global Installation

Adviser-CLI can be installed globally as a package, setting up its Python virtual environment and dependencies automatically.

### Option A: The NPM Installer (Recommended - Easiest & Runs Anywhere)
If you have Node.js/NPM installed, you can install Adviser-CLI globally with a single command. The installer automatically checks your Python 3 environment, initializes a localized virtualenv, and installs all dependencies in the background:
```bash
npm install -g adviser-cli
```
*Once installed, the `adviser` command is globally available. Simply run `adviser init` to launch the interactive setup wizard!*

---

### Option B: The Shell Installer Scripts
If you prefer shell-only installation without npm, clone the repository and run the express script for your operating system:
*   **macOS & Linux**:
    ```bash
    git clone https://github.com/prem22k/adviser-cli-tool.git && cd adviser-cli-tool && ./install.sh
    ```
*   **Windows (PowerShell)**:
    ```powershell
    git clone https://github.com/prem22k/adviser-cli-tool.git; cd adviser-cli-tool; powershell -ExecutionPolicy Bypass -File .\install.ps1
    ```

---

## 🤖 Zero-Friction IDE MCP Integration (One-Click Setup)

Adviser-CLI features an automated integration command to register itself as a Model Context Protocol (MCP) server for agentic IDE extensions in a single click:

```bash
adviser mcp-install
```

### What this does:
1. **Cursor IDE Integration**: Scans your system and programmatically injects the `adviser-mcp` server configuration directly into the global Cursor configuration file (`config.json`) across macOS, Windows, and Linux. No manual JSON editing or path copying required!
2. **Claude Code Integration**: Generates and prints the exact, ready-to-run terminal command to register Adviser-CLI with Claude Code globally:
   ```bash
   claude mcp add adviser-mcp -- /path/to/adviser mcp
   ```
3. **Concurrency-Safe Operation**: Automatically configures the persistent database to use **Write-Ahead Logging (WAL mode)** and accesses the database over a **shared-cache read-only connection**. This eliminates SQLite `database is locked` errors, enabling your IDE agent to run background queries concurrently while you execute CLI ingests.

---

## 💻 Execution & Command Reference

Verify your installation:
```bash
adviser --help
```

### 1. Multi-Profile Setup
```bash
# Launch the interactive profile setup wizard
adviser init

# List all saved configuration profiles
adviser profile list

# Select an active profile
adviser profile select my-profile
```

### 2. Ingest your Documents
```bash
adviser ingest
```
*To force rebuild the index, add the `-f` flag:*
```bash
adviser ingest --force
```

### 3. Start Chatting
```bash
adviser chat
```
*To display debugging panels showing dense/sparse scores, ranks, and RRF calculations for each query, add the `--debug` flag:*
```bash
adviser chat --debug
```

### 4. Generate a Digest Summary
```bash
adviser digest
```
*To preview the chapter breakdown, ETA time, and estimated token costs first:*
```bash
adviser digest --plan
```

### 5. Managing Index Snapshots
```bash
# Backup your active index to a compressed tarball
adviser snapshot save backup.tar.gz

# Restore an index from a compressed tarball
adviser snapshot load backup.tar.gz
```

---

## 🚀 Completed Phase 2 Technical Deliverables

We have fully implemented, tested, and delivered the Phase 2 systems roadmap:

1. **Model Context Protocol (MCP) Server**: A standard-compliant JSON-RPC Stdio transport server exposing `query_local_vector_index` and `fetch_document_source` tools natively.
2. **Layout-Aware VisionRAG Indexer**: A Pillow and `pdf2image` visual rasterization pipeline average-pooling ColPali `vidore/colpali-v1.2` patch embeddings into a 1280-dimension cosine index.
3. **Persisted SQLite WAL Concurrency**: Solves multi-process locks, enabling parallel retrieval queries during active vector updates.
4. **NPM Package Packaging**: Exposes `adviser` as a global Node-wrapped command, seamlessly bridging the Python ML backend with Node-centric IDE ecosystems.
5. **Claude-Style Hyper-Smooth Token Streaming**: Integrates a dedicated `rich.live.Live` manager and isolated layout `Group` container for flicker-free incremental markdown rendering, paired with a dynamic dots spinner (`• • •`) during cloud API latency.
6. **Styled Interactive Prompt Interface**: Upgrades the prompt session with advanced `prompt_toolkit` stylesheets (`royalblue` prompt, `cyan` prefix, `white` typed text, and `dim ansigray` auto-suggest), inline command history auto-suggestions (completed via Right Arrow), and visual spacer isolation that scrolls fluidly.

---

## 🛠️ Development & Engineering Credits

This project was engineered, developed, and stabilized through high-performance pair-programming leveraging:
*   **OpenAI Codex**: Used for initial prototyping, structural layout mapping, and quick code generation cycles.
*   **Antigravity (Google DeepMind)**: Used for Phase 2 systems auditing, advanced prompt-toolkit TUI refactoring, Model Context Protocol integration, and deployment stabilization.

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
