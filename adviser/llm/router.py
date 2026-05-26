"""Circuit breaker utilities for provider failover."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ProviderState:
    name: str
    failed_at: float | None = None
    failure_reason: str | None = None
    cooldown_seconds: int = 300


class CircuitBreaker:
    def __init__(self, providers: list[Any]) -> None:
        self.states = {
            provider.name: ProviderState(name=provider.name)
            for provider in providers
        }

    def is_available(self, provider_name: str) -> bool:
        state = self.states.get(provider_name)
        if state is None or state.failed_at is None:
            return True
        return (time.time() - state.failed_at) >= state.cooldown_seconds

    def mark_failed(self, provider_name: str, reason: str) -> None:
        state = self.states.setdefault(provider_name, ProviderState(name=provider_name))
        state.failed_at = time.time()
        state.failure_reason = reason

    def available_providers(self, providers: list[Any]) -> list[Any]:
        return [provider for provider in providers if self.is_available(provider.name)]
