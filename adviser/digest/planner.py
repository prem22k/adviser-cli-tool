"""Planning helpers for full-corpus digest jobs."""

from __future__ import annotations

import math
from typing import Any

from rich.console import Console
from rich.table import Table

from adviser.config import settings
from adviser.ingestion.loaders import DocumentLoader

console = Console()
CHAPTER_SIZE = 50_000
TOKEN_TO_CHAR_RATIO = 4
PROVIDER_SPEEDS = {
    "gemini": 90,
    "groq": 140,
    "ollama": 35,
}


def estimate_plan(providers: list[Any] | None = None) -> dict[str, Any]:
    loader = DocumentLoader()
    documents = loader.load(settings.DATA_PATH)
    total_chars = sum(len(str(document["text"])) for document in documents)
    chapter_count = max(1, math.ceil(total_chars / CHAPTER_SIZE))
    estimated_output_tokens = max(250, chapter_count * 700)

    table = Table(title="Digest Plan", expand=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Estimate", style="white")
    table.add_row("Corpus characters", f"{total_chars:,}")
    table.add_row("Estimated chapters", str(chapter_count))
    table.add_row("Estimated output tokens", f"{estimated_output_tokens:,}")

    for provider in providers or settings.get_provider_chain():
        speed = PROVIDER_SPEEDS.get(provider.name, 60)
        seconds = max(1, estimated_output_tokens // speed)
        table.add_row(f"{provider.name} ETA", f"~{seconds // 60}m {seconds % 60}s")

    console.print(table)
    return {
        "total_chars": total_chars,
        "chapter_count": chapter_count,
        "estimated_output_tokens": estimated_output_tokens,
    }
