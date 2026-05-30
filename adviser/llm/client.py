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
            
            from rich.console import Group
            from rich.live import Live
            from rich.markdown import Markdown
            from rich.spinner import Spinner
            from rich.text import Text

            chunks: list[str] = []
            # Latency spinner anchored to a layout container using the dot animation and elegant ellipses
            spinner = Spinner("dots", text=Text(" • • •", style="dim"), style="dim")
            
            with Live(spinner, console=console, auto_refresh=True, refresh_per_second=10) as live:
                first = True
                for part in stream:
                    token = part.choices[0].delta.content or ""
                    if token:
                        if first:
                            first = False
                        chunks.append(token)
                        accumulated = "".join(chunks)
                        live.update(Group(Markdown(accumulated)), refresh=True)
                        
            return "".join(chunks)
        except (RateLimitError, APIConnectionError, APITimeoutError):
            raise

    def _to_gemini_chat(self, messages: list[dict[str, str]]) -> tuple[list[dict[str, Any]], str]:
        system_prompt = ""
        history: list[dict[str, Any]] = []
        pending_user_parts: list[str] = []

        for message in messages:
            role = message["role"]
            content = message["content"].strip()
            if not content:
                continue

            if role == "system":
                system_prompt = content
                continue

            if role == "assistant":
                history.append({"role": "model", "parts": [content]})
                continue

            if not pending_user_parts and system_prompt:
                pending_user_parts.append(system_prompt)
                system_prompt = ""
            pending_user_parts.append(content)
            history.append({"role": "user", "parts": ["\n\n".join(pending_user_parts)]})
            pending_user_parts = []

        if not history:
            initial = system_prompt or "Hello."
            history.append({"role": "user", "parts": [initial]})
            return history[:-1], history[-1]["parts"][0]

        last_message = history[-1]
        if last_message["role"] != "user":
            final_user_message = system_prompt or "Continue."
            return history, final_user_message

        return history[:-1], str(last_message["parts"][0])

    def _call_gemini(self, provider: Any, messages: list[dict[str, str]]) -> str:
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise RuntimeError("The google-generativeai package is required for Gemini providers.") from exc

        genai.configure(api_key=provider.api_key)
        model = genai.GenerativeModel(model_name=provider.model)
        history, prompt = self._to_gemini_chat(messages)
        chat = model.start_chat(history=history)
        
        try:
            response = chat.send_message(prompt, stream=True)
            
            from rich.console import Group
            from rich.live import Live
            from rich.markdown import Markdown
            from rich.spinner import Spinner
            from rich.text import Text

            chunks: list[str] = []
            # Latency spinner anchored to a layout container using the dot animation and elegant ellipses
            spinner = Spinner("dots", text=Text(" • • •", style="dim"), style="dim")
            
            with Live(spinner, console=console, auto_refresh=True, refresh_per_second=10) as live:
                first = True
                for chunk in response:
                    token = getattr(chunk, "text", "") or ""
                    if token:
                        if first:
                            first = False
                        chunks.append(token)
                        accumulated = "".join(chunks)
                        live.update(Group(Markdown(accumulated)), refresh=True)
                        
            return "".join(chunks)
        except Exception:
            raise

    def chat(self, messages: list[dict[str, str]]) -> str:
        try:
            from openai import APIConnectionError, APITimeoutError, RateLimitError
        except ImportError as exc:
            raise RuntimeError("The openai package is required for chat execution.") from exc

        try:
            import google.api_core.exceptions as google_exceptions
        except ImportError:
            google_exceptions = None

        retryable_errors: tuple[type[BaseException], ...] = (
            RateLimitError,
            APIConnectionError,
            APITimeoutError,
        )
        if google_exceptions is not None:
            retryable_errors = retryable_errors + (
                google_exceptions.TooManyRequests,
                google_exceptions.ServiceUnavailable,
                google_exceptions.DeadlineExceeded,
                google_exceptions.GoogleAPICallError,
            )

        available = self.circuit_breaker.available_providers(self.providers)
        if not available:
            raise RuntimeError("No healthy providers available. Wait for cooldown or reconfigure Adviser.")

        last_error: Exception | None = None
        for provider in available:
            try:
                if provider.kind == "gemini":
                    return self._call_gemini(provider, messages)
                if provider.kind == "airllm":
                    from adviser.llm.airllm_provider import generate_chat
                    answer = generate_chat(provider.model, messages)
                    console.print(answer)
                    return answer
                return self._call_openai_compatible(provider, messages)
            except retryable_errors as exc:
                last_error = exc
                self.circuit_breaker.mark_failed(provider.name, str(exc))
                console.print(
                    f"[yellow]Provider {provider.name} failed, trying next provider:[/yellow] {exc}"
                )
            except Exception:
                raise
        raise RuntimeError("All configured providers failed.") from last_error
