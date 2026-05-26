# Codex Prompt: Implementing the Zero-Infrastructure Adviser RAG CLI

You are an expert AI software engineer. Your task is to build a brand new **Adviser CLI** shell as part of a high-speed 7-day hackathon sprint. Adviser is a terminal-native, zero-infrastructure RAG assistant designed for querying and summarizing local documents with peak efficiency.

You must implement the entire codebase under the `adviser/` package using **Typer** for CLI structure, **Rich** for visual terminal styling, and **ChromaDB's PersistentClient** for the local vector store.

---

## 🎯 Target Architecture & Directory Layout

Construct the codebase exactly according to the following layout:

```text
adviser-cli-tool/
├── .env.example
├── pyproject.toml
└── adviser/
    ├── __init__.py
    ├── cli.py
    ├── config/
    │   ├── __init__.py
    │   ├── settings.py
    │   ├── profiles.py
    │   └── snapshots.py
    ├── digest/
    │   ├── __init__.py
    │   ├── engine.py
    │   └── planner.py
    ├── ingestion/
    │   ├── __init__.py
    │   ├── loaders.py
    │   └── ingest.py
    ├── retrieval/
    │   ├── __init__.py
    │   └── retriever.py
    └── llm/
        ├── __init__.py
        ├── client.py
        ├── router.py
        └── memory.py
```

---

## 🛠️ Step 1: Packaging & Project Setup

### `pyproject.toml`
Create a clean `pyproject.toml` utilizing modern PEP 517 build standards (using `setuptools`).
- **Dependencies**:
  - `chromadb>=0.5.0`
  - `sentence-transformers>=3.0.0`
  - `rank-bm25>=0.2.2`
  - `openai>=1.40.0`
  - `google-generativeai>=0.8.0`
  - `rich>=13.0.0`
  - `python-dotenv>=1.0.0`
  - `tiktoken>=0.7.0`
  - `tqdm>=4.66.0`
  - `typer>=0.12.0`
  - `pdfplumber>=0.11.0`
  - `python-docx>=1.1.0`
  - `ruamel.yaml>=0.18.0`
  - `prompt_toolkit>=3.0.0`
- **Optional Dev Dependencies**: `pytest`, `mypy`, `black`, `flake8`.
- **Scripts**: Define `adviser = "adviser.cli:app"` as the primary console script.

### `.env.example`
Provide a template configuration file specifying:
```env
# API Keys (Provide at least one)
GROQ_API_KEY=
GEMINI_API_KEY=

# Local paths
DATA_PATH=./data/corpus
DB_PATH=./data/chroma_db

# Chunking configurations
CHUNK_SIZE=400
CHUNK_OVERLAP=80

# Retrieval & LLM Settings
TOP_K_RETRIEVE=15
OLLAMA_MODEL=
OLLAMA_BASE_URL=http://localhost:11434
USE_AUDITOR=false
USE_RERANKER=false
```

---

## ⚙️ Step 2: Global Configuration & Profiles (`adviser/config/`)

### `adviser/config/settings.py`
This module acts as the single source of truth for all global variables.
- Load variables from `.env` via `python-dotenv`.
- Define default variables:
  - API Keys: `GROQ_API_KEY`, `GEMINI_API_KEY`
  - Paths: `DATA_PATH` (defaults to `./data/corpus.txt`), `DB_PATH` (defaults to `./data/chroma_db`)
  - Chunks: `CHUNK_SIZE` (400), `CHUNK_OVERLAP` (80)
  - Search Weights: `BM25_WEIGHT` (0.35), `VECTOR_WEIGHT` (0.65)
  - LLM Client defaults: `ADVISER_PERSONA` ("You are a knowledgeable adviser..."), `MAX_CONTEXT_TOKENS` (6000), `CONVERSATION_WINDOW` (6)
- Provide a `validate()` function that raises `RuntimeError` if no API keys are found, or `FileNotFoundError` if the specified `DATA_PATH` does not exist.
- Implement an HTTPS-enforcing utility `_enforce_https(url)` that enforces `https` schemes for non-loopback addresses while allowing local HTTP URLs (e.g. localhost, loopback IPs) to pass untouched.
- Create an `apply_profile(profile)` function that dynamically overrides global settings variables at runtime.
- Implement a list of provider objects (`get_provider_chain()`) including Gemini, Groq (leveraging OpenAI-compatible SDK), and Ollama (if active).

