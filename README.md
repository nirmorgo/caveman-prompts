# caveman-prompts 🦴

> *"Me have big brain idea. Token cost money. Word cost token. Less word = less money. UGH."*

![caveman discovers fire](https://media.giphy.com/media/l0HlBO7eyXzSZkJri/giphy.gif)

---

## What Is This?

Caveman discover fire. Caveman discover wheel. Now caveman discover that long prompt cost many token and token cost many dollar.

**That's this library.**

`caveman-prompts` compresses your verbose, politeness-laden, filler-stuffed LLM prompts down to the raw semantic core — **without losing meaning**. You feed it *"Could you please be so kind as to perhaps write a function that returns a list of integers?"* and it grunts back *"make fn -> list ints?"*

Claude understands. Tokens saved. Wallet happy. UGH.

---

## Why Should Me Care?

- **LLM APIs charge per token.** Your polite preambles cost real money.
- **Shorter prompts = faster responses.** The model doesn't need your "I was wondering if maybe..."
- **Caveman-tested, mammoth-approved.** If a hominid with a rock can express intent, so can your prompts.

---

## Install

```bash
pip install caveman-prompts
```

Or, if you are caveman:

```bash
pip get thing
```

---

## The Three Levels of Grunting

### Level 1 — Polite Caveman

Strips filler phrases and pleasantries. Still uses full words like a civilized hominid.

```python
from caveman import CavemanCompressor

c = CavemanCompressor(level=1)
c.compress("Could you please write a function that returns a list?")
# -> "write a function that returns a list?"
```

*You: Can you please help me?*
*Level 1: Help me?*

Tribe elders nod in approval.

---

### Level 2 — Default Caveman (Recommended)

Abbreviates tech jargon. `function` → `fn`. `database` → `db`. `returns` → `->`. The whole vocabulary of a senior engineer who has stopped caring about newcomers.

```python
c = CavemanCompressor(level=2)
c.compress("Can you please write a function that returns a list?")
# -> "make fn -> a list?"
```

This is the sweet spot. A senior engineer who has transcended verbosity. A caveman who has tasted the mammoth of efficiency and never looked back.

![caveman nod](https://media.giphy.com/media/l0HlBO7eyXzSZkJri/giphy.gif)

---

### Level 3 — Full Caveman Mode 🪨

Articles? Gone. Pronouns? Banished to the shadow realm. Connectives replaced with symbols. This is the linguistic equivalent of a caveman painting on a cave wall.

```python
c = CavemanCompressor(level=3)
c.compress("Can you please write a function that returns a list?")
# -> "make fn -> list?"
```

| Human says | Caveman says |
| --- | --- |
| `and` | `+` |
| `or` | `\|` |
| `with` | `w/` |
| `without` | `w/o` |
| `because` | `bc` |
| `the`, `a`, `an` | *(silence)* |
| `in order to` | `->` |
| `for example` | `eg` |

Level 3 caveman doesn't acknowledge your pronouns. Caveman only sees the concept.

---

## Usage

### Basic Compression

```python
from caveman import CavemanCompressor

c = CavemanCompressor(level=2)
result = c.compress("Can you please write a function that returns a list of integers?")
print(result)
# -> make fn -> list ints?
```

### See the Token Savings Report

```python
c.report("Can you please write a function that returns a list of integers?")
```

Prints a breakdown of how many tokens you clubbed to death. Very satisfying.

### Chain It Like a Caveman Chief

```python
result = (
    CavemanCompressor()
    .set_level(3)
    .add_rule("utilize", "use")
    .compress("Please utilize the database to store the configuration variables")
)
# -> use db store config vars
```

### Sacred Words — Protect the Mammoth

Some words must not be touched. Class names. API keys. The name of your firstborn. Mark them sacred:

```python
c = CavemanCompressor(level=3).add_sacred("MyClassName")
c.compress("Please refactor MyClassName to use the database")
# -> refactor MyClassName use db
```

`MyClassName` survives the compression ice age unscathed.

### Custom Rules

```python
c = CavemanCompressor().add_rule("grok", "understand")
```

Teach the caveman new words. Very exciting for everyone involved.

### Code Blocks Are Preserved

Your actual code is sacred. Caveman is smart enough to leave triple-backtick blocks alone:

```python
prompt = """
Can you please refactor this function:

    ```python
    def process(items):
        return [x for x in items if x is not None]
    ```
"""
c = CavemanCompressor(level=3)
print(c.compress(prompt))
# -> refactor fn:
# [code block untouched]
```

Caveman respects the sacred fire of triple backticks.

---

## Real-World Example

**Original prompt:**
> *"Can you please write an asynchronous function that retrieves all user records from the database and returns them as a list of objects, and make sure it handles errors properly."*

**Level 1** — filler stripped, full words kept:
> *"write an asynchronous function that retrieves all user records from the database and returns them as a list of objects, and make sure it handles errors properly."*

**Level 2** — tech jargon abbreviated:
> *"make an async fn that retrieves all user records from the db and -> them as a list of objs, and make sure it handles errs properly."*

**Level 3** — full caveman. articles, pronouns, auxiliaries gone:
> *"make async fn retrieves all user records db + -> list objs, + ensure handles errs properly."*

Claude still understands. Your AWS bill weeps slightly less. Caveman grunt with satisfaction.

![money saved](https://media.giphy.com/media/3o7TKtnuHOHHUjR38Y/giphy.gif)

---

## API Reference

### `CavemanCompressor(level=2)`

| Method | What It Does |
| --- | --- |
| `.compress(text)` | Returns compressed string. Me use this most. |
| `.report(text)` | Prints token savings breakdown. Very pretty. |
| `.set_level(n)` | Change grunt intensity (1–3). Chainable. |
| `.add_sacred(word)` | Protect word from compression forever. |
| `.add_rule(from, to)` | Add custom substitution. Teach new word. |

---

## FAQ

**Q: Will this break my prompts?**
A: Level 1 and 2 — no. Level 3 — Claude handles it fine. We tested. Claude smart.

**Q: What about punctuation and newlines?**
A: Preserved. Caveman respects structure. Caveman not animal.

**Q: Why is it called caveman-prompts?**
A: Because the goal is maximum meaning with minimum words. Also because *"Unga bunga compress token"* was already taken as a PyPI name. (Actually it wasn't. We just liked caveman.)

---

## Contributing

Found a word that should be removed? A phrase that should be shortened? Submit a PR.

Or just grunt in the issues tab. We'll figure it out.

---

*Made with ❤️ and very few unnecessary words.*

*UGH.*
