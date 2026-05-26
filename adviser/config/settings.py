"""Global runtime settings for Adviser."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse

from dotenv import load_dotenv

load_dotenv()


@dataclass(slots=True)
class ProviderConfig:
    name: str
    kind: str
    model: str
    api_key: str | None = None
    base_url: str | None = None


GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

DATA_PATH = Path(os.getenv("DATA_PATH", "./data/corpus.txt")).expanduser()
DB_PATH = Path(os.getenv("DB_PATH", "./data/chroma_db")).expanduser()

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "400"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "80"))
TOP_K_RETRIEVE = int(os.getenv("TOP_K_RETRIEVE", "15"))

BM25_WEIGHT = float(os.getenv("BM25_WEIGHT", "0.35"))
VECTOR_WEIGHT = float(os.getenv("VECTOR_WEIGHT", "0.65"))

ADVISER_PERSONA = os.getenv(
    "ADVISER_PERSONA",
    "You are a knowledgeable adviser who answers carefully from the provided local context.",
)
MAX_CONTEXT_TOKENS = int(os.getenv("MAX_CONTEXT_TOKENS", "6000"))
CONVERSATION_WINDOW = int(os.getenv("CONVERSATION_WINDOW", "6"))

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "").strip()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()
USE_AUDITOR = os.getenv("USE_AUDITOR", "false").strip().lower() == "true"
USE_RERANKER = os.getenv("USE_RERANKER", "false").strip().lower() == "true"


def _is_loopback_host(hostname: str | None) -> bool:
    if not hostname:
        return False
    return hostname in {"localhost", "127.0.0.1", "::1"} or hostname.startswith("127.")


def _enforce_https(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return url
    if parsed.scheme == "https":
        return url
    if parsed.scheme == "http" and _is_loopback_host(parsed.hostname):
        return url
    if parsed.scheme == "http":
        return urlunparse(parsed._replace(scheme="https"))
    return url


def validate() -> None:
    has_cloud_key = bool(GROQ_API_KEY or GEMINI_API_KEY)
    has_local_provider = bool(OLLAMA_MODEL)
    if not has_cloud_key and not has_local_provider:
        raise RuntimeError(
            "No LLM providers configured. Set GROQ_API_KEY or GEMINI_API_KEY, or configure OLLAMA_MODEL."
        )
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Configured DATA_PATH does not exist: {DATA_PATH}")


def apply_profile(profile: Any) -> None:
    global ADVISER_PERSONA
    global CHUNK_OVERLAP
    global CHUNK_SIZE
    global DATA_PATH
    global DB_PATH
    global TOP_K_RETRIEVE

    ADVISER_PERSONA = profile.persona
    DATA_PATH = Path(profile.data_path).expanduser()
    DB_PATH = Path(profile.db_path).expanduser()
    CHUNK_SIZE = int(profile.chunk_size)
    CHUNK_OVERLAP = int(profile.chunk_overlap)
    TOP_K_RETRIEVE = int(profile.top_k)


def get_provider_chain() -> list[ProviderConfig]:
    providers: list[ProviderConfig] = []
    if GEMINI_API_KEY:
        providers.append(
            ProviderConfig(
                name="gemini",
                kind="gemini",
                model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
                api_key=GEMINI_API_KEY,
            )
        )
    if GROQ_API_KEY:
        providers.append(
            ProviderConfig(
                name="groq",
                kind="openai-compatible",
                model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
                api_key=GROQ_API_KEY,
                base_url=_enforce_https(os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")),
            )
        )
    if OLLAMA_MODEL:
        providers.append(
            ProviderConfig(
                name="ollama",
                kind="openai-compatible",
                model=OLLAMA_MODEL,
                base_url=_enforce_https(OLLAMA_BASE_URL.rstrip("/") + "/v1"),
            )
        )
    return providers
