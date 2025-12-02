# Specification 006: LoRA Support

## Quick Reference

| Document | Purpose | Status |
|----------|---------|--------|
| [Product Requirements](./product-requirements.md) | What we're building and why | ✅ Complete |
| [Solution Design](./solution-design.md) | How we're building it | ✅ Complete |
| [Implementation Plan](./implementation-plan.md) | Step-by-step execution | ✅ Complete |

## Overview

Enable z-Explorer users to apply LoRA style adapters with zero-friction: drop `.safetensors` files in a folder, use them by filename in prompts using existing batch parameter syntax.

**Syntax**: `prompt : lora_name:weight`

**Examples**:
```
a cat : anime              # Default weight (0.8)
a cat : anime:0.7          # Explicit weight
a cat : anime, sketch:0.5  # Multiple LoRAs
a cat : anime:0.8, x3      # LoRA + batch params
```

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Syntax | Reuse batch params (`: lora:weight`) | Users already know the pattern |
| Discovery | Scan at generation time | No restart needed for new LoRAs |
| Default weight | 0.8 | Community recommendation |
| LoRA limit | 4 simultaneous | Stability boundary |

## Implementation Summary

**7 Phases** | **7-13 hours estimated**

1. **T1**: LoRA Config Module - dataclasses, discovery, YAML loader
2. **T2**: Parser Extension - batch param disambiguation
3. **T3**: Image Generator - peft/LoRA loading integration
4. **T4**: Core Generator - workflow updates, progress events
5. **T5**: CLI & Server (parallel) - /loras command, API endpoints
6. **T6**: GUI (parallel) - Settings field, autocomplete
7. **T7**: Integration & E2E validation

## Features (MoSCoW)

### Must Have
- LoRA file discovery (drop .safetensors, use by name)
- Prompt syntax (`name:weight`)
- Multiple LoRA support (up to 4)
- Directory configuration (LORA_DIR)

### Should Have
- Autocomplete in FakeCLI
- Progress feedback (found, warnings)

### Could Have
- Optional `loras.yaml` for metadata
- `/loras` command

## Dependencies

- `peft` library (LoRA loading APIs)
- `pyyaml` (optional metadata file)

## Next Steps

To implement this specification:

```bash
/start:implement 006
```

---

## Confidence Assessment

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Requirements Clarity** | 9/10 | Well-defined acceptance criteria, clear edge cases |
| **Technical Feasibility** | 9/10 | peft library is proven; patterns exist in codebase |
| **Design Completeness** | 9/10 | Parser algorithm, data models, progress timing all specified |
| **Implementation Path** | 9/10 | TDD phases with clear dependencies |
| **Risk Mitigation** | 8/10 | Graceful degradation documented; some unknowns in LoRA compatibility |

### Overall Implementation Confidence: **88%**

**Low-risk implementation** - All major decisions made, patterns established, TDD approach minimizes risk.

### Open Items

1. **Nested LoRA directories**: Decision leaning toward flat-only for simplicity (not blocking)
2. **peft integration testing**: May surface edge cases during T3

### Validation Notes

- ✅ PRD → SDD → PLAN alignment verified
- ✅ No contradictions between documents
- ✅ All acceptance criteria have corresponding tests in PLAN
- ✅ Dependency graph is acyclic
- ✅ Parallel tasks correctly identified
