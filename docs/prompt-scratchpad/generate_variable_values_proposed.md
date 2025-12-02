# generate_prompt_variable_values - Proposed Improvements

Saved: 2024-12-02
Status: 📋 BACKLOG (low priority)
Priority: Low - current prompt works well, these are polish items

## Current Prompt (Working)

```python
prompt = f"""Generate exactly {count} values for: "{readable_name}"

Context: This will be substituted into the prompt "{context_prompt}"

The variable name tells you what to generate. Examples:
- "cat breed" → ["Scottish Fold", "Persian", "Maine Coon"]
- "detailed scene" → ["A moonlit forest with ancient oaks and a winding stream reflecting stars", "A bustling Tokyo alley at night with neon signs and rain-slicked pavement", "An abandoned lighthouse on a cliff during a violent storm"]
- "color" → ["crimson", "midnight blue", "emerald green"]

Interpret "{readable_name}" literally. Generate what it asks for.

Return ONLY a JSON array of {count} strings. No objects, no nested structures, just plain strings in an array.

JSON array:"""
```

## Proposed Tweak

```python
prompt = f"""Generate exactly {count} diverse values for: "{readable_name}"

Context: This will be substituted into the prompt "{context_prompt}"

The variable name tells you what to generate. Examples:
- "cat breed" → ["Scottish Fold", "Persian", "Maine Coon"]
- "detailed scene" → ["A moonlit forest with ancient oaks...", "A bustling Tokyo alley..."]
- "single word mood" → ["melancholic", "euphoric", "tense"]

Interpret "{readable_name}" literally. Match the complexity implied by the name.
Ensure variety - avoid repetitive or similar values.

Return ONLY a JSON array of {count} strings.

JSON array:"""
```

## Changes Summary

| Change | Rationale |
|--------|-----------|
| Added "diverse" to first line | Explicit variety guidance |
| Added "single word mood" example | Shows edge case with constrained output |
| Added "Match the complexity implied" | Aligns with enhance_prompt's AMPLIFY philosophy |
| Added "Ensure variety" rule | Prevents repetitive outputs like "red, dark red, light red" |
| Shortened detailed scene example | Less token usage, same idea |

## When to Prioritize

Consider implementing if users report:
- Repetitive/similar values in generated lists
- Wrong complexity (too long when short requested, or vice versa)
- Edge cases not being respected (e.g., "3 word phrase" generating sentences)

## Test Script

Use existing test script to validate:
```bash
uv run python tests/scripts/generate_prompt_variable_values.py
```
