# caveman-prompts 🦴

> *"Me have big brain idea. Token cost money. Word cost token. Less word = less money. UGH."*

```text
        ___
       (o o)    <-- caveman
        ) (
    ___|___|___
   /   _____   \    *bonk bonk*
  /   /TOKEN\   \       O
 /   /  $$$$  \  \     /|\ 
/___/___________\___\  / \
```

---

## What Is This?

Caveman discover fire. Caveman discover wheel. Now caveman discover that long prompt cost many token and token cost many dollar.

You give Claude big wordy prompt. Claude understand. But you pay many token. Why? Word like "could you please be so kind as to" mean nothing. Claude no need. Caveman no need. Token wasted. Wallet cry.

**This library fix. Me compress. Claude still understand. You save money. UGH.**

You feed it:

> *"Could you please be so kind as to perhaps write a function that returns a list of integers?"*

It grunt back:

> *"make fn -> list ints?"*

Same meaning. Fewer token. Caveman win.

---

## Why Me Use?

```text
  💰💰                  <-- your wallet without caveman-prompts
     /    \
    | 😭  |
     \    /

  💰💰💰💰💰💰💰💰💰💰   <-- your wallet with caveman-prompts
     /    \
    | 😄  |
     \    /
```

- **Token cost money.** Polite filler burn coin for nothing.
- **Short prompt = fast answer.** Claude no need your "I was wondering if maybe..."
- **Caveman-tested, mammoth-approved.** If hominid with rock can express intent, your prompt can too.

---

## Me Install

```bash
git clone https://github.com/nirmorgo/caveman-prompts.git
cd caveman-prompts
pip install -e .
```

---

## Three Level Of Grunt

### Level 1 — Polite Caveman

Strip filler. Strip pleasantry. Keep full word. Caveman still wear fur but no say "could you please."

```text
    ___
   (^ ^)   me civilized
    ) (    me just remove
   /| |\   unnecessary greeting
  /  |  \
```

```python
from caveman import CavemanCompressor

c = CavemanCompressor(level=1)
c.compress("Could you please write a function that returns a list?")
# -> "write a function that returns a list?"
```

*You say: Can you please help me?*
*Level 1 say: Help me?*

Tribe elder nod. Good enough.

---

### Level 2 — Default Caveman (Me Recommend)

Now caveman also shrink tech word. `function` become `fn`. `database` become `db`. `returns` become `->`. Caveman know code. Caveman just no waste syllable.

```text
    ___
   (- -)   function?  fn!
    ) (    database?  db!
  __|_|__  integer?   int!
 /  | |  \
```

```python
c = CavemanCompressor(level=2)
c.compress("Can you please write a function that returns a list?")
# -> "make fn -> a list?"
```

This sweet spot. Use this. Claude understand. Token shrink. Life good.

---

### Level 3 — Full Caveman Mode 🪨

Article? Gone. Pronoun? Gone. Auxiliary verb? Gone. Connective become symbol. This cave painting. This pure intent.

```text
  o
 /|    <-- all caveman need
 |
/ \
```

```python
c = CavemanCompressor(level=3)
c.compress("Can you please write a function that returns a list?")
# -> "make fn -> list?"
```

| You say | Caveman say |
| --- | --- |
| `and` | `+` |
| `or` | `\|` |
| `with` | `w/` |
| `without` | `w/o` |
| `because` | `bc` |
| `the`, `a`, `an` | *(silence)* |
| `in order to` | `->` |
| `for example` | `eg` |

Level 3 no care about pronoun. Level 3 only see concept.

---

## Me Use It

### Basic Squish

```python
from caveman import CavemanCompressor

c = CavemanCompressor(level=2)
result = c.compress("Can you please write a function that returns a list of integers?")
print(result)
# -> make fn -> list ints?
```

### See How Many Token Me Save

```python
c.report("Can you please write a function that returns a list of integers?")
```

Print breakdown. Show token before, token after. Very satisfying. Like after big hunt.

### Chain Many Thing Together

```python
result = (
    CavemanCompressor()
    .set_level(3)
    .add_rule("utilize", "use")
    .compress("Please utilize the database to store the configuration variables")
)
# -> use db store config vars
```

### Sacred Word — Caveman No Touch

Some word must stay. Class name. API name. Firstborn name. Mark sacred. Caveman respect.

```text
   /\___/\
  ( 0   0 )  <-- sacred mammoth
  (  ___  )      caveman no
   \_____/       touch him
   || | ||
   || | ||
```

```python
c = CavemanCompressor(level=3).add_sacred("MyClassName")
c.compress("Please refactor MyClassName to use the database")
# -> refactor MyClassName use db
```

`MyClassName` survive ice age. Unchanged. Protected.

### Teach New Word

```python
c = CavemanCompressor().add_rule("grok", "understand")
```

Caveman learn. Caveman grow.

### Code Block Safe

Caveman smart. Caveman no touch code block. Triple backtick = sacred fire.

```text
      )
    )  )
   ) ) )        <-- sacred fire
  (((((((
   |   |
   |   |
```

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

---

## Real Example — Me Show All Level

```text
  BEFORE:  ████████████████████████  76 tokens  😰
  LEVEL 1: ████████████████          52 tokens  😐
  LEVEL 2: ████████████              38 tokens  🙂
  LEVEL 3: ███████                   24 tokens  😎
```

**Original (many word, many token):**
> *"Can you please write an asynchronous function that retrieves all user records from the database and returns them as a list of objects, and make sure it handles errors properly."*

**Level 1** — filler gone, word still big:
> *"write an asynchronous function that retrieves all user records from the database and returns them as a list of objects, and make sure it handles errors properly."*

**Level 2** — tech word shrink:
> *"make an async fn that retrieves all user records from the db and -> them as a list of objs, and make sure it handles errs properly."*

**Level 3** — full caveman, only meaning survive:
> *"make async fn retrieves all user records db + -> list objs, + ensure handles errs properly."*

Claude still understand. AWS bill weep less. Caveman grunt with satisfaction.

---

## Caveman API Rock

### `CavemanCompressor(level=2)`

| Method | What Do |
| --- | --- |
| `.compress(text)` | Squish prompt. Return small version. |
| `.report(text)` | Show token savings. Print pretty. |
| `.set_level(n)` | Change grunt power (1–3). Chain ok. |
| `.add_sacred(word)` | Protect word forever. Caveman no touch. |
| `.add_rule(from, to)` | Teach new substitution. Caveman learn. |

---

## Question Caveman Get A Lot

**Q: This break prompt?**
A: Level 1, 2 — no. Level 3 — Claude handle fine. Me test. Claude smart.

**Q: Punctuation survive?**
A: Yes. Newline survive. Caveman respect structure. Caveman not animal.

**Q: Why called caveman-prompts?**
A: Maximum meaning. Minimum word. Also caveman funny. UGH.

---

## Me Contribute?

```text
    ___
   (o O)  <-- caveman see bug
    ) (
   /| |\   "this word not
  /  |  \   need remove??
            ME FIX. PR NOW."
```

Find word that should go? Phrase that should shrink? Submit PR.

Or grunt in issue tab. Me figure out.

---

*Made w/ few word. Much meaning. UGH.*
