"""Document chunking and Chroma persistence pipeline."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn, TimeRemainingColumn

from adviser.config import settings
from adviser.ingestion.loaders import DocumentLoader

console = Console()


def smart_chunk(text: str, chunk_size: int = 400, overlap: int = 80) -> list[str]:
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not cleaned:
        return []

    paragraphs = [paragraph.strip() for paragraph in cleaned.split("\n\n") if paragraph.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > chunk_size:
            if current:
                chunks.append(current.strip())
                current = ""
            chunks.extend(_split_long_paragraph(paragraph, chunk_size))
            continue

        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            chunks.append(current.strip())
            current = paragraph

    if current:
        chunks.append(current.strip())

    if overlap <= 0 or len(chunks) <= 1:
        return chunks

    overlapped: list[str] = []
    for index, chunk in enumerate(chunks):
        if index == 0:
            overlapped.append(chunk)
            continue
        carry = chunks[index - 1][-overlap:].strip()
        combined = f"{carry}\n{chunk}".strip() if carry else chunk
        overlapped.append(combined)
    return overlapped


def _split_long_paragraph(paragraph: str, chunk_size: int) -> list[str]:
    words = paragraph.split()
    if not words:
        return []

    pieces: list[str] = []
    current_words: list[str] = []
    current_length = 0

    for word in words:
        projected = current_length + len(word) + (1 if current_words else 0)
        if projected <= chunk_size:
            current_words.append(word)
            current_length = projected
            continue

        if current_words:
            pieces.append(" ".join(current_words))
            current_words = []
            current_length = 0

        while len(word) > chunk_size:
            pieces.append(word[:chunk_size])
            word = word[chunk_size:]
        current_words = [word]
        current_length = len(word)

    if current_words:
        pieces.append(" ".join(current_words))
    return pieces


def chunk_id(text: str, source: str, idx: int) -> str:
    digest = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
    return f"{source}_{idx}_{digest}"


def ingest(force_reload: bool = False) -> dict[str, object]:
    if not settings.DATA_PATH.exists():
        raise FileNotFoundError(f"Configured DATA_PATH does not exist: {settings.DATA_PATH}")

    try:
        import chromadb
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
    except ImportError as exc:
        raise RuntimeError("ChromaDB and sentence-transformers must be installed to run ingestion.") from exc

    console.print(f"[cyan]Loading documents from[/cyan] [dim]{settings.DATA_PATH}[/dim]")
    settings.DB_PATH.mkdir(parents=True, exist_ok=True)
    embedding_function = SentenceTransformerEmbeddingFunction(
        model_name="BAAI/bge-small-en-v1.5",
        device="cpu",
        normalize_embeddings=True,
    )
    client = chromadb.PersistentClient(path=str(settings.DB_PATH))

    if force_reload:
        try:
            client.delete_collection("adviser")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name="adviser",
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"},
    )

    loader = DocumentLoader()
    documents = loader.load(settings.DATA_PATH)
    if not documents:
        raise RuntimeError(f"No supported documents found under {settings.DATA_PATH}")

    console.print(f"[cyan]Chunking loaded documents[/cyan] [dim]({len(documents)} files)[/dim]")
    all_ids: list[str] = []
    all_texts: list[str] = []
    all_metadatas: list[dict[str, object]] = []
    sources: list[str] = []

    with _progress() as progress:
        task_id = progress.add_task("Chunking Documents", total=len(documents))
        for document in documents:
            source = str(document["source"])
            sources.append(source)
            chunks = smart_chunk(str(document["text"]), settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
            for idx, chunk in enumerate(chunks):
                all_ids.append(chunk_id(chunk, source, idx))
                all_texts.append(chunk)
                all_metadatas.append({"source": source, "chunk_idx": idx})
            progress.advance(task_id)

    batch_size = 100
    with _progress() as progress:
        task_id = progress.add_task(
            "Embedding & Vector Storage",
            total=max(1, (len(all_ids) + batch_size - 1) // batch_size),
        )
        for start in range(0, len(all_ids), batch_size):
            end = start + batch_size
            collection.upsert(
                ids=all_ids[start:end],
                documents=all_texts[start:end],
                metadatas=all_metadatas[start:end],
            )
            progress.advance(task_id)

    stats = {"total_chunks": len(all_ids), "sources": sorted(set(sources))}
    stats_path = settings.DB_PATH / "stats.json"
    stats_path.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    total_indexed_chunks = collection.count()

    console.print("[bold green]✓ Done![/bold green]")
    console.print(
        Panel(
            "\n".join(
                [
                    f"• Files loaded: [dim]{len(documents)}[/dim]",
                    f"• New chunks created: [dim]{len(all_ids)}[/dim]",
                    f"• Total chunks in index: [dim]{total_indexed_chunks}[/dim]",
                    f"• Database path: [dim]{settings.DB_PATH}[/dim]",
                ]
            ),
            title="[bold cyan]Adviser Ingestion Statistics[/bold cyan]",
            border_style="cyan",
        )
    )
    return {
        "files_loaded": len(documents),
        "total_chunks": len(all_ids),
        "indexed_chunks": total_indexed_chunks,
        "sources": sorted(set(sources)),
        "db_path": str(settings.DB_PATH),
    }


def _progress() -> Progress:
    return Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(bar_width=40, style="cyan", complete_style="green"),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console,
    )
