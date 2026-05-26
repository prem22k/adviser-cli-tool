"""Provider-aware LLM client with failover and streaming."""

from __future__ import annotations

from typing import Any

from rich.console import Console

from adviser.config import settings
from adviser.llm.router import CircuitBreaker

console = Console()


class LLMClient:
    def __init__(self, providers: list[Any] | None = None) -> None:
        self.providers = providers or settings.get_provider_chain()
        self.circuit_breaker = CircuitBreaker(self.providers)

    @property
    def primary_provider_name(self) -> str:
        if not self.providers:
            return "none"
        return self.providers[0].name

    def _call_openai_compatible(self, provider: Any, messages: list[dict[str, str]]) -> str:
        try:
            from openai import APIConnectionError, APITimeoutError, OpenAI, RateLimitError
        except ImportError as exc:
            raise RuntimeError("The openai package is required for Groq and Ollama providers.") from exc

        client = OpenAI(
            api_key=provider.api_key or "ollama",
            base_url=provider.base_url,
        )
        try:
            stream = client.chat.completions.create(
                model=provider.model,
                messages=messages,
                temperature=0.2,
                stream=True,
            )
            chunks: list[str] = []
            for part in stream:
                token = part.choices[0].delta.content or ""
                if token:
                    console.print(token, style="bold green", end="")
                    chunks.append(token)
            console.print()
            return "".join(chunks)
        except (RateLimitError, APIConnectionError, APITimeoutError):
            raise

    def _to_gemini_contents(self, messages: list[dict[str, str]]) -> list[dict[str, Any]]:
        system_prompt = ""
        contents: list[dict[str, Any]] = []
        for message in messages:
            role = message["role"]
            content = message["content"]
            if role == "system":
                system_prompt = content.strip()
                continue
            mapped_role = "model" if role == "assistant" else "user"
            if mapped_role == "user" and system_prompt:
                content = f"{system_prompt}\n\n{content}".strip()
                system_prompt = ""
            contents.append({"role": mapped_role, "parts": [content]})
        if system_prompt and not contents:
            contents.append({"role": "user", "parts": [system_prompt]})
        return contents

    def _call_gemini(self, provider: Any, messages: list[dict[str, str]]) -> str:
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise RuntimeError("The google-generativeai package is required for Gemini providers.") from exc

        genai.configure(api_key=provider.api_key)
        model = genai.GenerativeModel(model_name=provider.model)
        response = model.generate_content(self._to_gemini_contents(messages), stream=True)
        chunks: list[str] = []
        for chunk in response:
            token = getattr(chunk, "text", "") or ""
            if token:
                console.print(token, style="bold green", end="")
                chunks.append(token)
        console.print()
        return "".join(chunks)

    def chat(self, messages: list[dict[str, str]]) -> str:
        available = self.circuit_breaker.available_providers(self.providers)
        if not available:
            raise RuntimeError("No healthy providers available. Wait for cooldown or reconfigure Adviser.")

        last_error: Exception | None = None
        for provider in available:
            try:
                if provider.kind == "gemini":
                    return self._call_gemini(provider, messages)
                return self._call_openai_compatible(provider, messages)
            except Exception as exc:
                last_error = exc
                self.circuit_breaker.mark_failed(provider.name, str(exc))
                console.print(
                    f"[yellow]Provider {provider.name} failed, trying next provider:[/yellow] {exc}"
                )
        raise RuntimeError("All configured providers failed.") from last_error
