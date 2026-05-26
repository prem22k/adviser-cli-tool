"""Rolling conversation memory for chat sessions."""

from __future__ import annotations


class ConversationMemory:
    def __init__(self, window_size: int) -> None:
        self.window_size = window_size
        self.messages: list[dict[str, str]] = []

    def add(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        limit = self.window_size * 2
        if limit > 0:
            self.messages = self.messages[-limit:]

    def clear(self) -> None:
        self.messages.clear()

    def get_messages(self, system_prompt: str, user_query: str, context: str) -> list[dict[str, str]]:
        content = (
            "Use the provided context to answer the user's question. "
            "If the answer is not in the context, say so plainly.\n\n"
            f"Context:\n{context}\n\nUser question:\n{user_query}"
        )
        return [{"role": "system", "content": system_prompt}, *self.messages, {"role": "user", "content": content}]
