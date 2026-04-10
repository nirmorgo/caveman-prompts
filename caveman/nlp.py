"""spaCy-based NLP helpers.

spaCy and the English model are hard dependencies. On first use, if the model
is not yet installed, it is downloaded automatically (one-time, ~12 MB).
Subsequent runs load the cached model with no network activity.
"""

import re

_nlp = None
_matcher = None
_ready: bool = False

# ---------------------------------------------------------------------------
# Level 1 — structural filler patterns
#
# Token patterns match on POS / lemma / lower, so a single rule covers all
# tense and surface-form variants instead of an exhaustive string list.
# ---------------------------------------------------------------------------

_FILLER_PATTERNS: list[tuple[str, list[dict]]] = [
    # "I was / had been wondering / hoping / thinking if / whether"
    ("POLITE_WONDER", [
        {"LOWER": "i"},
        {"POS": "AUX", "OP": "*"},
        {"LEMMA": {"IN": ["wonder", "hope", "think", "wish"]}, "POS": "VERB"},
        {"LOWER": {"IN": ["if", "whether", "that"]}, "OP": "?"},
    ]),
    # "I would / could / should like / want / need / love (you) to"
    ("POLITE_MODAL", [
        {"LOWER": "i"},
        {"POS": "AUX", "OP": "+"},
        {"LEMMA": {"IN": ["like", "want", "need", "love", "appreciate"]}},
        {"LOWER": "you", "OP": "?"},
        {"LOWER": "to", "OP": "?"},
    ]),
    # "Could / Would / Can / Will you (please)"
    ("MODAL_REQUEST", [
        {"LOWER": {"IN": ["could", "would", "can", "will"]}},
        {"LOWER": "you"},
        {"LOWER": "please", "OP": "?"},
    ]),
    # "you could / would / can (please)" — residue after opener is stripped
    ("YOU_MODAL", [
        {"LOWER": "you"},
        {"LOWER": {"IN": ["could", "would", "can", "will"]}},
        {"LOWER": "please", "OP": "?"},
    ]),
    # "I'm / I am trying / looking / attempting to"
    ("IM_TRYING", [
        {"LOWER": "i"},
        {"LOWER": {"IN": ["'m", "am"]}},
        {"LEMMA": {"IN": ["try", "look", "attempt", "seek"]}, "POS": "VERB"},
        {"LOWER": "to"},
    ]),
    # Greetings: "Hi", "Hello", "Hey" (optionally followed by punctuation)
    ("GREETING", [
        {"LOWER": {"IN": ["hi", "hello", "hey"]}},
        {"IS_PUNCT": True, "OP": "?"},
    ]),
    # "Thank you (in advance)" / "Thanks (in advance)"
    ("THANKS", [
        {"LEMMA": "thank"},
        {"LOWER": "you", "OP": "?"},
        {"LOWER": "in", "OP": "?"},
        {"LOWER": "advance", "OP": "?"},
    ]),
    # "feel free to"
    ("FEEL_FREE", [
        {"LOWER": "feel"},
        {"LOWER": "free"},
        {"LOWER": "to"},
    ]),
    # "don't hesitate to" (handles tokenised "do n't" and contracted "don't")
    ("DONT_HESITATE", [
        {"LOWER": {"IN": ["don't", "do"]}},
        {"LOWER": {"IN": ["n't", "not"]}, "OP": "?"},
        {"LOWER": "hesitate"},
        {"LOWER": "to"},
    ]),
    # "just to clarify / confirm / note / mention / add / check"
    # "just" is optional because _FILLER_WORDS strips it in Pass 1; position-gated at start
    ("JUST_TO_X", [
        {"LOWER": "just", "OP": "?"},
        {"LOWER": "to"},
        {"LEMMA": {"IN": ["clarify", "confirm", "note", "mention", "add", "check"]}},
    ]),
    # "as you (may / might / already) know"
    ("AS_YOU_KNOW", [
        {"LOWER": "as"},
        {"LOWER": "you"},
        {"LOWER": {"IN": ["may", "might", "already"]}, "OP": "?"},
        {"LOWER": "know"},
    ]),
    # "by the way"
    ("BY_THE_WAY", [
        {"LOWER": "by"},
        {"LOWER": "the"},
        {"LOWER": "way"},
    ]),
    # "for what it's worth"
    ("FWIW", [
        {"LOWER": "for"},
        {"LOWER": "what"},
        {"LOWER": {"IN": ["it's", "it"]}},
        {"LOWER": "'s", "OP": "?"},
        {"LOWER": "worth"},
    ]),
    # "needless to say"
    ("NEEDLESS_TO_SAY", [
        {"LOWER": "needless"},
        {"LOWER": "to"},
        {"LOWER": "say"},
    ]),
    # "just wondering / checking / confirming" (standalone); position-gated at start
    # Uses exact gerund forms (not lemma) to avoid matching imperatives like "Check ..."
    ("JUST_WONDERING", [
        {"LOWER": "just", "OP": "?"},
        {"LOWER": {"IN": ["wondering", "checking", "confirming", "verifying"]}},
    ]),
]

