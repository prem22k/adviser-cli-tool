# Codex Prompt: Implementing the Day-One Text & Markdown Ingestion Engine

You are an expert AI software engineer. Your task is to build a brand new, highly optimized, and clean Python document ingestion module as the day-one core asset for our new hackathon project, the **Adviser CLI** tool.

This module must handle recursively loading `.txt` and `.md` files from a target directory, stripping YAML frontmatter from markdown files, chunking the content using a paragraph-aware smart splitter, embedding the text chunks using the lightweight local `"BAAI/bge-small-en-v1.5"` SentenceTransformers model, and storing them in a local **ChromaDB** vector store using the `PersistentClient`.

To ensure a premium command-line interface experience, you must style the console output and use **Rich progress bars** to display real-time progress during the loading, chunking, and embedding phases.

---

## 🎯 Target Architecture & File Structure

Implement the logic split across two files within the `adviser` package structure:
1. `adviser/ingestion/loaders.py`: Responsible for loading files from a directory, concurrent file-reading, and stripping frontmatter.
2. `adviser/ingestion/ingest.py`: Responsible for paragraph-aware text-chunking, hash-based deterministic IDs, and indexing in ChromaDB using a `SentenceTransformerEmbeddingFunction` local model, all styled beautifully with `rich.progress`.

---

## 🛠️ Step-by-Step Implementation Guide

### Part 1: Document Loader (`adviser/ingestion/loaders.py`)

Implement a `DocumentLoader` class that conforms to the following guidelines:

1. **Class Signature**:
   ```python
   from pathlib import Path
   from typing import Any

   class DocumentLoader:
       SUPPORTED_EXTENSIONS = {".txt", ".md"}
       ...
   ```

2. **Concurrent Directory Scan**:
   - `load(self, path: Path) -> list[dict[str, Any]]`:
     - If the input path is a single file, load it directly.
     - If it is a directory, scan recursively using `rglob("*")` for files matching `SUPPORTED_EXTENSIONS`.
     - Use a `ThreadPoolExecutor` (capping max workers at 8) to read documents concurrently.
     - Handle file-level read errors (like encoding issues) gracefully by catching exceptions per-file, logging a warning, and continuing to index the rest of the corpus.
     - Returns a list of dictionaries: `[{"source": "filename.md", "text": "content..."}]`.

3. **Frontmatter Stripping**:
   - `_strip_frontmatter(self, text: str) -> str`:
     - If the text starts with `---`, use a regular expression to locate the second `---` on a new line and strip out the entire YAML header, returning only the actual document body.

---

### Part 2: Ingestion & ChromaDB Integration (`adviser/ingestion/ingest.py`)

Implement the chunking, embedding, and database loading logic under `adviser/ingestion/ingest.py`:

1. **Paragraph-Aware Smart Chunking**:
   - `smart_chunk(text: str, chunk_size: int = 400, overlap: int = 80) -> list[str]`:
     - Clean carriage returns (`\r\n` -> `\n`).
     - Split the text into paragraphs based on double newlines (`\n\n`).
     - Loop through paragraphs and aggregate them into a single chunk until adding the next paragraph would exceed `chunk_size` characters.
     - If an individual paragraph exceeds `chunk_size` characters on its own, fall back to word-boundary splits to fit as many words as possible into sub-chunks of size `chunk_size`.
     - If `overlap` is greater than 0, prepend the last `overlap` characters of the previous chunk to the beginning of the next chunk to maintain narrative context across chunk boundaries.

2. **Deterministic Hash-Based Chunk IDs**:
   - `chunk_id(text: str, source: str, idx: int) -> str`:
     - Generate a unique, stable ID for every chunk.
     - Calculate the MD5 hash of the chunk's text and slice the first 8 characters of the hex digest.
     - Format and return the ID as: `{source}_{idx}_{md5_hash_slice}`.

3. **ChromaDB Storage & Embedding Pipeline**:
   - `ingest(force_reload: bool = False)`:
     - Set up `chromadb.PersistentClient` pointing to `DB_PATH`.
     - Load the local embeddings model using Chroma's `SentenceTransformerEmbeddingFunction`:
       ```python
       from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

       embed_fn = SentenceTransformerEmbeddingFunction(
           model_name="BAAI/bge-small-en-v1.5",
           device="cpu",
           normalize_embeddings=True
       )
       ```
     - If `force_reload` is flagged, delete the existing `"adviser"` collection.
     - Get or create the `"adviser"` collection with cosine similarity mapping:
       ```python
       collection = client.get_or_create_collection(
           name="adviser",
           embedding_function=embed_fn,
           metadata={"hnsw:space": "cosine"}
       )
       ```
     - Read the documents using `DocumentLoader`.
     - Smart-chunk the loaded documents.
     - Add the chunks to ChromaDB in batches (e.g. batch size of 100) to keep memory footprint low and avoid API payload limitations.
     - Save metadata fields `{"source": doc_source, "chunk_idx": idx}` along with each chunk document.
     - Write a `stats.json` file inside `DB_PATH` preserving the state: `{"total_chunks": total_count, "sources": [list_of_filenames]}`.

---

## 🎨 Rich UI & Progress Bars Specification

To provide an elite, professional command-line experience, you must wrap all processing loops with beautiful terminal progress indicators from the `rich.progress` library.

1. **Progress Bar Configurations**:
   - Use `rich.progress.Progress` with the following columns:
     - `SpinnerColumn(spinner_name="dots")`
     - `TextColumn("[bold cyan]{task.description}")`
     - `BarColumn(bar_width=40, color="cyan", complete_color="green")`
     - `TaskProgressColumn()`
     - `TimeRemainingColumn()`
   - Display two separate tasks in the progress layout:
     1. **File Scanning & Loading**: Shows the real-time parsing progress as the thread pool reads files from the directory.
     2. **Embedding & Vector Storage**: Tracks the progress of batch processing and uploading chunks to the local ChromaDB.

2. **Console Styling & Theme Palette**:
   - Create a clean `rich.console.Console` instance.
   - Use consistent color keys:
     - Success / Complete: `[bold green]✓ Done![/bold green]`
     - Step description: `[cyan]...[/cyan]`
     - File metadata / stats: `[dim]...[/dim]` or `[grey50]...[/grey50]`
   - Group the final summary statistics inside a styled `rich.panel.Panel`:
     - Title: `Adviser Ingestion Statistics` in bold cyan.
     - Body: Clear, bulleted layout displaying the total number of files loaded, new chunks created, total chunks in the index, and the target database saving location.
