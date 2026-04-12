"""spaCy-based NLP helpers.

spaCy and the English model are hard dependencies. On first use, if the model
is not yet installed, it is downloaded automatically (one-time, ~12 MB).
Subsequent runs load the cached model with no network activity.
"""

import re

_nlp = None
_matcher = None       # L1 filler matcher
_l2_matcher = None    # L2 phrase simplification matcher
_l2_replacements: dict[str, str] = {}  # label → replacement text
_ready: bool = False

# Plural abbreviations whose space-prefixed form costs more BPE tokens than
# the original word (e.g. " databases" 1 tok → " dbs" 2 tok).  Computed once
# at import time via tiktoken.
_L2_SPACE_LOSERS: frozenset[str] = frozenset()


def _build_space_losers() -> frozenset[str]:
    """Return the set of L2 abbreviation values that tokenize worse with a
    leading space than their source words."""
    import tiktoken  # noqa: PLC0415
    from .rules import LEVEL2_SUBS  # noqa: PLC0415

    enc = tiktoken.get_encoding("o200k_base")
    losers: set[str] = set()
    for word, abbrev in LEVEL2_SUBS.items():
        if len(enc.encode(" " + abbrev)) > len(enc.encode(" " + word)):
            losers.add(abbrev)
    return frozenset(losers)


_L2_SPACE_LOSERS = _build_space_losers()

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
# Level 2 — Matcher-based phrase simplification
#
# Unlike L1 (which removes spans), L2 replaces multi-word phrases with shorter
# equivalents.  Using spaCy Matcher patterns instead of regex lets us match on
# lemma and POS, catching inflected forms that regex misses:
#   "was able to", "will be able to", "depended on", "looked at", …
# ---------------------------------------------------------------------------

_L2_PHRASE_PATTERNS: list[tuple[str, list[dict], str]] = [
    # --- Obligation / ability (lemma-based — catches all inflections) ---
    # "is/was/will be/would be able to" → "can"
    ("L2_ABLE_TO", [
        {"POS": "AUX", "OP": "+"},
        {"LOWER": "able"},
        {"LOWER": "to"},
    ], "can"),
    # "needs/needed/needing to", "has/had/having to" → "must"
    ("L2_MUST", [
        {"LEMMA": {"IN": ["need", "have"]}, "POS": {"IN": ["VERB", "AUX"]}},
        {"LOWER": "to"},
    ], "must"),
    # --- Action verbs (lemma-based) ---
    # "take/took/taking a look at" → "check"
    ("L2_TAKE_LOOK_AT", [
        {"LEMMA": "take"},
        {"POS": "DET", "OP": "?"},
        {"LEMMA": "look"},
        {"LOWER": "at"},
    ], "check"),
    # "look/looks/looked/looking at" → "check"
    ("L2_LOOK_AT", [
        {"LEMMA": "look", "POS": "VERB"},
        {"LOWER": "at"},
    ], "check"),
    # "look/looks/looked/looking for" → "find"
    ("L2_LOOK_FOR", [
        {"LEMMA": "look", "POS": "VERB"},
        {"LOWER": "for"},
    ], "find"),
    # "make/makes/made/making sure" → "ensure"
    ("L2_MAKE_SURE", [
        {"LEMMA": "make"},
        {"LOWER": "sure"},
    ], "ensure"),
    # "depend/depends/depended/depending on" → "needs"
    ("L2_DEPEND_ON", [
        {"LEMMA": {"IN": ["depend", "rely"]}},
        {"LOWER": "on"},
    ], "needs"),
    # "not working / not functioning" → "broken"
    ("L2_NOT_WORKING", [
        {"LOWER": {"IN": ["not", "n't"]}},
        {"LEMMA": {"IN": ["work", "function"]}, "POS": "VERB"},
    ], "broken"),
    # --- Exact-match phrases (no inflection, but unified in one system) ---
    ("L2_IN_ORDER_TO", [
        {"LOWER": "in"},
        {"LOWER": "order"},
        {"LOWER": "to"},
    ], "to"),
    ("L2_WHETHER_OR_NOT", [
        {"LOWER": "whether"},
        {"LOWER": "or"},
        {"LOWER": "not"},
    ], "if"),
    ("L2_AS_WELL_AS", [
        {"LOWER": "as"},
        {"LOWER": "well"},
        {"LOWER": "as"},
    ], "and"),
    ("L2_IN_ADDITION_TO", [
        {"LOWER": "in"},
        {"LOWER": "addition"},
        {"LOWER": "to"},
    ], "and"),
    ("L2_AS_LONG_AS", [
        {"LOWER": "as"},
        {"LOWER": "long"},
        {"LOWER": "as"},
    ], "while"),
    ("L2_AS_SOON_AS", [
        {"LOWER": "as"},
        {"LOWER": "soon"},
        {"LOWER": "as"},
    ], "when"),
    ("L2_AS_A_RESULT", [
        {"LOWER": "as"},
        {"POS": "DET"},
        {"LOWER": "result"},
    ], "so"),
    ("L2_IN_OTHER_WORDS", [
        {"LOWER": "in"},
        {"LOWER": "other"},
        {"LOWER": "words"},
    ], "i.e."),
    ("L2_FOR_EXAMPLE", [
        {"LOWER": "for"},
        {"LOWER": {"IN": ["example", "instance"]}},
    ], "e.g."),
    ("L2_SUCH_AS", [
        {"LOWER": "such"},
        {"LOWER": "as"},
    ], "e.g."),
    ("L2_INSTEAD_OF", [
        {"LOWER": "instead"},
        {"LOWER": "of"},
    ], "not"),
    ("L2_SIMILAR_TO", [
        {"LOWER": "similar"},
        {"LOWER": "to"},
    ], "like"),
    ("L2_A_LOT_OF", [
        {"POS": "DET"},
        {"LOWER": "lot"},
        {"LOWER": "of"},
    ], "many"),
    ("L2_IN_CASE", [
        {"LOWER": "in"},
        {"LOWER": "case"},
    ], "if"),
    ("L2_DUE_TO", [
        {"LOWER": "due"},
        {"LOWER": "to"},
    ], "because"),
    ("L2_RIGHT_NOW", [
        {"LOWER": "right"},
        {"LOWER": "now"},
    ], "now"),
    ("L2_AT_THIS_POINT", [
        {"LOWER": "at"},
        {"LOWER": "this"},
        {"LOWER": "point"},
    ], "now"),
    ("L2_AT_LEAST", [
        {"LOWER": "at"},
        {"LOWER": "least"},
    ], "min"),
    ("L2_AT_MOST", [
        {"LOWER": "at"},
        {"LOWER": "most"},
    ], "max"),
]

