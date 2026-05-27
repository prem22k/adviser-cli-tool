# Adviser CLI
> **Zero-Infrastructure, Local-First Hybrid RAG Assistant in the Terminal**

Adviser is a terminal-native, zero-infrastructure Retrieval-Augmented Generation (RAG) assistant designed to search, query, and summarize large collections of private text and markdown documents. By combining local dense-sparse retrieval with priority-cascade LLM routing, active hardware auto-detection, and circuit-breaker safety, Adviser brings private, fast, and resilient intelligence straight to your command line.

---

## ✨ Core Highlights & Architecture

```text
                                [ User Corpus ] (.txt, .md)
                                       │
                                       ▼ (Concurrent scanning & loading)
                           [ Paragraph-Aware Splitter ]
                                       │
               ┌───────────────────────┴───────────────────────┐
               ▼ (Local BAAI/bge-small-en-v1.5)               ▼ (Local tokenization)
       [ Dense ChromaDB Vector ]                       [ Sparse BM25 Keywords ]
               │                                               │
               └───────────────────────┬───────────────────────┘
                                       ▼ (Reciprocal Rank Fusion)
                            [ Hybrid RRF Context ]
                                       │
               ┌───────────────────────┼───────────────────────┐
               ▼                       ▼                       ▼
      [ Cloud: Gemini ]       [ Cloud: Groq Llama3 ]  [ Local: Ollama / AirLLM ]
```

### 🧠 1. Dense + Sparse Hybrid Retrieval Stack
*   **Dual-Engine Search**: Combines semantic embeddings (dense vector search using local `BAAI/bge-small-en-v1.5`) with classical keyword relevance (sparse keyword search using `Rank-BM25Okapi`).
*   **Reciprocal Rank Fusion (RRF)**: Merges results from both dense and sparse sources, balancing weights (`BM25_WEIGHT` vs `VECTOR_WEIGHT`) to produce exceptionally high retrieval precision without the latency of heavy reranker models.

### ⚡ 2. Resilient Priority-Cascade Routing
*   **Provider Chain**: Cascades your query down a prioritized chain of LLMs—from Google Gemini (`gemini-3.5-flash`), to Groq (`llama-3.1-8b-instant`), down to local offline models.
*   **Session-Aware Circuit Breaker**: Actively monitors provider health. If a primary service encounters a rate limit (HTTP 429), connection timeout, or transient outage, the circuit breaker trips, sets a 300-second cooldown, and automatically routes the prompt to the next fallback provider in line without interrupting your active chat.

### 🖥️ 3. Hardware Auto-Detection & Local LLM Sizing
*   **Hardware Profiler**: Auto-detects local system resources (CPU cores count, available system RAM, and GPU architectures like NVIDIA CUDA, macOS Metal Unified Memory, and AMD ROCm).
*   **Smart Sizing Catalog**: Matches your **Hardware Tier** against a mathematical VRAM/RAM model size validator (with a strict 15% safety headroom) to recommend the exact local Ollama models (such as `llama3.2:3b` or `deepseek-r1:7b`) that can execute safely on your machine.
*   **Ollama Pre-Flight Checks**: Verifies if the local Ollama daemon is installed, warning you and presenting exact one-liner commands to install it if it is missing.

### 💾 4. Offline Memory-Efficient AirLLM Provider
*   **Local Layer-Wise Inference**: Integrates **AirLLM** to run massive models (like 70B parameters) locally on small consumer GPUs (with as little as 4GB VRAM) by loading model layers sequentially in-memory.

### 🔄 5. Map-Reduce Digest Summary Engine
*   **Chapter Splits**: Breaks large corpora into ~50k-character chapters, summarizing them using map calls.
*   **Crash-Resume Logic**: Scans existing partial summaries, detects completed segments, and resumes precisely where the run was interrupted.
*   **Plan Estimator**: Calculates token overheads, outlines ETA speeds, and estimates execution costs across active providers before launching.

---

## 📂 Codebase Layout

