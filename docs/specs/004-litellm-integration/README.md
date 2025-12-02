# Spec 004: LiteLLM Integration

## Quick Summary

**What**: Add LiteLLM support to use cloud LLM providers (OpenAI, Anthropic, Ollama, etc.) for prompt enhancement and variable generation.

**Why**: Local LLMs require ~8GB VRAM which many users don't have. Cloud APIs offer better quality (GPT-4, Claude) with zero VRAM usage.

**Status**: ✅ Ready for Implementation

## Specification Documents

| Document | Purpose | Status |
|----------|---------|--------|
| [product-requirements.md](./product-requirements.md) | What to build and why | ✅ Complete |
| [solution-design.md](./solution-design.md) | How to build it | ✅ Complete |
| [implementation-plan.md](./implementation-plan.md) | Step-by-step tasks | ✅ Complete |

## Key Deliverables

1. **LiteLLM Mode** - New `LLM_MODE=litellm` for cloud APIs
2. **LLM_MODEL Variable** - Unified model identifier (replaces LLM_REPO)
3. **Standard Env Vars** - Use provider's API key vars (OPENAI_API_KEY, etc.)
4. **Setup Wizard** - Cloud API option during first-run setup
5. **Full Backward Compat** - Existing configs continue working

## Configuration Examples

```bash
# Local model (existing)
LLM_MODE=hf_download
LLM_MODEL=unsloth/Qwen3-4B-Instruct-2507-bnb-4bit

# Cloud: OpenAI
LLM_MODE=litellm
LLM_MODEL=openai/gpt-4o-mini
# Set OPENAI_API_KEY in your environment

# Cloud: Anthropic
LLM_MODE=litellm
LLM_MODEL=anthropic/claude-3-haiku-20240307
# Set ANTHROPIC_API_KEY in your environment

# Local via API: Ollama
LLM_MODE=litellm
LLM_MODEL=ollama/llama3
# No API key needed for local Ollama
```

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Provider abstraction | LiteLLM library | 100+ providers, unified interface |
| Config variable | LLM_MODEL (replaces LLM_REPO) | "Model" is more accurate |
| API keys | Provider standard vars | No custom vars, works with existing setups |
| Prompts | Same for all modes | Simplicity, consistent behavior |

## Implementation Phases

```
T1: Add LiteLLM dependency
     ↓
T2: Extend configuration model (LLMMode, LLMConfig)
     ↓
T3: Implement _generate_litellm() function
     ↓
T4: Update enhance_prompt() and variable generation
     ↓
T5: Setup wizard LiteLLM option (parallel)
     ↓
T6: Update documentation (parallel)
     ↓
T7: Integration & E2E validation
```

**Estimated Effort**: ~5.5 hours

## Confidence Assessment

| Dimension | Level | Notes |
|-----------|-------|-------|
| Requirements Clarity | 🟢 High | Clear user needs, design already discussed |
| Technical Feasibility | 🟢 High | LiteLLM is mature, well-documented |
| Scope Containment | 🟢 High | Additive changes only, no breaking changes |
| Risk Level | 🟢 Low | External dependency but actively maintained |
| Estimation Accuracy | 🟢 High | Straightforward integration |

**Overall Confidence**: 🟢 **High** - Ready to ship

## Dependencies

- **None required** - This is a standalone enhancement

## Related Specs

- **002**: Info Flyout & Metadata (no dependency)
- **003**: Gallery Search (no dependency)  
- **005** (future): Variable Editor (will use this LLM config)

## How to Implement

```bash
/start:implement 004
```

## Supported Providers

LiteLLM supports 100+ providers including:

| Provider | Model Examples | API Key Env Var |
|----------|---------------|-----------------|
| OpenAI | gpt-4o-mini, gpt-4o | OPENAI_API_KEY |
| Anthropic | claude-3-haiku, claude-3.5-sonnet | ANTHROPIC_API_KEY |
| Ollama | llama3, mistral | (none - local) |
| Azure OpenAI | (deployment name) | AZURE_API_KEY |
| Google | gemini-pro | GOOGLE_API_KEY |

See full list: https://docs.litellm.ai/docs/providers
