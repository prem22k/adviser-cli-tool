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
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-mini").strip()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022").strip()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip()
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1").strip()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "").strip()
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "codestral-latest").strip()
MISTRAL_BASE_URL = os.getenv("MISTRAL_BASE_URL", "https://api.mistral.ai/v1").strip()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct").strip()
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").strip()

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY", "").strip()
TOGETHER_MODEL = os.getenv("TOGETHER_MODEL", "meta-llama/Llama-3.3-70b-instruct-turbo").strip()
TOGETHER_BASE_URL = os.getenv("TOGETHER_BASE_URL", "https://api.together.xyz/v1").strip()

FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY", "").strip()
FIREWORKS_MODEL = os.getenv("FIREWORKS_MODEL", "accounts/fireworks/models/llama-v3-70b-instruct").strip()
FIREWORKS_BASE_URL = os.getenv("FIREWORKS_BASE_URL", "https://api.fireworks.ai/inference/v1").strip()

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
AIRLLM_MODEL = os.getenv("AIRLLM_MODEL", "").strip()
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
    has_keys = any([
        GROQ_API_KEY,
        GEMINI_API_KEY,
        OPENAI_API_KEY,
        ANTHROPIC_API_KEY,
        DEEPSEEK_API_KEY,
        MISTRAL_API_KEY,
        OPENROUTER_API_KEY,
        TOGETHER_API_KEY,
        FIREWORKS_API_KEY,
        OLLAMA_MODEL,
        AIRLLM_MODEL,
    ])
    if not has_keys:
        raise RuntimeError("No API keys or local models configured. Set at least one API key or local model.")
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Configured DATA_PATH does not exist: {DATA_PATH}")


def apply_profile(profile: Any) -> None:
    global ADVISER_PERSONA
    global CHUNK_OVERLAP
    global CHUNK_SIZE
    global DATA_PATH
    global DB_PATH
    global TOP_K_RETRIEVE
    global GEMINI_MODEL
    global GROQ_MODEL
    global OPENAI_MODEL
    global ANTHROPIC_MODEL
    global DEEPSEEK_MODEL
    global MISTRAL_MODEL
    global OPENROUTER_MODEL
    global TOGETHER_MODEL
    global FIREWORKS_MODEL

    ADVISER_PERSONA = profile.persona
    DATA_PATH = Path(profile.data_path).expanduser()
    DB_PATH = Path(profile.db_path).expanduser()
    CHUNK_SIZE = int(profile.chunk_size)
    CHUNK_OVERLAP = int(profile.chunk_overlap)
    TOP_K_RETRIEVE = int(profile.top_k)

    if hasattr(profile, "gemini_model"):
        GEMINI_MODEL = profile.gemini_model
    if hasattr(profile, "groq_model"):
        GROQ_MODEL = profile.groq_model
    if hasattr(profile, "openai_model"):
        OPENAI_MODEL = profile.openai_model
    if hasattr(profile, "anthropic_model"):
        ANTHROPIC_MODEL = profile.anthropic_model
    if hasattr(profile, "deepseek_model"):
        DEEPSEEK_MODEL = profile.deepseek_model
    if hasattr(profile, "mistral_model"):
        MISTRAL_MODEL = profile.mistral_model
    if hasattr(profile, "openrouter_model"):
        OPENROUTER_MODEL = profile.openrouter_model
    if hasattr(profile, "together_model"):
        TOGETHER_MODEL = profile.together_model
    if hasattr(profile, "fireworks_model"):
        FIREWORKS_MODEL = profile.fireworks_model


def get_provider_chain() -> list[ProviderConfig]:
    providers: list[ProviderConfig] = []
    if GEMINI_API_KEY:
        providers.append(
            ProviderConfig(
                name="gemini",
                kind="gemini",
                model=GEMINI_MODEL,
                api_key=GEMINI_API_KEY,
            )
        )
    if ANTHROPIC_API_KEY:
        providers.append(
            ProviderConfig(
                name="anthropic",
                kind="anthropic",
                model=ANTHROPIC_MODEL,
                api_key=ANTHROPIC_API_KEY,
            )
        )
    if OPENAI_API_KEY:
        providers.append(
            ProviderConfig(
                name="openai",
                kind="openai-compatible",
                model=OPENAI_MODEL,
                api_key=OPENAI_API_KEY,
                base_url=_enforce_https(OPENAI_BASE_URL),
            )
        )
    if GROQ_API_KEY:
        providers.append(
            ProviderConfig(
                name="groq",
                kind="openai-compatible",
                model=GROQ_MODEL,
                api_key=GROQ_API_KEY,
                base_url=_enforce_https(os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")),
            )
        )
    if DEEPSEEK_API_KEY:
        providers.append(
            ProviderConfig(
                name="deepseek",
                kind="openai-compatible",
                model=DEEPSEEK_MODEL,
                api_key=DEEPSEEK_API_KEY,
                base_url=_enforce_https(DEEPSEEK_BASE_URL),
            )
        )
    if MISTRAL_API_KEY:
        providers.append(
            ProviderConfig(
                name="mistral",
                kind="openai-compatible",
                model=MISTRAL_MODEL,
                api_key=MISTRAL_API_KEY,
                base_url=_enforce_https(MISTRAL_BASE_URL),
            )
        )
    if OPENROUTER_API_KEY:
        providers.append(
            ProviderConfig(
                name="openrouter",
                kind="openai-compatible",
                model=OPENROUTER_MODEL,
                api_key=OPENROUTER_API_KEY,
                base_url=_enforce_https(OPENROUTER_BASE_URL),
            )
        )
    if TOGETHER_API_KEY:
        providers.append(
            ProviderConfig(
                name="together",
                kind="openai-compatible",
                model=TOGETHER_MODEL,
                api_key=TOGETHER_API_KEY,
                base_url=_enforce_https(TOGETHER_BASE_URL),
            )
        )
    if FIREWORKS_API_KEY:
        providers.append(
            ProviderConfig(
                name="fireworks",
                kind="openai-compatible",
                model=FIREWORKS_MODEL,
                api_key=FIREWORKS_API_KEY,
                base_url=_enforce_https(FIREWORKS_BASE_URL),
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
    if AIRLLM_MODEL:
        providers.append(
            ProviderConfig(
                name="airllm",
                kind="airllm",
                model=AIRLLM_MODEL,
            )
        )
    return providers