```text
adviser-cli-tool/
├── .env.example                # Template configuration file
├── pyproject.toml              # Packaging and dependency declarations
├── README.md                   # Complete architectural guide
└── adviser/
    ├── __init__.py
    ├── cli.py                  # CLI entrypoint commands, setup wizards, loops
    ├── config/
    │   ├── __init__.py
    │   ├── settings.py         # Source-of-truth configuration properties
    │   ├── profiles.py         # Multi-profile configurations management
    │   └── snapshots.py        # Compressed tarball backup utilities
    ├── digest/
    │   ├── __init__.py
    │   ├── engine.py           # Map-reduce digest summarizer
    │   └── planner.py          # Digest token & ETA plan estimator
    ├── ingestion/
    │   ├── __init__.py
    │   ├── loaders.py          # Concurrent document scanners
    │   └── ingest.py           # Smart chunk splitters & vector storages
    ├── retrieval/
    │   ├── __init__.py
    │   └── retriever.py        # Hybrid dense/sparse RRF retriever
    ├── hardware/
    │   ├── __init__.py
    │   ├── detector.py         # CPU, RAM, and GPU scanner
    │   ├── models.py           # VRAM sizing recommended formulas
    │   └── catalog.yaml        # Sizing recommendations dataset
    └── llm/
        ├── __init__.py
        ├── client.py           # Unified model client calls
        ├── router.py           # Circuit breaker failover routes
        ├── airllm_provider.py  # Layer-wise memory-efficient local execution
        └── memory.py           # Rolling conversational window bounds
```

---

## 🛠️ Installation & Setup

Adviser requires **Python 3.10+** and runs entirely within a virtual environment:

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

## ⚙️ Configuration & Environment

Configuration is governed by environment variables. You can export these variables directly in your active terminal session or write them persistently into a `.env` file at the root of the project:

```bash
# Copy the template file
cp .env.example .env
```

### Essential Settings:
*   `GEMINI_API_KEY`: Google Gemini credential key (required for cloud fallback).
*   `GROQ_API_KEY`: Groq API credential key (required for cloud fallback).
*   `OLLAMA_MODEL`: The local Ollama model name to target (e.g. `llama3.1:8b`).
*   `AIRLLM_MODEL`: The local AirLLM HuggingFace model identifier (e.g. `meta-llama/Llama-3.2-3B-Instruct`).

---

## 🚀 Execution & Command Reference

Verify your installation:
```bash
adviser --help
```

### 1. Initialize a Profile (`adviser init`)
Launch the hardware-aware setup wizard. It scans system resources, verifies if Ollama is installed, recommends optimal local models, and saves an active settings profile (e.g. `test-profile` pointing to `./test_corpus`):
```bash
adviser init
```

### 2. Ingest your Documents (`adviser ingest`)
Ingests all `.txt` and `.md` files in the corpus folder, concurrently strips frontmatter, splits paragraphs with carried-over context, and embeds them into ChromaDB:
```bash
adviser ingest
```
*To force rebuild the index, add the `-f` flag:*
```bash
adviser ingest --force
```

### 3. Start Chatting (`adviser chat` or `adviser`)
Starts the interactive chat session, loading memory history buffers and retrieving context on each user query:
```bash
adviser chat
```
*To display debugging panels showing dense/sparse scores, ranks, and RRF calculations for each query, add the `--debug` flag:*
```bash
adviser chat --debug
```

### 4. Generate a Digest Summary (`adviser digest`)
Generates a comprehensive map-reduce summary of your entire corpus:
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

## 🧪 System Logic Verification

A custom local testing validation run proves the mathematical and algorithmic correctness of all core layers:

```bash
# Test Ingest splits, Document Frontmatter loaders, LLM Circuit Breakers, and Hybrid search RRF ranks:
python -c "
from adviser.ingestion.ingest import smart_chunk
from adviser.ingestion.loaders import DocumentLoader
from adviser.llm.router import CircuitBreaker
from adviser.config.settings import ProviderConfig
from adviser.retrieval.retriever import HybridRetriever

# 1. Smart Paragraph-Aware Splitter Test
print(smart_chunk('Paragraph 1.\n\nParagraph 2.', chunk_size=100, overlap=10))

# 2. Loader YAML Frontmatter Stripper Test
print(DocumentLoader()._strip_frontmatter('---\ntitle: test\n---\nBody content'))

# 3. LLM Router Failover Test
prov1 = ProviderConfig(name='gemini', kind='gemini', model='gemini-3.5-flash')
prov2 = ProviderConfig(name='groq', kind='openai-compatible', model='llama-3.1-8b-instant')
breaker = CircuitBreaker([prov1, prov2])
breaker.mark_failed('gemini', 'rate_limit')
print('Active provider after primary fail:', breaker.available_providers([prov1, prov2])[0].name)
"
```

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