### `adviser/config/profiles.py`
Manage user configuration profiles stored as YAML files under `~/.config/adviser/profiles/`.
- Use `ruamel.yaml` for stable YAML serialization/deserialization.
- Define a `Profile` dataclass containing: `name`, `persona`, `data_path`, `db_path`, `chunk_size` (400), `chunk_overlap` (80), `top_k` (15), `providers` (list of strings).
- `Profile.save()`: Writes the profile attributes to `~/.config/adviser/profiles/{self.name}.yaml`.
- Provide a static `ProfileManager` class:
  - `create(name, persona, data_path, db_path, providers)`: Builds and persists a `Profile`.
  - `load(name)`: Loads and returns a `Profile` by reading its YAML file.
  - `list_profiles()`: Scans `~/.config/adviser/profiles/` and lists names.
  - `set_active(name)`: Writes the active profile's name into a single file at `~/.config/adviser/active`.
  - `get_active()`: Reads the active file, loads and returns the corresponding `Profile` object (or `None`).
  - `delete(name)`: Deletes the profile's YAML file and resets active tracking if it was the active profile.

---

## 📂 Step 3: Concurrency-based Document Loader (`adviser/ingestion/loaders.py`)

Create a flexible, thread-safe `DocumentLoader` capable of ingesting text from files and directories concurrently.
- Define `SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".docx", ".md"}`.
- Implement `load(path: Path) -> list[dict[str, Any]]`:
  - If a file, load it immediately.
  - If a directory, scan recursively using `rglob` for files matching `SUPPORTED_EXTENSIONS`.
  - Concurrently process files using a `ThreadPoolExecutor` (cap max workers to 8) to optimize reading large document sets. Handlers should gracefully catch exceptions per-file, logging warnings for skipped files without stopping the entire run.
- File-specific loaders:
  - `.txt` & `.md`: Read text via standard utf-8 file reads. For markdown files, strip YAML frontmatter if it starts with standard `---` boundaries.
  - `.pdf`: Extract text from all pages using `pdfplumber`. Provide friendly fallback guidance to run `pip install` if dependencies are missing.
  - `.docx`: Extract paragraph text using `python-docx`. Similarly, guide user if the package is missing.

---

## ⚡ Step 4: Core Ingestion Engine (`adviser/ingestion/ingest.py`)

Implement the text-chunking and ChromaDB storage pipeline.
- **Smart Chunking Algorithm**:
  - Implement `smart_chunk(text, chunk_size, overlap) -> list[str]`:
    - Clean Windows carriage returns.
    - Split text into paragraphs based on double newlines (`\n\n`).
    - Sequentially group paragraphs into larger chunks as long as they stay within `chunk_size`.
    - If a single paragraph is larger than `chunk_size`, fall back to word-boundary splits to pack maximum allowed characters.
    - Apply an overlapping trailing-text window (`overlap` characters) across adjacent chunks to maintain context flow across chunk edges.
- **ID Generation**:
  - `chunk_id(text, source, idx) -> str`: Return a deterministic unique ID based on a short MD5 hash of the chunk contents combined with the source file name and chunk index.
- **Main Ingestion Flow** `ingest(force_reload: bool)`:
  - Load the embedding model using Chroma's `SentenceTransformerEmbeddingFunction(model_name="BAAI/bge-small-en-v1.5", device="cpu", normalize_embeddings=True)`.
  - Establish connection to ChromaDB via `chromadb.PersistentClient(path=str(DB_PATH))`.
  - If `force_reload` is flagged, delete the existing collection `"adviser"` to reset.
  - Get or create collection `"adviser"` with cosine similarity metric `{"hnsw:space": "cosine"}`.
  - Use `DocumentLoader` to load files from `DATA_PATH`.
  - Chunk documents using `smart_chunk` and save metadata containing `{"source": doc_source, "chunk_idx": idx}`.
  - Add chunks and embeddings to the collection in batches.
  - Write a `stats.json` file inside `DB_PATH` saving ingestion stats: `{"total_chunks": total_count, "sources": [list_of_sources]}`.

---

## 🔍 Step 5: ChromaDB Persistent Hybrid Retriever (`adviser/retrieval/retriever.py`)

Implement hybrid text search using Vector Search and BM25, combined with Reciprocal Rank Fusion (RRF).
- **Initialization**:
  - Create a `HybridRetriever` class.
- **Database Loading**:
  - `load() -> dict[str, Any]`: Read the local embedding function `"BAAI/bge-small-en-v1.5"`. Initialize `chromadb.PersistentClient` pointing to `DB_PATH`. Retrieve all documents to train the BM25 search index.
  - Instantiate the BM25 index: Tokenize all loaded documents by splitting lowercase words, then load them into `BM25Okapi(tokenized)`.
  - Read `stats.json` if available and return.
