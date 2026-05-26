"""Concurrent text and markdown document loading helpers."""

from __future__ import annotations

import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn, TimeRemainingColumn

logger = logging.getLogger(__name__)
console = Console()
FRONTMATTER_PATTERN = re.compile(r"\A---\s*\n.*?\n---\s*\n?", re.DOTALL)


class DocumentLoader:
    """Load text documents from a single file or a directory tree."""

    SUPPORTED_EXTENSIONS = {".txt", ".md"}

    def load(self, path: Path) -> list[dict[str, Any]]:
        target = path.expanduser()
        if not target.exists():
            raise FileNotFoundError(f"Document path not found: {target}")
        if target.is_file():
            if target.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                logger.warning("Unsupported file type skipped: %s", target)
                return []
            with self._progress() as progress:
                task_id = progress.add_task("File Scanning & Loading", total=1)
                loaded = self._load_single(target)
                progress.advance(task_id)
            return [loaded] if loaded else []

        files = sorted(
            candidate
            for candidate in target.rglob("*")
            if candidate.is_file() and candidate.suffix.lower() in self.SUPPORTED_EXTENSIONS
        )
        if not files:
            return []

        docs: list[dict[str, Any]] = []
        max_workers = min(8, max(1, len(files)), (os.cpu_count() or 1))
        with self._progress() as progress:
            task_id = progress.add_task("File Scanning & Loading", total=len(files))
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_map = {executor.submit(self._load_single, file_path): file_path for file_path in files}
                for future in as_completed(future_map):
                    file_path = future_map[future]
                    try:
                        document = future.result()
                    except Exception as exc:
                        logger.warning("Skipping %s: %s", file_path, exc)
                        progress.advance(task_id)
                        continue
                    if document:
                        docs.append(document)
                    progress.advance(task_id)
        docs.sort(key=lambda item: item["source"])
        return docs

    def _load_single(self, path: Path) -> dict[str, Any] | None:
        try:
            text = path.read_text(encoding="utf-8")
        except Exception as exc:
            logger.warning("Skipping %s: %s", path, exc)
            return None

        if path.suffix.lower() == ".md":
            text = self._strip_frontmatter(text)
        text = text.strip()
        if not text:
            logger.warning("Skipping %s: extracted text is empty", path)
            return None
        return {"source": path.name, "text": text}

    def _strip_frontmatter(self, text: str) -> str:
        if text.startswith("---"):
            text = FRONTMATTER_PATTERN.sub("", text, count=1)
        return text

    @staticmethod
    def _progress() -> Progress:
        return Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(bar_width=40, style="cyan", complete_style="green"),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console,
        )
