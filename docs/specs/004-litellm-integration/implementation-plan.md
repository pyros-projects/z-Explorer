# Implementation Plan

## Validation Checklist

- [x] All specification file paths are correct and exist
- [x] Context priming section is complete
- [x] All implementation phases are defined
- [x] Each phase follows TDD: Prime → Test → Implement → Validate
- [x] Dependencies between phases are clear (no circular dependencies)
- [x] Parallel work is properly tagged with `[parallel: true]`
- [x] Activity hints provided for specialist selection `[activity: type]`
- [x] Every phase references relevant SDD sections
- [x] Every test references PRD acceptance criteria
- [x] Integration & E2E tests defined in final phase
- [x] Project commands match actual project setup
- [x] A developer could follow this plan independently

---

## Specification Compliance Guidelines

### How to Ensure Specification Adherence

1. **Before Each Phase**: Complete the Pre-Implementation Specification Gate
2. **During Implementation**: Reference specific SDD sections in each task
3. **After Each Task**: Run Specification Compliance checks
4. **Phase Completion**: Verify all specification requirements are met

### Deviation Protocol

If implementation cannot follow specification exactly:
1. Document the deviation and reason
2. Get approval before proceeding
3. Update SDD if the deviation is an improvement
4. Never deviate without documentation

## Metadata Reference

- `[parallel: true]` - Tasks that can run concurrently
- `[component: component-name]` - For multi-component features
- `[ref: document/section; lines: 1, 2-3]` - Links to specifications
- `[activity: type]` - Activity hint for specialist agent selection

---

## Context Priming

*GATE: You MUST fully read all files mentioned in this section before starting any implementation.*

**Specification**:

- `docs/specs/004-litellm-integration/product-requirements.md` - Product Requirements
- `docs/specs/004-litellm-integration/solution-design.md` - Solution Design

**Key Design Decisions**:

- **ADR-1**: Use LiteLLM library as abstraction layer
- **ADR-2**: Rename LLM_REPO to LLM_MODEL (with backward compat)
- **ADR-3**: No custom API key variables — use provider standards
- **ADR-4**: Same prompts work for all modes

**Implementation Context**:

- Commands: `uv run pytest`, `uv run ruff check .`, `uv run ruff format .`
- Add dependency: `uv add litellm`
- Key files: `model_config.py`, `llm_provider.py`, `setup_wizard.py`

---

## Implementation Phases

### T1: Add LiteLLM Dependency

*Deliverable: LiteLLM library available in project.*

- [ ] T1.1 Prime Context
    - [ ] T1.1.1 Read `pyproject.toml` to understand current dependencies

- [ ] T1.2 Implement `[activity: domain-modeling]`
    - [ ] T1.2.1 Add litellm dependency: `uv add litellm`
    - [ ] T1.2.2 Verify installation: `uv run python -c "import litellm; print(litellm.__version__)"`

- [ ] T1.3 Validate
    - [ ] T1.3.1 Run `uv sync` to ensure clean install
    - [ ] T1.3.2 Verify no dependency conflicts

---

### T2: Extend Configuration Model

*Deliverable: LLMConfig supports LITELLM mode and LLM_MODEL variable.*

- [ ] T2.1 Prime Context
    - [ ] T2.1.1 Read `src/z_explorer/model_config.py` fully
    - [ ] T2.1.2 Note LLMMode enum and LLMConfig dataclass `[ref: SDD/Application Data Models]`

- [ ] T2.2 Write Tests `[activity: test-execution]`
    - [ ] T2.2.1 Create/extend `tests/test_model_config.py`:
        - `test_litellm_mode_parsed()` - LLM_MODE=litellm recognized
        - `test_llm_model_read()` - LLM_MODEL env var read correctly
        - `test_llm_repo_backward_compat()` - LLM_REPO works with warning
        - `test_litellm_config_validation()` - model required for litellm mode
        `[ref: PRD/Feature 2, Feature 4 Acceptance Criteria]`

