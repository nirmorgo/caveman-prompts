"""Basic usage examples for caveman-prompts."""

from caveman import CavemanCompressor

# --- Level 2 (default) ---
c = CavemanCompressor(level=2)
print(c.compress("Can you please write a function that returns a list?"))
# -> make a fn that -> a list?

# --- Report ---
c.report("Can you please write a function that returns a list?")

# --- Level 3 (full caveman) ---
c3 = CavemanCompressor(level=3)
print(c3.compress("Can you please write a function that returns a list?"))
# -> make fn -> list?

# --- Chainable setters ---
result = (
    CavemanCompressor()
    .set_level(3)
    .add_rule("utilize", "use")
    .compress("Please utilize the database to store the configuration variables")
)
print(result)

# --- Sacred words ---
c_sacred = CavemanCompressor(level=3).add_sacred("MyClassName")
print(c_sacred.compress("Please refactor MyClassName to use the database"))
# MyClassName is never touched

# --- Preserve code blocks ---
prompt = """\
Can you please write a function like this:

```python
def process(items):
    return [x for x in items if x is not None]
```
"""
print(c3.compress(prompt))