# Filler adverb lemmas safe to remove when POS-tagged as ADV.
# POS gating prevents false positives (e.g. "rather" in "would rather").
_L2_FILLER_ADV_LEMMAS: frozenset[str] = frozenset({
    "very", "really", "quite", "rather",
    "currently", "actually",
    "certainly", "definitely",
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
    "string":      "NOUN",
    "value":       "NOUN",
    "values":      "NOUN",
    "source":      "NOUN",
    "token":       "NOUN",
    "instance":    "NOUN",
    "version":     "NOUN",
    "versions":    "NOUN",
    "channel":     "NOUN",
    "deployment":  "NOUN",
    "migration":   "NOUN",
    "embedding":   "NOUN",
    "vector":      "NOUN",
    "gradient":    "NOUN",
    "prediction":  "NOUN",
    "evaluation":  "NOUN",
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
    global _nlp, _matcher, _l2_matcher, _l2_replacements, _ready
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

    # L1 filler matcher
    _matcher = Matcher(_nlp.vocab)
    for label, pattern in _FILLER_PATTERNS:
        _matcher.add(label, [pattern])

    # L2 phrase simplification matcher
    _l2_matcher = Matcher(_nlp.vocab)
    for label, pattern, replacement in _L2_PHRASE_PATTERNS:
        _l2_matcher.add(label, [pattern])
        _l2_replacements[label] = replacement

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


def apply_level2_phrases_nlp(text: str) -> str:
    """Replace wordy multi-word phrases with concise equivalents using spaCy.

    Uses the Matcher with lemma / POS patterns so that inflected forms are
    caught automatically (e.g. "was able to", "depended on", "looked at").
    Longer matches take priority over shorter overlapping ones.
    """
    _setup()

    doc = _nlp(text)
    matches = _l2_matcher(doc)
    if not matches:
        return text

    # Build (start_char, end_char, replacement) tuples.
    # Prefer longer spans when matches overlap.
    spans: list[tuple[int, int, int, str]] = []  # (start, end, length, repl)
    for match_id, start, end in matches:
        label = _nlp.vocab.strings[match_id]
        repl = _l2_replacements[label]
        start_char = doc[start].idx
        end_tok = doc[end - 1]
        end_char = end_tok.idx + len(end_tok.text_with_ws)
        spans.append((start_char, end_char, end - start, repl))

    # Sort: longest span first, then by position — greedily accept non-overlapping
    spans.sort(key=lambda s: (-s[2], s[0]))
    accepted: list[tuple[int, int, str]] = []
    for start_c, end_c, _length, repl in spans:
        if not any(start_c < ae and end_c > as_ for as_, ae, _ in accepted):
            accepted.append((start_c, end_c, repl))
    accepted.sort()

    # Rebuild text with replacements
    parts: list[str] = []
    cursor = 0
    for start_c, end_c, repl in accepted:
        parts.append(text[cursor:start_c])
        parts.append(repl)
        # Preserve one trailing space if the original span had one
        if end_c <= len(text) and (end_c == len(text) or text[end_c - 1] == " "):
            parts.append(" ")
        cursor = end_c
    parts.append(text[cursor:])

    return re.sub(r"[ \t]+", " ", "".join(parts)).strip()


def apply_level2_nlp(text: str, subs: dict[str, str]) -> str:
    """POS-gated token removal and tech abbreviations.

    Single spaCy parse, four token-level operations:
    1. Remove "that" when used as relative pronoun or conjunction (PRON/SCONJ).
       Keeps demonstrative "that" (DET) — "use **that** function" is meaningful.
    2. Remove filler adverbs (ADV-tagged tokens whose lemma is in the filler set).
    3. Remove determiners (a, an, the, every, …).
    4. Apply single-word tech abbreviations with POS constraints.
    """
    _setup()

    doc = _nlp(text)
    parts: list[str] = []
    for token in doc:
        # --- "that" removal (relative pronoun / conjunction only) ---
        if token.lower_ == "that" and token.pos_ in {"PRON", "SCONJ"} \
                and "\x00" not in token.text:
            next_tok = doc[token.i + 1] if token.i + 1 < len(doc) else None
            # Keep if followed by contraction suffix ("that's")
            if next_tok and next_tok.text.startswith("'"):
                parts.append(token.text_with_ws)
                continue
            continue  # drop it

        # --- Filler adverb removal (POS-gated) ---
        if token.pos_ == "ADV" and token.lemma_ in _L2_FILLER_ADV_LEMMAS \
                and "\x00" not in token.text:
            continue  # drop the filler adverb

        # --- Determiner removal ---
        if token.pos_ == "DET" and "\x00" not in token.text:
            # Keep determiners adjacent to hyphens (e.g. "all-or-nothing")
            next_tok = doc[token.i + 1] if token.i + 1 < len(doc) else None
            prev_tok = doc[token.i - 1] if token.i > 0 else None
            if (next_tok and next_tok.text == "-") or (prev_tok and prev_tok.text == "-"):
                parts.append(token.text_with_ws)
                continue
            # Keep determiners followed by a contraction suffix ("that's")
            if next_tok and next_tok.text.startswith("'"):
                parts.append(token.text_with_ws)
                continue
            continue  # drop the determiner

        # --- Single-word tech abbreviations ---
        word_lower = token.lower_
        if word_lower in subs:
            constraint = LEVEL2_POS_CONSTRAINTS.get(word_lower)
            if constraint is None or token.pos_ == constraint:
                # Skip if the token is part of a hyphenated compound — the
                # abbreviation almost always costs more BPE tokens when glued
                # to a hyphen (e.g. "-service" 1 tok → "-svc" 2 tok).
                prev_tok = doc[token.i - 1] if token.i > 0 else None
                next_tok = doc[token.i + 1] if token.i + 1 < len(doc) else None
                if (prev_tok and prev_tok.text == "-") or (next_tok and next_tok.text == "-"):
                    parts.append(token.text_with_ws)
                    continue
                abbrev = subs[word_lower]
                # Skip plurals whose abbreviated form costs extra BPE tokens
                # (e.g. " databases" 1 tok → " dbs" 2 tok).
                if abbrev in _L2_SPACE_LOSERS:
                    parts.append(token.text_with_ws)
                    continue
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
            # Don't strip contraction suffixes ('s, 're, 've, 'll, 'd, 'm) —
            # they are morphologically bound to the previous word, and removing
            # them causes the host word to merge with the next token (no space).
            if token.text.startswith("'"):
                continue
            next_tok = doc[token.i + 1] if token.i + 1 < len(doc) else None
            prev_tok = doc[token.i - 1] if token.i > 0 else None
            # Don't strip host words followed by a contraction suffix —
            # removing "It" from "It's" would orphan "'s".
            if next_tok and next_tok.text.startswith("'"):
                continue
            # Don't strip tokens that are part of a hyphenated compound (e.g. "in-memory")
            if (next_tok and next_tok.text == "-") or (prev_tok and prev_tok.text == "-"):
                continue
            spans.append((token.idx, token.idx + len(token.text_with_ws)))

    return _remove_spans(text, spans) if spans else text