- [ ] T2.3 Implement `[activity: domain-modeling]`
    - [ ] T2.3.1 Add `LITELLM = "litellm"` to `LLMMode` enum
    - [ ] T2.3.2 Add `model: Optional[str] = None` field to `LLMConfig`
    - [ ] T2.3.3 Update `get_llm_config()`:
        - Read `LLM_MODEL` env var
        - Fallback to `LLM_REPO` with deprecation warning
        - Handle `LLM_MODE=litellm`
        ```python
        model = os.getenv("LLM_MODEL")
        if not model:
            repo = os.getenv("LLM_REPO")
            if repo:
                import warnings
                warnings.warn("LLM_REPO is deprecated, use LLM_MODEL instead", DeprecationWarning)
                model = repo
        ```
    - [ ] T2.3.4 Update `LLMConfig.validate()` for litellm mode:
        - Require `model` field when mode is LITELLM
        - Validate model format (should contain `/` for provider/model)
        `[ref: SDD/Configuration Reading Pattern]`

- [ ] T2.4 Validate
    - [ ] T2.4.1 Run `uv run ruff check src/z_explorer/model_config.py` `[activity: lint-code]`
    - [ ] T2.4.2 Run `uv run pytest tests/test_model_config.py -v` `[activity: run-tests]`

---

### T3: Implement LiteLLM Generation

*Deliverable: `generate_text()` works with LiteLLM mode.*

- [ ] T3.1 Prime Context
    - [ ] T3.1.1 Read `src/z_explorer/llm_provider.py` fully
    - [ ] T3.1.2 Review LiteLLM docs: https://docs.litellm.ai/docs/completion
    - [ ] T3.1.3 Note existing `generate_text()` signature `[ref: SDD/Runtime View]`

- [ ] T3.2 Write Tests `[activity: test-execution]`
    - [ ] T3.2.1 Create/extend `tests/test_llm_provider.py`:
        - `test_generate_text_litellm_mode()` - calls LiteLLM (mock)
        - `test_generate_text_local_mode()` - existing behavior unchanged
        - `test_litellm_no_local_model_loaded()` - verify no GPU memory used
        - `test_litellm_error_handling()` - missing API key, network error
        `[ref: PRD/Feature 1 Acceptance Criteria]`

- [ ] T3.3 Implement `[activity: domain-modeling]`
    - [ ] T3.3.1 Create `_generate_litellm()` function:
        ```python
        def _generate_litellm(
            prompt: str,
            model: str,
            max_tokens: int = 1024,
            temperature: float = 0.7,
        ) -> str:
            import litellm
            
            response = litellm.completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content.strip()
        ```
    - [ ] T3.3.2 Modify `generate_text()` to check mode:
        ```python
        def generate_text(prompt: str, max_tokens: int = 1024, ...) -> str:
            from z_explorer.model_config import get_llm_config, LLMMode
            
            config = get_llm_config()
            
            if config.mode == LLMMode.LITELLM:
                if not config.model:
                    raise ValueError("LLM_MODEL required for litellm mode")
                return _generate_litellm(prompt, config.model, max_tokens, temperature)
            else:
                # Existing local model path
                model, tokenizer = _load_model()
                # ... existing logic
        ```
    - [ ] T3.3.3 Add error handling wrapper for LiteLLM exceptions:
        - `litellm.AuthenticationError` → Clear message about API key
        - `litellm.RateLimitError` → Retry suggestion
        - `litellm.NotFoundError` → Model name format hint
        `[ref: SDD/Error Handling]`

- [ ] T3.4 Validate
    - [ ] T3.4.1 Run `uv run ruff check src/z_explorer/llm_provider.py` `[activity: lint-code]`
    - [ ] T3.4.2 Run `uv run pytest tests/test_llm_provider.py -v` `[activity: run-tests]`
    - [ ] T3.4.3 Manual test with real API key (if available) `[activity: exploratory-testing]`

---

### T4: Update Existing LLM Functions

*Deliverable: `enhance_prompt()` and `generate_prompt_variable_values()` work with LiteLLM.*

- [ ] T4.1 Prime Context
    - [ ] T4.1.1 Re-read `llm_provider.py` focusing on `enhance_prompt` and `generate_prompt_variable_values`
    - [ ] T4.1.2 Note they both call `generate_text()` internally

