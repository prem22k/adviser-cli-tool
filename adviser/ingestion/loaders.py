"""Concurrent document loading helpers."""

from __future__ import annotations

import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".docx", ".md"}
FRONTMATTER_PATTERN = re.compile(r"\A---\s*\n.*?\n---\s*\n?", re.DOTALL)


class DocumentLoader:
    """Load text documents from a single file or a directory tree."""

    def load(self, path: Path) -> list[dict[str, Any]]:
        target = path.expanduser()
        if not target.exists():
            raise FileNotFoundError(f"Document path not found: {target}")
        if target.is_file():
            loaded = self._load_single(target)
            return [loaded] if loaded else []

        files = sorted(
            candidate
            for candidate in target.rglob("*")
            if candidate.is_file() and candidate.suffix.lower() in SUPPORTED_EXTENSIONS
        )
        if not files:
            return []

        docs: list[dict[str, Any]] = []
        max_workers = min(8, max(1, len(files)), (os.cpu_count() or 1))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {executor.submit(self._load_single, file_path): file_path for file_path in files}
            for future in as_completed(future_map):
                file_path = future_map[future]
                try:
                    document = future.result()
                except Exception as exc:
                    logger.warning("Skipping %s: %s", file_path, exc)
                    continue
                if document:
                    docs.append(document)
        docs.sort(key=lambda item: item["source"])
        return docs

    def _load_single(self, path: Path) -> dict[str, Any] | None:
        suffix = path.suffix.lower()
        try:
            if suffix in {".txt", ".md"}:
                text = self._load_text(path, strip_frontmatter=suffix == ".md")
            elif suffix == ".pdf":
                text = self._load_pdf(path)
            elif suffix == ".docx":
                text = self._load_docx(path)
            else:
                logger.warning("Unsupported file type skipped: %s", path)
                return None
        except Exception as exc:
            logger.warning("Skipping %s: %s", path, exc)
            return None

        text = text.strip()
        if not text:
            logger.warning("Skipping %s: extracted text is empty", path)
            return None
        return {"source": str(path), "text": text}

    @staticmethod
    def _load_text(path: Path, strip_frontmatter: bool = False) -> str:
        text = path.read_text(encoding="utf-8")
        if strip_frontmatter and text.startswith("---"):
            text = FRONTMATTER_PATTERN.sub("", text, count=1)
        return text

    @staticmethod
    def _load_pdf(path: Path) -> str:
        try:
            import pdfplumber
        except ImportError as exc:
            raise RuntimeError(
                "PDF support requires pdfplumber. Install project dependencies before ingesting PDFs."
            ) from exc

        pages: list[str] = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                pages.append(page.extract_text() or "")
        return "\n".join(pages)

    @staticmethod
    def _load_docx(path: Path) -> str:
        try:
            from docx import Document
        except ImportError as exc:
            raise RuntimeError(
                "DOCX support requires python-docx. Install project dependencies before ingesting DOCX files."
            ) from exc

        document = Document(path)
        return "\n".join(paragraph.text for paragraph in document.paragraphs)
