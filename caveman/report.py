"""Token-savings report formatting."""


def count_tokens(text: str) -> int:
    """Rough token estimate: ~4 characters per token (OpenAI heuristic)."""
    return max(1, len(text) // 4)


def print_report(original: str, compressed: str) -> None:
    orig_tok = count_tokens(original)
    comp_tok = count_tokens(compressed)
    saved = orig_tok - comp_tok
    pct = int(saved / orig_tok * 100) if orig_tok > 0 else 0

    _MAX = 60
    orig_display = original if len(original) <= _MAX else original[:_MAX] + "..."
    comp_display = compressed if len(compressed) <= _MAX else compressed[:_MAX] + "..."

    print(f"Original   ({orig_tok:3d} tok): {orig_display}")
    print(f"Compressed ({comp_tok:3d} tok): {comp_display}")
    if saved > 0:
        print(f"Saved: ~{saved} tokens ({pct}% reduction)")
    else:
        print("Saved: 0 tokens (no reduction)")
