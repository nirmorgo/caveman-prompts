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

## Three Level Of Grunt

### Level 1 — Polite Caveman

Strip filler. Strip pleasantry. Keep full word. Caveman still wear fur but no say "could you please."

Caveman now use brain (spaCy). Understand pattern. Not just word list. Strip greeting, polite opener, filler word, thanks — all gone.

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
c.compress(
    "Hi! I was basically wondering if you could help me debug this function. "
    "Just to clarify, it's not returning the correct values from the database. "
    "Thanks in advance!"
)
# -> "help me debug this function. it's not returning the correct values from the database."
```

Greeting gone. "I was basically wondering if you could" gone. "Just to clarify," gone. "Thanks in advance!" gone. Only meaning survive.

*You say: Hi! I was basically wondering if you could help me. Thanks in advance!*
*Level 1 say: help me.*

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
| `the`, `a`, `an` | *(silence)* |
| `it`, `they`, `we` | *(silence)* |
| `without` | `w/o` |
| `because` | `bc` |
| `in order to` | `->` |
| `for example` | `eg` |
| `depends on` | `needs` |
| `not working` | `broken` |
| `null` / `undefined` | `nil` |
| `doesn't` / `can't` | `no` |
| `isn't` / `aren't` | `not` |

Level 3 no care about pronoun. Level 3 only see concept.

---

## See What Happen — Real Examples

**1. Filler-heavy prompt** — greeting, polite opener, thanks all stripped at L1:

```text
IN:  Hi! I was basically wondering if you could help me debug this function.
     Just to clarify, it's not returning the correct values from the database.
     Thanks in advance!

L1:  help me debug this function. it's not returning the correct values from the database.
L2:  help me debug this fn. it's not returning the correct vals from the db.
L3:  help debug fn. not returning ok vals db.
```

*~75% token reduction at L3. Claude still understand. UGH.*

---

**2. Incident report** — filler opener gone, tech terms compressed, caveman logic applied:

```text
IN:  Don't hesitate to let me know if you need more context, but basically the
     problem is that the pipeline is not working because it can't connect to the
     message queue. The connection isn't being established because the credentials
     are invalid.

L1:  let me know if you need more context, but the problem is that the pipeline is
     not working because it can't connect to the message queue. The connection isn't
     being established because the credentials are invalid.
L2:  let me know if you need more ctx, but the problem is that the pipe is not
     working because it can't connect to the MQ. The conn isn't being established
     because the creds are invalid.
L3:  let know if need more ctx, but bug pipe broken bc no connect MQ. conn not
     established bc creds bad.
```

*~59% token reduction at L3.*

---

**3. Bug report with mixed concerns** — greeting, clarifier, and polite request all stripped:

```text
IN:  Hi! Just to clarify, I'm not sure if this is actually a bug, but basically
     the deployment pipeline is not working because it can't connect to the message
     queue. Could you please take a look at the configuration and let me know if the
     credentials are valid and whether the connection is being established correctly?

L1:  I'm not sure if this is actually a bug, but the deployment pipeline is not
     working because it can't connect to the message queue. take a look at the
     configuration and let me know if the credentials are valid and whether the
     connection is being established correctly?
L2:  I'm not sure if this is actually a bug, but the deploy pipe is not working
     because it can't connect to the MQ. take a look at the config and let me know
     if the creds are valid and whether the conn is being established correctly?
L3:  not sure if bug, but deploy pipe broken bc no connect MQ. check config and let
     know if creds ok and whether conn established correctly?
```

*~57% token reduction at L3.*

---

## Me Install

```bash
git clone https://github.com/nirmorgo/caveman-prompts.git
cd caveman-prompts
pip install -e .
```

First run download small brain model (~12 MB, one time only). After that — fast. No internet needed.

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
