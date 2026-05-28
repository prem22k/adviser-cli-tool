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

*   **Core AI Engine & Code Intelligence**: Powered by **OpenAI Codex** and advanced models to provide high-fidelity code understanding, structured retrieval, and rapid, deterministic build routing across local or cloud pipelines.
*   **CLI & Rich Terminal Rendering**: Powered by **Python + Typer + Rich**, presenting a stunning, highly responsive terminal UI with micro-animations, clean progress bars, and beautifully framed panels.
*   **Local Persistent Vector Store**: Driven by a local **Persistent ChromaDB** client running semantic embeddings (`BAAI/bge-small-en-v1.5`) alongside classical keyword search (**Rank-BM25Okapi**).
*   **Hybrid Reciprocal Rank Fusion (RRF)**: Algebraically fuses dense vector distances and sparse keyword BM25 ranks using customizable weights (`BM25_WEIGHT` vs `VECTOR_WEIGHT`) for elite context relevance.
*   **Resilience Stack**: Session-aware **circuit breakers** actively monitor and cool down unstable endpoints (throttling HTTP 429/503 errors), cascading queries down a priority chain (Gemini 3.5 Flash ➔ Groq Llama 3.3 ➔ Local Ollama).

---

## 📸 Visual Walkthrough & Live MVP Proof

This section showcases a live visual walkthrough of our Phase 1 MVP in action, verifying the mathematical and algorithmic correctness of all core layers:

### Step 1: Intelligent Environment Initialization
![Intelligent Environment Initialization](./assets/init.png)
> **Explanation**: Executing `adviser init` launches our hardware-aware setup wizard. Rather than acting as a blind API wrapper, the system automatically profiles the local system architecture (detecting 6 CPU cores, 7.4 GB RAM, and the hardware tier), verifies if the Ollama daemon is installed, and mathematically recommends model sizes that can run safely within a strict memory footprint.

---

### Step 2: Local Vector Ingestion & Chunking
![Local Vector Ingestion & Chunking](./assets/ingest.png)
> **Explanation**: Showcases the high-performance execution of `adviser ingest` on 50 highly complex, confidential corporate crisis emails.
>
> **Data Provenance**: The test document corpus is sourced directly from the official [Kaggle Enron Email Dataset](https://www.kaggle.com/datasets/wcukierski/enron-email-dataset) benchmark corpus containing over 500,000 documents. The live walkthrough targets exactly 50 highly confidential crisis emails extracted from this massive corpus to verify the precision and latency of our hybrid dense-sparse vector ranking pipelines under complex multi-document corporate environments.
>
> The loader reads files concurrently, strips markdown frontmatter, applies the paragraph-aware chunk splitter, embeds the text using `BAAI/bge-small-en-v1.5`, and writes exactly 750 vector chunks to the persistent ChromaDB database—rendered in a consolidated, noise-free Rich progress UI.

---

### Step 3: Direct Knowledge Retrieval & Financial Analysis
![Direct Knowledge Retrieval & Financial Analysis](./assets/chat_1.png)
> **Explanation**: Showcases the interactive `adviser chat` performing granular semantic extractions from the ingested corpus. In this run, the hybrid dense-sparse retriever effortlessly extracts portfolio restructuring strategies (including the QQQ tax-loss token roll) and tracks market analyst upgrades and downgrades directly from internal corporate records, bypassing public wrappers.

---

### Step 4: Enterprise RAG Capabilities & Structural Analysis
![Enterprise RAG Capabilities & Structural Analysis](./assets/chat_2.png)
> **Explanation**: Our heavy-hitting multi-document synthesis in action. The tool navigates deep, multi-threaded corporate exchanges to formulate a concise 5-point analysis of structural and bankruptcy risks during energy volatility crises. It prints the exact local persistent chunk locations directly in the shell for immediate code audibility.

---

## 🛠️ Installation & Setup

Adviser requires **Python 3.10+** and is designed to install and configure itself automatically in under 60 seconds.

### The 1-Command Express Installer (Recommended)
Simply clone the repository and run the express installer script matching your operating system. It automatically builds a localized virtual environment (`./venv`), optimizes dependencies (leveraging `uv` if present for 10x faster installation, with a robust fallback to standard `pip`), and launches the setup wizard instantly:

*   **macOS & Linux**:
    ```bash
    git clone https://github.com/prem22k/adviser-cli-tool.git && cd adviser-cli-tool && ./install.sh
    ```
*   **Windows (PowerShell)**:
    ```powershell
    git clone https://github.com/prem22k/adviser-cli-tool.git; cd adviser-cli-tool; powershell -ExecutionPolicy Bypass -File .\install.ps1
    ```

---

### Manual Step-by-Step Installation
If you prefer to configure your environment manually, you can execute the following steps:

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/prem22k/adviser-cli-tool.git
    cd adviser-cli-tool
    ```

2.  **Create and activate a standard virtual environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the package in editable mode with development dependencies**:
    ```bash
    pip install -e ".[dev]"
    ```

---

## 🛠️ Execution & Command Reference

Verify your installation:
```bash
adviser --help
```

### 1. Initialize a Profile
```bash
adviser init
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

### 5. Managing Profiles & Snapshots
```bash
# List all saved configuration profiles
adviser profile list

# Select an active profile
adviser profile select my-profile

# Backup your active index to a compressed tarball
adviser snapshot save backup.tar.gz

# Restore an index from a compressed tarball
adviser snapshot load backup.tar.gz
```

---

## 🚀 Phase 2 Technical Roadmap

Our remaining 7-day sprint will focus on elevating Adviser-CLI from a terminal-native chat tool into a deeply integrated developer workspace assistant:

1.  **VisionRAG Pipeline (ColPali Integration)**:
    *   Implement layout-aware visual embeddings. For complex system architectures, database schemas, and multi-repo financial PDFs where text parsers destroy tables and charts, Adviser will parse PDF pages as high-resolution images, preserving visual and tabular structures.
2.  **Model Context Protocol (MCP) Server Integration**:
    *   Expose the local ChromaDB persistent index as a secure, authenticated MCP server. This allows agentic IDE extensions (like Cursor, Claude Code, and Windsurf) to query local corporate context autonomously while keeping your source code and documentation strictly local and private.

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