# Single-word fillers removed at the token level (always safe to strip in prompts)
# Patterns only valid at the start of a segment (after Pass 1 removes single-word fillers).
# Gated by token position so optional "just" doesn't cause false positives mid-sentence.
_START_ONLY_PATTERNS: frozenset[str] = frozenset({"JUST_TO_X", "JUST_WONDERING"})

_FILLER_WORDS: frozenset[str] = frozenset({
    "please", "kindly",
    "basically", "essentially", "honestly", "simply",
    "obviously", "clearly", "naturally",
    "just",
})

# ---------------------------------------------------------------------------
# Level 2 — POS constraints for single-word substitutions
#
# Maps word (lower) → expected spaCy POS tag. Substitution is skipped when
# the word's actual POS doesn't match, preventing false positives like
# "it functions correctly" → "it fns correctly".
# ---------------------------------------------------------------------------

LEVEL2_POS_CONSTRAINTS: dict[str, str] = {
    # Nouns only
    "function":    "NOUN",
    "functions":   "NOUN",
    "string":      "NOUN",
    "strings":     "NOUN",
    "value":       "NOUN",
    "values":      "NOUN",
    "source":      "NOUN",
    "token":       "NOUN",
    "tokens":      "NOUN",
    "instance":    "NOUN",
    "instances":   "NOUN",
    "version":     "NOUN",
    "versions":    "NOUN",
    "channel":     "NOUN",
    "channels":    "NOUN",
    "deployment":  "NOUN",
    "deployments": "NOUN",
    "migration":   "NOUN",
    "migrations":  "NOUN",
    "embedding":   "NOUN",
    "embeddings":  "NOUN",
    "vector":      "NOUN",
    "vectors":     "NOUN",
    "gradient":    "NOUN",
    "gradients":   "NOUN",
    "prediction":  "NOUN",
    "predictions": "NOUN",
    "evaluation":  "NOUN",
    "checkpoint":  "NOUN",
    "inference":   "NOUN",
    # Verbs only
    "build":         "VERB",
    "create":        "VERB",
    "delete":        "VERB",
    "remove":        "VERB",
    "update":        "VERB",
    "generate":      "VERB",
    "implement":     "VERB",
    "initialize":    "VERB",
    "execute":       "VERB",
    "optimize":      "VERB",
    "describe":      "VERB",
    "write":         "VERB",
    "obtain":        "VERB",
    "retrieve":      "VERB",
    "utilize":       "VERB",
    "using":         "VERB",
    "serialize":     "VERB",
    "deserialize":   "VERB",
    "encode":        "VERB",
    "decode":        "VERB",
    "validate":      "VERB",
    # "returns" → "->" only as verb ("returns a value"), not noun ("tax returns")
    "returns":       "VERB",
}


# ---------------------------------------------------------------------------
# Setup — lazy, but guaranteed to succeed (spaCy is a hard dependency)
# ---------------------------------------------------------------------------

def _setup() -> None:
    """Load the spaCy model, downloading it on first use if necessary."""
    global _nlp, _matcher, _ready
    if _ready:
        return

    import spacy  # noqa: PLC0415
    from spacy.matcher import Matcher  # noqa: PLC0415

    try:
        _nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])
    except OSError:
        print("Downloading language model (one-time setup, ~12 MB)...", flush=True)
        spacy.cli.download("en_core_web_sm")
        _nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])

    _matcher = Matcher(_nlp.vocab)
    for label, pattern in _FILLER_PATTERNS:
        _matcher.add(label, [pattern])

    _ready = True


