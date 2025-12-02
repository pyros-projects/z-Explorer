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

### Why TextOnly?

The TextOnly variant uses standard `AutoTokenizer` and `AutoModelForCausalLM`, making it:

- **Compatible** - Works with standard transformers classes
- **Lightweight** - No vision encoder (which we don't need anyway)
- **Future-proof** - No special handling needed as transformers evolves

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

All changes are in `src/z_explorer/llm_provider.py`:

### 1. Add Global Flag

```python
_is_ministral_fp8 = False  # Track if we loaded a Ministral FP8 text-only model
```

### 2. Add Model Detection Function

```python
def _is_ministral_fp8_model(model_name: str) -> bool:
    """Check if the model is a Ministral FP8 model that needs dequantization.

    Matches models like:
    - Aratako/Ministral-3-3B-Instruct-2512-TextOnly
    - Any model with 'ministral' in the name
    """
    name_lower = model_name.lower()
    return "ministral" in name_lower
```

### 3. Add Model Loader Function

```python
def _load_ministral_fp8_model(repo: str):
    """Load a Ministral text-only FP8 model with Auto classes.

    Ministral models are stored in FP8 format and need to be dequantized
    to bfloat16 on load using FineGrainedFP8Config.
    """
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
- `FineGrainedFP8Config(dequantize=True)` is **required** - the model is stored in FP8 format
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

Similarly for `HF_LOCAL` mode.

### 5. Update `generate_text()` Function

Ministral models don't accept `token_type_ids`. Add this after creating the inputs:

```python
inputs = tokenizer(text, return_tensors="pt").to(model.device)

# Remove token_type_ids if present (Ministral FP8 models don't accept it)
if _is_ministral_fp8 and "token_type_ids" in inputs:
    del inputs["token_type_ids"]
```

### 6. Update `unload_model()` Function

Reset the flag when unloading:

```python
def unload_model():
    global _model, _tokenizer, _is_ministral_fp8
    # ... existing cleanup ...
    _is_ministral_fp8 = False
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

## Checklist

- [ ] Update `pyproject.toml` with transformers git dependency
- [ ] Add `mistral-common>=1.8.6` dependency
- [ ] Add `_is_ministral_fp8` global flag
- [ ] Add `_is_ministral_fp8_model()` detection function
- [ ] Add `_load_ministral_fp8_model()` loader function
- [ ] Update `_load_model()` to use Ministral loader (HF_DOWNLOAD + HF_LOCAL)
- [ ] Update `generate_text()` to remove `token_type_ids`
- [ ] Update `unload_model()` to reset flag
- [ ] Run `uv sync` to update dependencies
- [ ] Test with comparison script

## Troubleshooting

### Error: "block_size is None"

The model is FP8 quantized and needs dequantization. Ensure you're using:
```python
quantization_config=FineGrainedFP8Config(dequantize=True)
```

### Error: "token_type_ids"

Ministral doesn't accept this parameter. Ensure the `_is_ministral_fp8` check removes it from inputs.

### Stray JSON markers in output

If you see ` ```json ``` ` in outputs, the prompt examples help prevent this. The current prompt format with concrete examples produces clean JSON output.

## Output Quality

Ministral TextOnly produces rich, creative output:

| Variable Type | Qwen3-4B | Ministral TextOnly |
|--------------|----------|-------------------|
| Simple (cat_breed) | Good | Equally good |
| Art styles | 2 words avg | 7-9 words, more descriptive |
| Detailed scenes | 15-19 words | 51-65 words, richer |
| Fantasy landscapes | 31-37 words | 32-47 words |
| Very detailed 50w+ | 97-119 words | 124-127 words |

Both models produce quality output suitable for image generation prompts.
