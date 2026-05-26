"""Map-reduce digest engine for large corpora."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from adviser.config import settings
from adviser.digest.planner import CHAPTER_SIZE, estimate_plan
from adviser.ingestion.loaders import DocumentLoader
from adviser.llm.client import LLMClient

console = Console()
SUMMARY_PATH = Path("data/global_summary.txt")
CHAPTER_PATTERN = re.compile(r"^## Chapter (\d+) Analysis\s*$", re.MULTILINE)


def main(providers: list[Any] | None = None) -> Path:
    loader = DocumentLoader()
    documents = loader.load(settings.DATA_PATH)
    corpus = "\n\n".join(str(document["text"]) for document in documents)
    if not corpus.strip():
        raise RuntimeError("No corpus text available for digest generation.")

    chapters = [corpus[index : index + CHAPTER_SIZE] for index in range(0, len(corpus), CHAPTER_SIZE)]
    plan = estimate_plan()
    console.print(
        Panel.fit(
            f"Corpus size: {plan['total_chars']:,} chars\n"
            f"Chapters: {plan['chapter_count']}\n"
            f"Summary output: {SUMMARY_PATH}",
            title="Digest Job",
            border_style="cyan",
        )
    )
    if not Confirm.ask("Proceed with full digest job?", default=True):
        raise RuntimeError("Digest cancelled by user.")

    start_index = _resume_index(SUMMARY_PATH)
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    client = LLMClient(providers=providers)

    mode = "a" if SUMMARY_PATH.exists() and start_index > 0 else "w"
    with SUMMARY_PATH.open(mode, encoding="utf-8") as handle:
        for chapter_number, chapter_text in enumerate(chapters[start_index:], start=start_index + 1):
            console.print(f"[cyan]Summarizing chapter {chapter_number}/{len(chapters)}...[/cyan]")
            messages = [
                {"role": "system", "content": settings.ADVISER_PERSONA},
                {
                    "role": "user",
                    "content": (
                        "Summarize the following chapter. Focus on the key ideas, claims, evidence, "
                        "and any practical implications.\n\n"
                        f"Chapter text:\n{chapter_text}"
                    ),
                },
            ]
            summary = client.chat(messages)
            handle.write(f"## Chapter {chapter_number} Analysis\n\n{summary.strip()}\n\n")

    console.print(f"[cyan]Digest saved:[/cyan] {SUMMARY_PATH}")
    return SUMMARY_PATH


def _resume_index(path: Path) -> int:
    if not path.exists():
        return 0
    content = path.read_text(encoding="utf-8")
    matches = CHAPTER_PATTERN.findall(content)
    if not matches:
        return 0
    return max(int(match) for match in matches)
