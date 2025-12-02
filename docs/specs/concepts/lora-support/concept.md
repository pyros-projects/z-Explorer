pipe.load_lora_weights("bb85.safetensors", adapter_name="bb50")
pipe.set_adapters(["bb50"], adapter_weights=[1.0])


# LoRA Support - Design Concept

Status: 📋 CONCEPT (not scheduled)
Created: 2024-12-02

## Philosophy

LoRA support should follow z-Explorer's core principles:
- **Grammar as interface** - Use existing prompt syntax, no new UI panels
- **Zero friction** - Drop files in folder, use by name
- **Progressive disclosure** - Beginners can ignore, power users get control
- **No spaghetti** - Simple mental model

## User Experience

### Basic Usage
```
a portrait of a woman : anime
a dragon in a forest : sketch:0.7, cinematic, x4
```

### How It Works
1. User drops `anime.safetensors` into `loras/` folder
2. User types `a cat : anime` 
3. System loads LoRA, generates image, done

No config files. No registration. No UI toggles.

## Syntax

Reuse existing batch parameter syntax (`: key:value`):

```
prompt : lora_name              → LoRA at default weight (0.8)
prompt : lora_name:0.9          → LoRA at explicit weight
prompt : anime, sketch:0.5, x3  → Multiple LoRAs + batch params
```

### Disambiguation
The parser identifies LoRAs vs batch params:
- **Known params**: `x4`, `w1024`, `h768`, `seed:123`, `steps:30`
- **LoRA**: Everything else that exists in LORA_DIR

```
a cat : anime:0.8, w1024, x2
        └─LoRA─┘  └─params─┘
```

## Configuration

### Environment Variable
```env
LORA_DIR=./loras              # Default: ./loras in project root
```

### Settings Override (Session)
```
POST /api/settings
{ "lora_dir": "D:/models/loras" }
```

### GUI
Settings dialog gets a "LoRA Directory" field (same pattern as output dir).

## File Discovery

```
$LORA_DIR/
  anime.safetensors           → use as "anime"
  sketch.safetensors          → use as "sketch" 
  cinematic-v2.safetensors    → use as "cinematic-v2"
  subdirs/not-supported.safetensors  → ignored (flat structure)
```

**Identifier = filename without extension**

## Optional: Metadata File

For power users who want descriptions and custom defaults:

```yaml
# loras/loras.yaml (optional)
anime:
  weight: 0.85                    # Override default weight
  description: "Anime/manga style"
  aliases: ["manga", "japanese"]  # Alternative names

sketch:
  weight: 0.6
  triggers: ["pencil", "drawn"]   # Words that auto-suggest this LoRA
```

If no YAML exists, everything still works - just uses filename and default weight.

## Integration Points

| Component | Role |
|-----------|------|
| `model_config.py` | Add `LORA_DIR` config with validation |
| `cli.py` | Parse LoRA names from batch params |
| `core/generator.py` | Pass LoRA config to image generation |
| `image_generator.py` | `load_lora_weights()` + `set_adapters()` |
| `server.py` | Add `lora_dir` to settings API |
| `Settings.svelte` | Add LoRA directory field |
| `FakeCLI.svelte` | Autocomplete for available LoRA names |

## Memory Management

Fits the existing two-phase pattern:

```
Phase 1: LLM (variables, enhancement)
  ↓ unload LLM
Phase 2: Image Generation
  → Load pipeline
  → Load LoRA weights (if specified)
  → Generate
  → Unload LoRA weights (keep pipeline hot)
```

LoRAs are lightweight relative to the base model - can load/unload per generation without major overhead.

## Progress Events

```
✨ Found LoRA: anime (weight: 0.8)
✨ Found LoRA: sketch (weight: 0.5)
🎨 Generating with 2 LoRAs...
```

## Error Handling

| Scenario | Behavior |
|----------|----------|
| LoRA file not found | Warning + continue without it |
| Invalid weight (>2.0 or <0) | Clamp to valid range + warning |
| LORA_DIR doesn't exist | Create on first use or warn |
| Incompatible LoRA format | Skip with error message |

## Edge Cases

- **No LoRAs specified**: Normal generation (current behavior)
- **Empty LORA_DIR**: Works fine, no autocomplete suggestions
- **Same LoRA twice**: Last weight wins, warn user
- **LoRA + variable**: Works - variables resolve first, then LoRAs apply

```
a __animal__ in a forest : anime, x3
  ↓ Phase 1: resolve variable
a phoenix in a forest : anime, x3
  ↓ Phase 2: apply LoRA + generate 3 images
```

## Future Considerations (Out of Scope)

- LoRA training integration
- LoRA preview thumbnails
- LoRA strength curves (vary weight across batch)
- Online LoRA discovery/download

---

## Summary

**The z-Explorer way:**
1. Drop `.safetensors` in `loras/` folder
2. Use by name in prompt: `a cat : anime:0.8`
3. That's it. No config, no UI, no spaghetti.