- [ ] T4.2 Write Tests `[activity: test-execution]`
    - [ ] T4.2.1 Add to `tests/test_llm_provider.py`:
        - `test_enhance_prompt_litellm()` - works in litellm mode
        - `test_generate_variable_values_litellm()` - works in litellm mode
        `[ref: PRD/Feature 1 Acceptance Criteria]`

- [ ] T4.3 Implement `[activity: domain-modeling]`
    - [ ] T4.3.1 Verify `enhance_prompt()` uses `generate_text()` (should work automatically)
    - [ ] T4.3.2 Update `generate_prompt_variable_values()`:
        - In litellm mode, skip `_generate_with_outlines()` (outlines is for local models)
        - Use regular `generate_text()` + JSON parsing
        ```python
        def generate_prompt_variable_values(...):
            config = get_llm_config()
            
            # Skip outlines for litellm mode (cloud APIs)
            if config.mode != LLMMode.LITELLM:
                result = _generate_with_outlines(prompt, count)
                if result:
                    return result[:count + 10]
            
            # Fallback: regular generation + parsing
            response = generate_text(prompt, max_tokens=4096, temperature=0.7)
            # ... existing JSON parsing logic
        ```

- [ ] T4.4 Validate
    - [ ] T4.4.1 Run `uv run pytest tests/test_llm_provider.py -v` `[activity: run-tests]`

---

### T5: Update Setup Wizard `[parallel: true]`

*Deliverable: Setup wizard offers LiteLLM as LLM option.*

- [ ] T5.1 Prime Context
    - [ ] T5.1.1 Read `src/z_explorer/setup_wizard.py`
    - [ ] T5.1.2 Note current LLM configuration flow

