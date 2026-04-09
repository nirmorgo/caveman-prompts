"""Sacred content guard — protect segments that must never be compressed."""

import re

# Patterns tried in order; first match at each position wins (combined with |).
# More specific / longer patterns come before shorter ones.
_BUILTIN_PATTERNS = [
    # Fenced code blocks (multiline)
    r'```[\s\S]*?```',
    # Inline code
    r'`[^`\n]+`',
    # URLs
    r'https?://\S+',
    # File paths: ./foo, ../foo, /absolute/path
    r'\.\.?/\S+|(?:/\w[\w./\-]*)',
    # Double-quoted strings
    r'"[^"]*"',
    # Single-quoted strings
    r"'[^']*'",
    # Numbers (int or float)
    r'\b\d+(?:\.\d+)?\b',
    # snake_case identifiers (contain at least one underscore)
    r'\b\w+_\w+\b',
    # PascalCase / UpperCamelCase (two or more TitleCase segments)
    r'\b(?:[A-Z][a-z0-9]+){2,}\b',
    # lowerCamelCase (lowercase start, at least one internal uppercase)
    r'\b[a-z]+(?:[A-Z][a-z0-9]+)+\b',
    # ALL_CAPS abbreviations (e.g. API, URL, GPT4)
    r'\b[A-Z]{2,}\d*\b',
]


def build_sacred_regex(extra_words: list[str]) -> re.Pattern:
    """Return a compiled regex covering builtin patterns + user sacred words."""
    patterns = list(_BUILTIN_PATTERNS)
    for word in sorted(extra_words, key=len, reverse=True):
        patterns.append(re.escape(word))
    combined = "|".join(f"(?:{p})" for p in patterns)
    return re.compile(combined, re.DOTALL)


def protect(text: str, sacred_regex: re.Pattern) -> tuple[str, dict[str, str]]:
    """Replace all sacred segments with unique null-byte-fenced placeholders."""
    placeholders: dict[str, str] = {}
    counter = 0

    def replacer(m: re.Match) -> str:
        nonlocal counter
        key = f"\x00S{counter}\x00"
        placeholders[key] = m.group(0)
        counter += 1
        return key

    protected = sacred_regex.sub(replacer, text)
    return protected, placeholders


def restore(text: str, placeholders: dict[str, str]) -> str:
    """Swap placeholders back for their original sacred content."""
    for key, value in placeholders.items():
        text = text.replace(key, value)
    return text
