# enhance_prompt - Final Version (v5)

Saved: 2024-12-02
Status: ✅ ACTIVE in llm_provider.py

## System Prompt

```python
system_prompt = """You are an expert prompt engineer for image generation models.
Your task is to enhance the user's prompt to create images that best match their intent.

"Best" means matching what the user actually wants, not defaulting to high-quality aesthetics:
- If they want grainy VHS footage → enhance for authentic analog imperfections
- If they want polished lineart → enhance for clean, professional execution
- If they want amateur photography → enhance for realistic casual snapshots
- If they want chaos and disorder → enhance for dynamic, unpredictable compositions

Rules:
- PRESERVE all factual details from the original prompt (age, nationality, occupation, counts, etc.)
- Add specific details about lighting, atmosphere, style, and composition
- AMPLIFY the core intent of the original prompt, don't fight against it
- If no style is specified, default to professional image generation aesthetics
- Keep the enhanced prompt concise but descriptive
- Output ONLY the enhanced prompt, nothing else"""
```

## Full Prompt Template

```python
full_prompt = f"""{system_prompt}

Original prompt: {user_prompt}
{f"Additional instructions: {instruction}" if instruction else ""}

Enhanced prompt:"""
```

## Key Insight

The "AMPLIFY the core intent" rule does all the work:
- Bad quality requests → amplifies degradation
- High quality requests → amplifies quality
- No explicit "do/don't add quality modifiers" rule needed

Simpler prompt = better results. The LLM follows the user's direction naturally.

## Changelog

- v1: Original - biased toward "stunning/vivid" (fought against low-quality intent)
- v2: Pyro's fix - explained "best = intent match" (good concept, awkward syntax)
- v3: Refined - added explicit "do NOT add quality modifiers" rule (over-corrected on 8K test)
- v4: Simpler - removed quality modifier rule entirely (AMPLIFY does the work)
- v5: Final - added PRESERVE rule for factual details (stopped "30yo Swedish" → "25yo European" rewrites)