- [ ] T5.2 Implement `[activity: component-development]`
    - [ ] T5.2.1 Add LiteLLM option to LLM mode selection:
        ```
        LLM Configuration:
          1. Local (Qwen3-4B) — Runs on your GPU, ~8GB VRAM
          2. Cloud API (LiteLLM) — Use OpenAI, Anthropic, etc. (0 VRAM)
          3. Z-Image Text Encoder — Uses image model's encoder
        ```
    - [ ] T5.2.2 If LiteLLM selected, prompt for provider:
        ```
        Provider:
          1. OpenAI (gpt-4o-mini, gpt-4o)
          2. Anthropic (claude-3-haiku, claude-3.5-sonnet)
          3. Ollama (local API, no key needed)
          4. Other (enter model ID manually)
        ```
    - [ ] T5.2.3 If provider needs API key, show guidance:
        ```
        OpenAI API Key:
          Get your key at: https://platform.openai.com/api-keys
          Enter key (or leave blank to set later):
        ```
    - [ ] T5.2.4 Save configuration to .env:
        - `LLM_MODE=litellm`
        - `LLM_MODEL=openai/gpt-4o-mini`
        - (API key goes to user's shell env, not .env for security)
        `[ref: PRD/Feature 5 Acceptance Criteria]`

- [ ] T5.3 Validate
    - [ ] T5.3.1 Run `uv run ruff check src/z_explorer/setup_wizard.py` `[activity: lint-code]`
    - [ ] T5.3.2 Manual test: run setup wizard `[activity: exploratory-testing]`

---

### T6: Update Documentation

*Deliverable: Updated docs and env.example.*

- [ ] T6.1 Implement `[activity: system-documentation]`
    - [ ] T6.1.1 Update `env.example` with LiteLLM examples:
        ```bash
        # LLM Configuration
        # Local model (default)
        LLM_MODE=hf_download
        LLM_MODEL=unsloth/Qwen3-4B-Instruct-2507-bnb-4bit
        
        # Cloud API via LiteLLM
        # LLM_MODE=litellm
        # LLM_MODEL=openai/gpt-4o-mini
        # Set OPENAI_API_KEY in your environment
        ```
    - [ ] T6.1.2 Update `docs/CONFIGURATION.md` (if exists) with LiteLLM section
    - [ ] T6.1.3 Update `CLAUDE.md` with new LLM modes

- [ ] T6.2 Validate
    - [ ] T6.2.1 Verify documentation is accurate

---

### T7: Integration & End-to-End Validation

*Deliverable: Complete feature verified end-to-end.*

- [ ] T7.1 Backend Validation
    - [ ] T7.1.1 All unit tests passing: `uv run pytest` `[activity: run-tests]`
    - [ ] T7.1.2 Code quality: `uv run ruff check .` passes `[activity: lint-code]`
    - [ ] T7.1.3 Code formatting: `uv run ruff format --check .` passes `[activity: format-code]`

- [ ] T7.2 End-to-End Tests `[activity: exploratory-testing]`
    - [ ] T7.2.1 **Scenario 1**: Set LLM_MODE=litellm, LLM_MODEL=openai/gpt-4o-mini, OPENAI_API_KEY
        - Enhance a prompt → verify cloud API called
        - Generate variable values → verify works
    - [ ] T7.2.2 **Scenario 2**: Set LLM_MODE=hf_download (existing config)
        - Verify local model still works
        - No behavioral changes
    - [ ] T7.2.3 **Scenario 3**: Set LLM_REPO instead of LLM_MODEL
        - Verify deprecation warning shown
        - Verify config still works
    - [ ] T7.2.4 **Scenario 4**: LiteLLM mode without API key
        - Verify clear error message
    - [ ] T7.2.5 **Scenario 5**: Run setup wizard, select LiteLLM option
        - Verify .env updated correctly
        `[ref: SDD/Test Specifications]`

- [ ] T7.3 Performance Validation `[ref: SDD/Quality Requirements]`
    - [ ] T7.3.1 LiteLLM mode uses 0 VRAM for LLM
    - [ ] T7.3.2 API response time <5s for typical prompts
    - [ ] T7.3.3 Error messages are clear and actionable

- [ ] T7.4 PRD Acceptance Verification `[ref: PRD/Feature Requirements]`
    - [ ] T7.4.1 Feature 1: LiteLLM Mode - all criteria met
    - [ ] T7.4.2 Feature 2: LLM_MODEL configuration - all criteria met
    - [ ] T7.4.3 Feature 3: Standard provider env vars - all criteria met
    - [ ] T7.4.4 Feature 4: Backward compatibility - all criteria met
    - [ ] T7.4.5 Feature 5 (Should Have): Setup wizard - all criteria met

---

## Implementation Notes

### Parallel Execution Strategy

T5 (Setup Wizard) can be developed in parallel with T3/T4 (LLM Provider changes):

```
T1 (Dependency) → T2 (Config) → T3 (Generate) → T4 (Functions) → T7 (Validation)
                              ↘
                                T5 (Setup Wizard) ─────────────↗
                              ↘
                                T6 (Docs) ─────────────────────↗
```

### Testing Without Real API Key

For automated tests, mock LiteLLM responses:
```python
from unittest.mock import patch, MagicMock

@patch('litellm.completion')
def test_generate_litellm(mock_completion):
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Enhanced prompt text"
    mock_completion.return_value = mock_response
    
    result = generate_text("test", max_tokens=100)
    assert result == "Enhanced prompt text"
    mock_completion.assert_called_once()
```

### Estimated Effort

| Phase | Effort | Notes |
|-------|--------|-------|
| T1 | 10m | Just add dependency |
| T2 | 1h | Config model changes |
| T3 | 1.5h | Core LiteLLM integration |
| T4 | 30m | Verify existing functions work |
| T5 | 1h | Setup wizard updates |
| T6 | 30m | Documentation |
| T7 | 1h | Testing and validation |

**Total: ~5.5 hours**

---

## Glossary

| Term | Definition |
|------|------------|
| LiteLLM | Python library providing unified interface to 100+ LLM providers |
| Provider | External LLM service (OpenAI, Anthropic, Ollama, etc.) |
| Model ID | Format: `provider/model-name` (e.g., `openai/gpt-4o-mini`) |
| VRAM | Video RAM — local models use it, LiteLLM mode uses 0 |