def _remove_spans(text: str, char_spans: list[tuple[int, int]]) -> str:
    """Remove character ranges from *text*, collapsing leftover whitespace."""
    char_spans.sort()
    merged: list[list[int]] = []
    for start, end in char_spans:
        if merged and start < merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])

    result: list[str] = []
    cursor = 0
    for start, end in merged:
        result.append(text[cursor:start])
        cursor = end
    result.append(text[cursor:])
    return re.sub(r"[ \t]+", " ", "".join(result)).strip()


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def apply_level1_nlp(text: str) -> str:
    """Remove filler spans and single-word fillers using spaCy.

    Two-pass approach so that single-word fillers (basically, just, …) cannot
    interrupt structural patterns.  Pass 1 strips individual filler tokens.
    Pass 2 runs the Matcher on the cleaned text to catch multi-word patterns
    whose tokens may have been separated by a filler word in the original.
    """
    _setup()

    # --- Pass 1: remove single-word fillers ---
    doc = _nlp(text)
    spans: list[tuple[int, int]] = []
    for token in doc:
        if token.lower_ in _FILLER_WORDS:
            spans.append((token.idx, token.idx + len(token.text_with_ws)))

    intermediate = _remove_spans(text, spans) if spans else text
    if not intermediate:
        return ""

    # --- Pass 2: remove structural filler patterns from cleaned text ---
    doc2 = _nlp(intermediate)
    matches = _matcher(doc2)
    if not matches:
        return intermediate

    spans2: list[tuple[int, int]] = []
    for match_id, start, end in matches:
        name = _nlp.vocab.strings[match_id]
        if name in _START_ONLY_PATTERNS and start != 0:
            continue
        last_tok = doc2[end - 1]
        span_end = last_tok.idx + len(last_tok.text_with_ws)
        # Consume a trailing comma or semicolon left after the filler phrase
        if end < len(doc2) and doc2[end].text in {",", ";"}:
            comma = doc2[end]
            span_end = comma.idx + len(comma.text_with_ws)
        spans2.append((doc2[start].idx, span_end))

    return _remove_spans(intermediate, spans2)


def apply_level2_nlp(text: str, subs: dict[str, str]) -> str:
    """Apply word substitutions, skipping tokens whose POS doesn't match constraints."""
    _setup()

    doc = _nlp(text)
    parts: list[str] = []
    for token in doc:
        word_lower = token.lower_
        if word_lower in subs:
            constraint = LEVEL2_POS_CONSTRAINTS.get(word_lower)
            if constraint is None or token.pos_ == constraint:
                abbrev = subs[word_lower]
                # Preserve original capitalisation
                if token.text[0].isupper() and abbrev[0].islower():
                    abbrev = abbrev[0].upper() + abbrev[1:]
                parts.append(abbrev + token.whitespace_)
            else:
                parts.append(token.text_with_ws)
        else:
            parts.append(token.text_with_ws)

    return "".join(parts)


def apply_level3_nlp(text: str, skip_lower: frozenset[str] = frozenset()) -> str:
    """Remove function words by POS tag rather than an enumerated list.

    Removes all tokens whose POS is in {DET, AUX, PRON, ADP}, which covers
    every determiner, auxiliary verb, pronoun, and preposition — including
    words the static frozenset missed (toward, alongside, throughout, …).
    Filler adverbs are handled separately by the remaining LEVEL3_REMOVALS regex.

    Note: PART is intentionally excluded — it covers "not"/"n't" (negation)
    and infinitive "to", both of which carry meaning.

    skip_lower: token lower-forms that should never be removed even if their
    POS matches (used to protect L3 word-replacement outputs like "w/o", "no").
    """
    _setup()

    doc = _nlp(text)
    spans: list[tuple[int, int]] = []
    for token in doc:
        if token.pos_ in {"DET", "AUX", "PRON", "ADP"} and token.lower_ not in skip_lower \
                and "\x00" not in token.text:
            # Don't strip tokens that are part of a hyphenated compound (e.g. "in-memory")
            next_tok = doc[token.i + 1] if token.i + 1 < len(doc) else None
            prev_tok = doc[token.i - 1] if token.i > 0 else None
            if (next_tok and next_tok.text == "-") or (prev_tok and prev_tok.text == "-"):
                continue
            spans.append((token.idx, token.idx + len(token.text_with_ws)))

    return _remove_spans(text, spans) if spans else text