- **Vector Search**:
  - `_vector_search(query, k)`: Run ChromaDB query `collection.query(query_texts=[query], n_results=k, include=["documents", "metadatas", "distances"])`. Convert distance scores to cosine similarity `score = 1 - distance`.
- **BM25 Search**:
  - `_bm25_search(query, k)`: Call `bm25.get_scores(query.lower().split())`. Return top `k` candidates with non-zero scores.
- **Reciprocal Rank Fusion**:
  - Implement RRF to merge vector search and BM25 ranks.
  - `_reciprocal_rank_fusion(vector_hits, bm25_hits, k=60) -> list[dict[str, Any]]`:
    - For each hit in Vector Hits: `score += VECTOR_WEIGHT / (k + rank + 1)`
    - For each hit in BM25 Hits: `score += BM25_WEIGHT / (k + rank + 1)`
    - Sort results in descending order of the combined RRF score.
- **Main Search Interface**:
  - `search(query, top_k) -> list[dict[str, Any]]`: Fetch `top_k * 3` candidates from Vector and BM25 searches, fuse using RRF, and slice down to `top_k`.
- **Formatting Context**:
  - `format_context(hits, max_chars=12000) -> str`: Concatenate chunks formatted clearly as `[Chunk idx | source_name]\ntext` until hitting the maximum character budget.

---

## 🧠 Step 6: Multi-Provider LLM Client, Memory & Circuit Breaker (`adviser/llm/`)

### `adviser/llm/router.py` (Circuit Breaker)
Implement a session-scoped circuit breaker to bypass broken or throttled API connections immediately.
- Define a `ProviderState` dataclass storing `name`, `failed_at`, `failure_reason`, and `cooldown_seconds` (default 300s).
- Build a `CircuitBreaker(providers)` wrapper:
  - Maintain a dictionary mapping provider names to `ProviderState` trackers.
  - `is_available(provider_name)`: Verify if the provider is healthy or has cooled down since its last failure.
  - `mark_failed(provider_name, reason)`: Lock out a provider.
  - `available_providers(providers)`: Filter a provider chain list to return only healthy instances.

### `adviser/llm/memory.py` (Rolling Memory Window)
Maintain interactive session memory cleanly.
- `ConversationMemory(window_size)`:
  - Use a rolling memory window. Keep the last `window_size * 2` message blocks.
  - `add(role, content)`: Append a chat role block.
  - `get_messages(system_prompt, user_query, context)`: Return a list of OpenAI-style message dictionaries. Prepend the global system prompt. Augment the final user query block by injecting the retrieved document context.

