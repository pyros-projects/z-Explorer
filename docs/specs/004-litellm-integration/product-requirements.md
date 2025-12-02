# Product Requirements Document

## Validation Checklist

- [x] All required sections are complete
- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Problem statement is specific and measurable
- [x] Problem is validated by evidence (not assumptions)
- [x] Context → Problem → Solution flow makes sense
- [x] Every persona has at least one user journey
- [x] All MoSCoW categories addressed (Must/Should/Could/Won't)
- [x] Every feature has testable acceptance criteria
- [x] Every metric has corresponding tracking events
- [x] No feature redundancy (check for duplicates)
- [x] No contradictions between sections
- [x] No technical implementation details included
- [x] A new team member could understand this PRD

---

## Product Overview

### Vision
Use any LLM provider (OpenAI, Anthropic, Ollama, etc.) for prompt enhancement and variable generation with a single configuration change.

### Problem Statement
Currently, Z-Explorer only supports local LLM inference via HuggingFace Transformers:

1. **High VRAM requirement** — Local models like Qwen3-4B require ~8GB VRAM, excluding users with modest GPUs
2. **Quality ceiling** — Local 4B models produce good results, but GPT-4 and Claude produce excellent results
3. **Complex setup** — Users must download large model files and configure paths correctly
4. **No flexibility** — Can't easily switch between local and cloud models based on task or preference
5. **Offline-only limitation** — Some users prefer cloud APIs for speed/quality when connected

Evidence: Users with <8GB VRAM cannot use prompt enhancement features. The Z-Image model itself requires ~12GB VRAM with SDNQ, leaving no room for LLM. Power users want access to frontier models for higher-quality prompt enhancement.

### Value Proposition
Z-Explorer gives users the freedom to choose: run LLMs locally for privacy and offline use, OR use cloud APIs (OpenAI, Anthropic, Ollama, etc.) for quality and convenience — all with a single env var change. LiteLLM provides a unified interface to 100+ providers, so users set their provider's standard env vars and go.

## User Personas

### Primary Persona: The Low-VRAM User
- **Demographics:** Age 20-40, hobbyist or student, has 6-8GB GPU, wants AI image generation
- **Goals:** Use Z-Explorer's full features including prompt enhancement without GPU memory errors
- **Pain Points:** Can't fit both image model and LLM in VRAM, cloud APIs seem complex to set up

### Secondary Persona: The Quality Maximizer
- **Demographics:** Age 25-50, professional artist or content creator, willing to pay for quality
- **Goals:** Get the absolute best prompt enhancement using frontier models like GPT-4 or Claude
- **Pain Points:** Limited by local model quality, wants enterprise-grade LLM output

### Tertiary Persona: The Privacy-Conscious Creator
- **Demographics:** Any age, may work with sensitive content, values data privacy
- **Goals:** Keep all data local while having flexibility for non-sensitive tasks
- **Pain Points:** Doesn't want to send prompts to cloud by default, but wants option when appropriate

## User Journey Maps

### Primary User Journey: Low-VRAM User Enables Cloud LLM
1. **Awareness:** User sees "OOM error" when trying to enhance prompts, GPU can't fit both models
2. **Consideration:** User learns about LiteLLM option in docs — can use cloud API with 0 VRAM for LLM
3. **Adoption:** User sets `LLM_MODE=litellm` and `LLM_MODEL=openai/gpt-4o-mini`, adds `OPENAI_API_KEY`
4. **Usage:** Prompt enhancement works! Uses OpenAI API, image model uses full GPU
5. **Retention:** User continues with hybrid setup — cloud LLM for text, local GPU for images

### Secondary User Journey: Setup Wizard Configuration
1. **Awareness:** New user runs setup wizard on first launch
2. **Consideration:** Wizard offers choice: "Local LLM (requires ~8GB VRAM)" or "Cloud API (LiteLLM)"
3. **Adoption:** User selects Cloud API, picks provider (OpenAI), enters API key
4. **Usage:** App configured automatically with correct env vars
5. **Retention:** User can change later via Settings or .env file

### Tertiary User Journey: Switching Between Modes
1. **Awareness:** User normally uses cloud API but wants to work offline today
2. **Consideration:** Knows they can change `LLM_MODE` in .env or Settings
3. **Adoption:** Changes to `LLM_MODE=hf_download` for local mode
4. **Usage:** App uses local Qwen3-4B instead of cloud API
5. **Retention:** User switches freely based on context (travel=local, home=cloud)

## Feature Requirements

### Must Have Features

#### Feature 1: LiteLLM Mode
- **User Story:** As a user with limited VRAM, I want to use cloud LLM APIs so that I can enhance prompts without GPU memory issues
- **Acceptance Criteria:**
  - [x] New `LLM_MODE=litellm` option available
  - [x] When litellm mode active, LLM calls go through LiteLLM library
  - [x] All existing LLM features work (prompt enhancement, variable generation)
  - [x] No local model loaded when in litellm mode (0 VRAM for LLM)

#### Feature 2: Model Configuration via LLM_MODEL
- **User Story:** As a user, I want to specify which LLM to use with a simple model identifier so that I can easily switch between providers and models
- **Acceptance Criteria:**
  - [x] `LLM_MODEL` env var specifies the model (e.g., `openai/gpt-4o-mini`, `anthropic/claude-3-haiku`)
  - [x] Rename `LLM_REPO` to `LLM_MODEL` (backward compat: `LLM_REPO` still works with deprecation warning)
  - [x] Model identifier follows LiteLLM format: `provider/model-name`
  - [x] Works for both cloud (LiteLLM) and local (HuggingFace) modes

#### Feature 3: Standard Provider Environment Variables
- **User Story:** As a user, I want to use my provider's standard env vars so that I don't need to learn Z-Explorer-specific configuration
- **Acceptance Criteria:**
  - [x] NO custom API key env vars in Z-Explorer (no `Z_EXPLORER_API_KEY`)
  - [x] Users set provider's standard vars: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.
  - [x] LiteLLM automatically reads these standard env vars
  - [x] Documentation points to LiteLLM provider docs for env var details

#### Feature 4: Backward Compatibility
- **User Story:** As an existing user, I want my current configuration to keep working after the update
- **Acceptance Criteria:**
  - [x] Existing `LLM_MODE` values (z_image, hf_local, hf_download, gguf) continue working
  - [x] `LLM_REPO` recognized with deprecation warning suggesting `LLM_MODEL`
  - [x] Users without litellm mode configured see no change in behavior

### Should Have Features

#### Feature 5: Setup Wizard LiteLLM Option
- **User Story:** As a new user, I want to configure cloud LLM during setup so that I don't have to manually edit .env files
- **Acceptance Criteria:**
  - [x] Setup wizard offers "Cloud API (LiteLLM)" as LLM option
  - [x] Common providers listed (OpenAI, Anthropic, Ollama)
  - [x] API key input with provider-specific guidance
  - [x] Configuration saved to .env automatically

#### Feature 6: Settings UI for LLM Mode
- **User Story:** As a user, I want to switch LLM modes from the UI so that I don't have to restart the app or edit files
- **Acceptance Criteria:**
  - [x] Settings dialog shows current LLM configuration
  - [x] Can switch between local and litellm modes
  - [x] Model selection available for litellm mode
  - [x] Changes take effect on next LLM operation

### Could Have Features

#### Feature 7: Provider Health Check
- **User Story:** As a user, I want to verify my API key works before generating so that I catch configuration errors early
- **Acceptance Criteria:**
  - [x] "Test Connection" button in Settings
  - [x] Makes simple API call to verify credentials
  - [x] Shows success/failure feedback

#### Feature 8: Usage/Cost Display
- **User Story:** As a user paying for API calls, I want to see usage info so that I can monitor costs
- **Acceptance Criteria:**
  - [x] Token count shown after LLM operations
  - [x] Approximate cost estimate (if available from provider)

### Won't Have (This Phase)
- Streaming LLM responses (batch only for now)
- Multiple LLM providers active simultaneously
- Automatic provider failover
- Token budget limits or spending caps
- Caching of LLM responses
- Custom system prompts per provider

## Detailed Feature Specifications

### Feature: LiteLLM Mode
**Description:** A new `LLM_MODE=litellm` option that routes all LLM calls through the LiteLLM library, enabling access to 100+ LLM providers with a unified interface.

**User Flow:**
1. User sets `LLM_MODE=litellm` in .env or Settings
2. User sets `LLM_MODEL=provider/model-name` (e.g., `openai/gpt-4o-mini`)
3. User sets provider's API key env var (e.g., `OPENAI_API_KEY=sk-...`)
4. User uses prompt enhancement or variable generation features
5. App calls LiteLLM with model identifier, LiteLLM handles provider details
6. Response returned, no local model loaded

**Business Rules:**
- Rule 1: When `LLM_MODE=litellm`, never load local HuggingFace models (save VRAM)
- Rule 2: LiteLLM mode requires valid `LLM_MODEL` in provider/model format
- Rule 3: API key errors should surface clearly with provider-specific guidance
- Rule 4: All LLM features must work identically regardless of mode (same prompts, same parsing)

**Edge Cases:**
- Missing API key → Clear error: "Set OPENAI_API_KEY environment variable"
- Invalid model name → LiteLLM error propagated with context
- API rate limit → Error shown with retry suggestion
- Network offline → Error shown suggesting local mode
- Model not available → List common alternatives in error message

## Success Metrics

### Key Performance Indicators
- **Adoption:** 30% of users try litellm mode within first month of update
- **Engagement:** Users in litellm mode complete 2x more prompt enhancements (less friction)
- **Quality:** User satisfaction with enhanced prompts increases (subjective, via feedback)
- **Business Impact:** Opens Z-Explorer to users with <8GB VRAM (expands market)

### Tracking Requirements

| Event | Properties | Purpose |
|-------|------------|---------|
| `llm_mode_configured` | `mode: local\|litellm`, `provider: string` | Track adoption by mode |
| `llm_call_started` | `mode: string`, `model: string`, `feature: enhance\|variable` | Measure usage patterns |
| `llm_call_completed` | `mode: string`, `model: string`, `tokens: number`, `duration_ms: number` | Performance tracking |
| `llm_call_failed` | `mode: string`, `model: string`, `error_type: string` | Error monitoring |
| `setup_wizard_llm_choice` | `choice: local\|litellm`, `provider: string` | New user preferences |

---

## Constraints and Assumptions

### Constraints
- **No new custom env vars for API keys** — LiteLLM uses standard provider env vars
- **Same interface for all modes** — `generate_text()`, `enhance_prompt()`, `generate_prompt_variable_values()` must have identical signatures
- **Additive change** — All existing LLM modes must continue working

### Assumptions
- Users have internet access when using litellm mode
- Users can obtain API keys from their chosen provider
- LiteLLM library is stable and maintained
- Provider pricing is user's responsibility to monitor

## Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| LiteLLM dependency issues | Medium | Low | Pin specific version, have fallback to direct API calls |
| API costs surprise users | Medium | Medium | Document that cloud APIs cost money, show token counts |
| Provider API changes | Low | Low | LiteLLM handles this; we're insulated |
| Users share API keys accidentally | Medium | Low | Document security best practices, .env in .gitignore |

## Open Questions

- [x] Should we support Ollama as special case (local but via API)? → **Yes, Ollama works via LiteLLM with `ollama/model-name`**
- [x] Default model for litellm mode? → **No default; user must specify LLM_MODEL**
- [x] Show cost estimates? → **Could Have; defer to later if needed**

---

## Supporting Research

### Competitive Analysis
- **ComfyUI**: No built-in LLM, relies on external tools for prompt enhancement
- **A1111**: Has extensions for cloud LLM but requires complex setup
- **Midjourney**: Cloud-only, no local option
- **DALL-E**: Cloud-only, no flexibility

**Conclusion:** Z-Explorer uniquely offers both local AND cloud LLM with simple configuration switch.

### LiteLLM Provider Coverage
LiteLLM supports 100+ providers including:
- OpenAI (GPT-4, GPT-4o, GPT-4o-mini)
- Anthropic (Claude 3.5, Claude 3)
- Ollama (local models via API)
- Azure OpenAI
- Google (Gemini)
- Cohere, Mistral, Groq, Together, and many more

See: https://docs.litellm.ai/docs/providers

### User Research
From Z-Explorer user patterns:
- Many users have 6-8GB GPUs (not enough for LLM + image model)
- Power users explicitly request GPT-4 quality for prompt enhancement
- Privacy-conscious users want local option preserved
- "Just works" setup valued over flexibility for beginners
