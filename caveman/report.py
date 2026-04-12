"""Token-savings report formatting."""

import tiktoken

_enc = tiktoken.get_encoding("o200k_base")


def count_tokens(text: str) -> int:
    """Count tokens using the GPT-4o tokenizer (o200k_base)."""
    return len(_enc.encode(text))


def token_savings(original: str, compressed: str) -> dict:
    """Return token-savings stats as a dict."""
    orig_tok = count_tokens(original)
    comp_tok = count_tokens(compressed)
    saved = orig_tok - comp_tok
    pct = int(saved / orig_tok * 100) if orig_tok > 0 else 0
    return {
        "original_tokens": orig_tok,
        "compressed_tokens": comp_tok,
        "saved_tokens": saved,
        "saved_pct": pct,
    }


def print_report(original: str, compressed: str) -> None:
    stats = token_savings(original, compressed)
    orig_tok = stats["original_tokens"]
    comp_tok = stats["compressed_tokens"]
    saved = stats["saved_tokens"]
    pct = stats["saved_pct"]

    _MAX = 60
    orig_display = original if len(original) <= _MAX else original[:_MAX] + "..."
    comp_display = compressed if len(compressed) <= _MAX else compressed[:_MAX] + "..."

    print(f"Original   ({orig_tok:3d} tok): {orig_display}")
    print(f"Compressed ({comp_tok:3d} tok): {comp_display}")
    if saved > 0:
        print(f"Saved: ~{saved} tokens ({pct}% reduction)")
    else:
        print("Saved: 0 tokens (no reduction)")
