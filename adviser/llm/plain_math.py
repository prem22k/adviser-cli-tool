"""Turn LaTeX math in model answers into plain text for terminal display.

Rich renders answers as Markdown, which shows LaTeX source verbatim (``\\frac{a}{b}``,
``\\text{...}``). Some models use it for any calculation even when told not to, so the
common constructs are rewritten here. Fenced and inline code are left untouched.
"""

from __future__ import annotations

import re

_CODE = re.compile(r"(```.*?(?:```|$)|`[^`\n]*`)", re.DOTALL)
_TEXT = re.compile(r"\\(?:text|mathrm|textbf|mathbf|operatorname)\{([^{}]*)\}")
_FRAC = re.compile(r"\\[dt]?frac\{([^{}]*)\}\{([^{}]*)\}")
_SYMBOLS = {
    r"\times": "×", r"\approx": "≈", r"\cdot": "·", r"\div": "÷", r"\pm": "±",
    r"\leq": "≤", r"\geq": "≥", r"\le": "≤", r"\ge": "≥", r"\neq": "≠",
    r"\%": "%", r"\$": "$", r"\left": "", r"\right": "",
}
_SPACES = re.compile(r"\\[,;:! ]")
_DELIMS = re.compile(r"\\\[|\\\]|\\\(|\\\)|\$\$")


def _plain(segment: str) -> str:
    if "\\" not in segment and "$$" not in segment:
        return segment
    for pattern, repl in ((_TEXT, r"\1"), (_FRAC, r"(\1) / (\2)")):
        previous = None
        while previous != segment:
            previous, segment = segment, pattern.sub(repl, segment)
    for latex, plain in sorted(_SYMBOLS.items(), key=lambda kv: -len(kv[0])):
        segment = re.sub(re.escape(latex) + r"(?![A-Za-z])", plain, segment)
    segment = _SPACES.sub(" ", segment)
    return _DELIMS.sub("", segment)


def strip_latex(text: str) -> str:
    """Rewrite LaTeX math outside code spans/blocks as readable plain text."""
    parts = _CODE.split(text)
    return "".join(part if i % 2 else _plain(part) for i, part in enumerate(parts))
