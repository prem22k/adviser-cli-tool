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
        # Answers are rendered as Markdown in a terminal, which shows LaTeX as raw source.
        system = (
            f"{system_prompt}\n\nFormat answers as plain Markdown. Never use LaTeX or math markup "
            "(no \\frac, \\text, \\[ \\]); write formulas and calculations in plain text, e.g. 1,200 / 300 = 4."
        )
        return [{"role": "system", "content": system}, *self.messages, {"role": "user", "content": content}]
