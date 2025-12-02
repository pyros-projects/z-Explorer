# Ministral TextOnly Migration Guide

This guide explains how to add support for the Ministral-3B TextOnly model to the main branch of Z-Explorer.

## Model Information

| Property | Value |
|----------|-------|
| **Model** | `Aratako/Ministral-3-3B-Instruct-2512-TextOnly` |
| **Type** | Text-only (no vision encoder) |
| **Format** | FP8 quantized |
| **VRAM** | ~8-10GB (after dequantization to bfloat16) |
| **Speed** | Fast inference, comparable to Qwen3-4B |

### Why TextOnly over Multimodal?

The original `mistralai/Ministral-3-3B-Instruct-2512` requires special classes (`Mistral3ForConditionalGeneration`, `MistralCommonBackend`) that aren't available in standard transformers. The TextOnly variant:

- Uses standard `AutoTokenizer` and `AutoModelForCausalLM`
- Has no vision encoder (which we don't need anyway)
- Lower VRAM footprint
- Better compatibility and future-proof

## Dependencies

Add to `pyproject.toml`:

```toml
dependencies = [
    # ... existing deps ...
    "transformers @ git+https://github.com/huggingface/transformers",
    "mistral-common>=1.8.6",
]
```

The git version of transformers is required for:
- `FineGrainedFP8Config` support
- Proper FP8 dequantization handling

## Code Changes

### 1. Add Model Detection Function

In `llm_provider.py`, add this function after the imports:

```python
def _is_ministral_fp8_model(model_name: str) -> bool:
    """Check if the model is a Ministral FP8 model that needs dequantization."""
    name_lower = model_name.lower()
    return "ministral" in name_lower
```

### 2. Add Global Flag

Add this with the other global variables:

```python
_is_ministral_fp8 = False  # Track if we loaded a Ministral FP8 text-only model
```

### 3. Add Model Loader Function

Add this new loader function:

```python
def _load_ministral_fp8_model(repo: str):
    """Load a Ministral text-only FP8 model with Auto classes."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, FineGrainedFP8Config

    console.print(f"[cyan]Loading Ministral FP8 model: {repo}[/cyan]")

    tokenizer = AutoTokenizer.from_pretrained(repo, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        repo,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        quantization_config=FineGrainedFP8Config(dequantize=True),
        trust_remote_code=True,
    )

    return model, tokenizer
```

Key points:
- `FineGrainedFP8Config(dequantize=True)` is **required** - the model is stored in FP8 format and must be dequantized
- `torch_dtype=torch.bfloat16` ensures proper dtype after dequantization
- `trust_remote_code=True` is needed for the model's custom code

### 4. Update `_load_model()` Function

In the `HF_DOWNLOAD` branch, add the Ministral check:

```python
elif config.mode == LLMMode.HF_DOWNLOAD:
    if _is_ministral_fp8_model(config.hf_repo):
        _is_ministral_fp8 = True
        _model, _tokenizer = _load_ministral_fp8_model(config.hf_repo)
    else:
        # ... existing code for other models ...
```

Similarly for `HF_LOCAL` mode if needed.

### 5. Update `generate_text()` Function

Ministral models don't accept `token_type_ids`. Add this after creating the inputs:

```python
# Standard model inference (Qwen, etc.)
text = tokenizer.apply_chat_template(
    messages, tokenize=False, add_generation_prompt=True
)
inputs = tokenizer(text, return_tensors="pt").to(model.device)

# ADD THIS: Remove token_type_ids if present (Ministral FP8 models don't accept it)
if _is_ministral_fp8 and "token_type_ids" in inputs:
    del inputs["token_type_ids"]

with torch.no_grad():
    # ... rest of generation code ...
```

### 6. Update `unload_model()` Function

Reset the flag when unloading:

```python
def unload_model():
    global _model, _tokenizer, _is_ministral_fp8  # Add _is_ministral_fp8
    
    if _model is not None:
        # ... existing cleanup code ...
        _is_ministral_fp8 = False  # Add this line
```

## Configuration

Users can configure Ministral via environment variables:

```bash
# .env file
LLM_MODE=hf_download
LLM_REPO=Aratako/Ministral-3-3B-Instruct-2512-TextOnly
```

Or via runtime API:

```bash
curl -X POST http://localhost:8000/api/settings/models \
  -H "Content-Type: application/json" \
  -d '{"llm_repo": "Aratako/Ministral-3-3B-Instruct-2512-TextOnly"}'
```

## Testing

Use the comparison script to verify output quality:

```bash
uv run python tests/scripts/generate_prompt_variable_values.py \
  --compare "unsloth/Qwen3-4B-Instruct-2507-bnb-4bit" \
  "Aratako/Ministral-3-3B-Instruct-2512-TextOnly"
```

Expected results:
- Ministral produces equally creative output
- Art styles tend to be more descriptive
- Detailed scenes are longer and more evocative
- Simple variables (cat breeds, colors) are comparable

## Prompt Engineering Notes

The improved prompt format with examples helps Ministral return proper JSON arrays:

```python
prompt = f"""Generate exactly {count} values for: "{readable_name}"

...

The variable name tells you what to generate. Examples:
- "cat breed" → ["Scottish Fold", "Persian", "Maine Coon"]
- "detailed scene" → ["A moonlit forest...", "A bustling Tokyo alley...", "An abandoned lighthouse..."]
- "color" → ["crimson", "midnight blue", "emerald green"]

Return ONLY a JSON array of {count} strings. No objects, no nested structures, just plain strings in an array.

JSON array:"""
```

This prevents Ministral from returning nested JSON objects.

## Checklist

- [ ] Update `pyproject.toml` with transformers git dependency
- [ ] Add `mistral-common>=1.8.6` dependency
- [ ] Add `_is_ministral_fp8_model()` detection function
- [ ] Add `_is_ministral_fp8` global flag
- [ ] Add `_load_ministral_fp8_model()` loader function
- [ ] Update `_load_model()` to use Ministral loader
- [ ] Update `generate_text()` to remove `token_type_ids`
- [ ] Update `unload_model()` to reset flag
- [ ] Run `uv sync` to update dependencies
- [ ] Test with comparison script

## Troubleshooting

### Error: "block_size is None"

The model is FP8 quantized and needs dequantization. Ensure you're using `FineGrainedFP8Config(dequantize=True)`.

### Error: "token_type_ids"

Ministral doesn't accept this parameter. Ensure the `_is_ministral_fp8` check removes it from inputs.

### Error: "No valid tokenizer file found"

Make sure you're using `AutoTokenizer`, not `MistralCommonBackend` (that's for multimodal only).

### Stray JSON markers in output

If you see ` ```json ``` ` in outputs, the prompt may need adjustment. The examples in the prompt help prevent this.