### `adviser/llm/client.py` (LLM Client with Failover Cascade)
- Initialize the cascade of configured providers (Gemini, Groq, Ollama) and load the `CircuitBreaker`.
- Setup Gemini using the native `google-generativeai` SDK. Translate standard messages list into Gemini chat history structures (mapping `system` prompts to the user's first input, and mapping `assistant` to `model`).
- Implement the primary OpenAI-compatible generator `_call_openai_compatible(provider, messages)` to query remote endpoints (like Groq) and local Ollama models.
- Implement the primary entrypoint `chat(messages) -> str`:
  - Fetch available providers from the `CircuitBreaker`.
  - Loop through available providers sequentially. If a provider raises `RateLimitError` or standard connection errors, print an warning, call `circuit_breaker.mark_failed(provider_name, error)', and cascade immediately to the next provider.
  - Print streaming tokens to terminal standard output in real-time. Return the completed full text.

---

## 🗺️ Step 7: Map-Reduce Document Digest Engine (`adviser/digest/`)

Implement the multi-chapter summarization engine.

### `adviser/digest/planner.py` (Plan Mode)
- `estimate_plan()`: Read the total character size of the corpus. Divide by `50,000` to calculate the number of chapters. Output a Rich Table showing estimated corpus size, chapter count, output token count, and time forecasts per provider based on conservative speed heuristics.

### `adviser/digest/engine.py` (Digest Engine)
- Implement Map-Reduce summarization:
  - Load the corpus from `DATA_PATH`.
  - Split text into consecutive chapters of 50,000 characters.
  - Output estimated stats and block with `Confirm.ask("Proceed with full digest job?")`.
  - Use `LLMClient` to summarize each chapter.
  - Save results to `data/global_summary.txt` in a clean Markdown format with headers `## Chapter {i} Analysis`.
  - **Resuming Functionality**: If `data/global_summary.txt` already exists, parse the file to find the last successfully summarized chapter (e.g. `## Chapter X Analysis`), and resume the process from chapter `X + 1` automatically.

---

## 💾 Step 8: Database Snapshots (`adviser/config/snapshots.py`)

Enable users to easily backup and restore their indexed knowledge bases.
- Create a `SnapshotManager` class.
- `save(output_path: Path)`: Pack the entire `DB_PATH` directory into a compressed `.tar.gz` archive. Log clear Rich success feedback.
- `load(input_path: Path)`: Restore the database.
  - If a database directory currently exists at `DB_PATH`, safely backup the existing directory by renaming it to `{DB_PATH}.bak` before restoring.
  - Decompress the `.tar.gz` archive back to the target `DB_PATH`.

---

## 🖥️ Step 9: Typer CLI & Rich UI Shell (`adviser/cli.py`)

Create the visual CLI interface utilizing Typer command bindings and Rich visual components.

### Subcommand Tree
- Define `app = typer.Typer(...)` with `invoke_without_command=True`.
- Define subcommand routers:
  - `snapshot_app = typer.Typer()` -> registered as `app.add_typer(snapshot_app, name="snapshot")`
  - `profile_app = typer.Typer()` -> registered as `app.add_typer(profile_app, name="profile")`
  - `sync_app = typer.Typer()` -> registered as `app.add_typer(sync_app, name="sync")`

### CLI Command Specifications
1. **Interactive Chat** (`adviser` or `adviser chat` command):
   - Check if a profile argument was provided; otherwise, load the active profile.
   - Validate that API keys are set. If not, print setup instructions and exit.
   - Load the `HybridRetriever`, `LLMClient`, and `ConversationMemory`.
   - Setup a `prompt_toolkit` `PromptSession`.
   - Output a beautiful header panel:
     - Print `ADVISER v0.1.0` in bold white on a cyan background.
     - Show total loaded chunks count.
     - List the primary active LLM provider.
     - Print a helper rule: `Type exit to quit | clear to reset | sources to list files`.
   - Run the REPL loop:
     - Prompt user: `User ❯` in bold cyan.
     - Handle commands: `exit` / `quit` to exit, `clear` to reset memory, `sources` to display all currently indexed files.
     - Query `retriever.search(query)`.
     - In debug mode, print RRF scores, sources, and snippet previews for the top retrieved hits inside a dim panel.
     - Pass retrieved context and conversation history to `LLMClient.chat()` to stream the response.
2. **Ingest** (`adviser ingest` command):
   - Accept option `--force` / `-f` to trigger a clean re-index.
   - Call `ingest(force_reload=force)`.
3. **Digest** (`adviser digest` command):
   - Accept option `--plan` / `-p` to run plan estimation.
   - If plan is set, call `estimate_plan()`. Otherwise, call the digest `main()` executor.
4. **Snapshot Commands**:
   - `snapshot save [path]`: Call `SnapshotManager.save(path)`.
   - `snapshot load [path]`: Call `SnapshotManager.load(path)`.
5. **Profile Commands**:
   - `profile list`: Print a table of all profiles showing their document paths. Mark the active profile with a green asterisk.
   - `profile select [name]`: Activate the profile using `ProfileManager.set_active(name)`.
   - `profile create --name [name] --data-path [path] --persona [persona]`: Instantiate a new profile. Automatically assign a default database path under `~/.local/share/adviser/{name}/chroma_db`.

---

## 🧙 Step 10: Setup Wizard (`adviser init`)

Provide an interactive wizard to configure Adviser settings during first-time use.
- Output a styled setup panel: `Adviser Setup Wizard`.
- Simulate or implement lightweight hardware scanning (CPU cores, RAM size, GPU availability).
- Prompt the user interactively (using Rich prompts with default values):
  - Profile name (defaults to `"default"`).
  - Absolute path to document folder (e.g. `~/Documents/corpus`).
  - Personal instructions / custom persona.
  - Enable Cloud APIs (Groq/Gemini)?
  - Enable Ollama (Local)?
- Construct a new `Profile` with these answers, save it, and automatically register it as the active session profile.
- Output a styled concluding card showing clear next steps:
  1. Run `adviser ingest` to parse documents.
  2. Run `adviser chat` to start the assistant!

---

## 🎨 Rich Styling Guidelines
To ensure a premium terminal experience, enforce these styling details:
- Use consistent text colors: Info (`cyan`), Warning (`yellow`), Error (`bold red`), Assistant responses (`bold green`), User prompts (`bold cyan`), and metadata (`grey50` / `dim`).
- Surround complex status actions with `console.status("[dim]Working...[/dim]", spinner="dots")`.
- Format lists of documents, stats, and plans using clean, non-expanding `rich.table.Table` grids or styled `rich.panel.Panel` boxes.
