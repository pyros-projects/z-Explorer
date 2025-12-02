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
- `[ref: document/section]` - Links to specifications, patterns, or interfaces
- `[activity: type]` - Activity hint for specialist agent selection

---

## Context Priming

*GATE: You MUST fully read all files mentioned in this section before starting any implementation.*

**Specification**:

- `docs/specs/006-lora-support/product-requirements.md` - Product Requirements
- `docs/specs/006-lora-support/solution-design.md` - Solution Design

**Key Design Decisions**:

- ADR-1: Reuse batch parameter syntax (`: lora:weight`)
- ADR-2: Scan LoRA directory at generation time (no restart needed)
- ADR-3: Default weight 0.8
- ADR-4: Keep LoRAs loaded across batch for efficiency

**Implementation Context**:

- Commands to run:
  - Install: `uv sync`
  - Test: `uv run pytest`
  - Lint: `uv run ruff check .`
  - Format: `uv run ruff format .`
  - GUI Dev: `cd src/z_explorer/gui && npm run dev`
  - GUI Build: `cd src/z_explorer/gui && npm run build`
  
- Patterns to follow:
  - Lazy loading pattern (see `image_generator.py`)
  - Progress events pattern (see `core/generator.py`)
  - Configuration pattern (see `model_config.py`)
  
- Dependencies to add:
  - `peft` - For LoRA loading APIs
  - `pyyaml` - For loras.yaml parsing (may already exist)

---

## Implementation Phases

### Phase 1: Core LoRA Configuration & Discovery

- [ ] **T1 LoRA Configuration Module** `[component: backend]`

    - [ ] T1.1 Prime Context
        - [ ] T1.1.1 Read LoraConfig/LoraSpec dataclass specs `[ref: SDD/Data Models]`
        - [ ] T1.1.2 Read YAML metadata loader specs `[ref: SDD/YAML Metadata Loader]`
        - [ ] T1.1.3 Review model_config.py patterns `[ref: src/z_explorer/model_config.py]`
    
    - [ ] T1.2 Write Tests `[activity: test-execution]`
        - [ ] T1.2.1 Test LoraSpec creation with defaults `[ref: PRD/Feature 1]`
        - [ ] T1.2.2 Test LoraConfig.validate() creates missing directory `[ref: PRD/Edge Case 4]`
        - [ ] T1.2.3 Test discover_loras() finds .safetensors files `[ref: PRD/Feature 1]`
        - [ ] T1.2.4 Test resolve_lora() returns path or None `[ref: PRD/Feature 1]`
        - [ ] T1.2.5 Test get_default_weight() returns 0.8 without YAML `[ref: PRD/Feature 7]`
        - [ ] T1.2.6 Test get_default_weight() reads from loras.yaml `[ref: PRD/Feature 7]`
        - [ ] T1.2.7 Test YAML cache invalidation on file change
    
    - [ ] T1.3 Implement `[activity: domain-modeling]`
        - [ ] T1.3.1 Create `src/z_explorer/lora_config.py`
        - [ ] T1.3.2 Implement LoraSpec dataclass
        - [ ] T1.3.3 Implement LoraConfig dataclass with validate(), discover_loras(), resolve_lora()
        - [ ] T1.3.4 Implement get_default_weight() with YAML loading
        - [ ] T1.3.5 Implement get_lora_config() factory function
        - [ ] T1.3.6 Add LORA_DIR to environment variable handling
    
    - [ ] T1.4 Validate
        - [ ] T1.4.1 Run linting `uv run ruff check src/z_explorer/lora_config.py`
        - [ ] T1.4.2 Run tests `uv run pytest tests/test_lora_config.py -v`
        - [ ] T1.4.3 Verify all T1.2 tests pass

---

### Phase 2: Parser Extension

- [ ] **T2 Batch Parameter Parser Update** `[component: backend]`

    - [ ] T2.1 Prime Context
        - [ ] T2.1.1 Read parser algorithm `[ref: SDD/Parser Extension]`
        - [ ] T2.1.2 Review existing parse_batch_params() `[ref: src/z_explorer/cli.py]`
        - [ ] T2.1.3 Understand disambiguation rules `[ref: SDD/BATCH_PARAM_PREFIXES]`
    
    - [ ] T2.2 Write Tests `[activity: test-execution]`
        - [ ] T2.2.1 Test "a cat : x4" returns batch params only `[ref: PRD/Feature 2]`
        - [ ] T2.2.2 Test "a cat : anime" returns LoraSpec with default weight `[ref: PRD/Feature 2]`
        - [ ] T2.2.3 Test "a cat : anime:0.7" returns LoraSpec with explicit weight `[ref: PRD/Feature 2]`
        - [ ] T2.2.4 Test "a cat : anime:0.7, x3" returns both `[ref: PRD/Feature 2]`
        - [ ] T2.2.5 Test "a cat : anime, sketch:0.5" returns multiple LoRAs `[ref: PRD/Feature 3]`
        - [ ] T2.2.6 Test unknown LoRA returns LoraSpec with path=None `[ref: PRD/Feature 2]`
        - [ ] T2.2.7 Test weight clamping (>2.0 clamped to 2.0) `[ref: PRD/Business Rule 2]`
        - [ ] T2.2.8 Test weight clamping (<0 clamped to 0) `[ref: PRD/Business Rule 3]`
        - [ ] T2.2.9 Test batch param prefix takes precedence over LoRA `[ref: PRD/Edge Case 1]`
    
    - [ ] T2.3 Implement `[activity: component-development]`
        - [ ] T2.3.1 Add BATCH_PARAM_PREFIXES constant
        - [ ] T2.3.2 Modify parse_batch_params() signature to return tuple[str, dict, list[LoraSpec]]
        - [ ] T2.3.3 Implement disambiguation logic per SDD algorithm
        - [ ] T2.3.4 Handle weight parsing and clamping
        - [ ] T2.3.5 Update all callers of parse_batch_params()
    
    - [ ] T2.4 Validate
        - [ ] T2.4.1 Run linting `uv run ruff check src/z_explorer/cli.py`
        - [ ] T2.4.2 Run tests `uv run pytest tests/test_cli.py -v`
        - [ ] T2.4.3 Verify all T2.2 tests pass

---

### Phase 3: Image Generator Integration

- [ ] **T3 LoRA Loading in Pipeline** `[component: backend]`

    - [ ] T3.1 Prime Context
        - [ ] T3.1.1 Read image generator extension specs `[ref: SDD/Image Generator Extension]`
        - [ ] T3.1.2 Read progress event timing `[ref: SDD/Progress Event Timing]`
        - [ ] T3.1.3 Review existing generate_image() `[ref: src/z_explorer/image_generator.py]`
        - [ ] T3.1.4 Review peft library LoRA APIs
    
    - [ ] T3.2 Write Tests `[activity: test-execution]`
        - [ ] T3.2.1 Test generate_image() works without LoRAs (backwards compatible)
        - [ ] T3.2.2 Test generate_image() with single LoRA loads weights
        - [ ] T3.2.3 Test generate_image() with multiple LoRAs sets all adapters
        - [ ] T3.2.4 Test LoRA with path=None is skipped with warning
        - [ ] T3.2.5 Test LoRA load failure is caught and generation continues `[ref: PRD/Error Handling]`
    
    - [ ] T3.3 Implement `[activity: component-development]`
        - [ ] T3.3.1 Add `peft` to pyproject.toml dependencies
        - [ ] T3.3.2 Add loras parameter to generate_image() signature
        - [ ] T3.3.3 Implement LoRA loading with pipe.load_lora_weights()
        - [ ] T3.3.4 Implement adapter setting with pipe.set_adapters()
        - [ ] T3.3.5 Add error handling for LoRA load failures
        - [ ] T3.3.6 Add progress events for LoRA loading
    
    - [ ] T3.4 Validate
        - [ ] T3.4.1 Run linting `uv run ruff check src/z_explorer/image_generator.py`
        - [ ] T3.4.2 Run tests `uv run pytest tests/test_image_generator.py -v`
        - [ ] T3.4.3 Verify all T3.2 tests pass

---

### Phase 4: Generator Workflow Integration

- [ ] **T4 Core Generator Updates** `[component: backend]`

    - [ ] T4.1 Prime Context
        - [ ] T4.1.1 Read runtime flow specs `[ref: SDD/Primary Flow]`
        - [ ] T4.1.2 Review existing generate_batch() `[ref: src/z_explorer/core/generator.py]`
    
    - [ ] T4.2 Write Tests `[activity: test-execution]`
        - [ ] T4.2.1 Test generate_batch() passes LoRAs to image generation
        - [ ] T4.2.2 Test progress events show LoRA discovery messages
        - [ ] T4.2.3 Test LoRA + variable: variable resolves first, LoRA applies in Phase 2 `[ref: PRD/Edge Case 3]`
    
    - [ ] T4.3 Implement `[activity: component-development]`
        - [ ] T4.3.1 Update generate_batch() to accept loras parameter
        - [ ] T4.3.2 Add LoRA discovery progress events at 2-3%
        - [ ] T4.3.3 Pass LoRAs to generate_image() in Phase 2
        - [ ] T4.3.4 Add "Generating with N LoRAs" progress message
    
    - [ ] T4.4 Validate
        - [ ] T4.4.1 Run linting `uv run ruff check src/z_explorer/core/generator.py`
        - [ ] T4.4.2 Run tests `uv run pytest tests/test_core/ -v`
        - [ ] T4.4.3 Verify all T4.2 tests pass

---

### Phase 5: CLI & Server Integration

- [ ] **T5.1 CLI Integration** `[parallel: true]` `[component: backend]`

    - [ ] T5.1.1 Prime Context
        - [ ] Read /loras command spec `[ref: SDD/CLI /loras Command]`
        - [ ] Review existing CLI command handling `[ref: src/z_explorer/cli.py]`
    
    - [ ] T5.1.2 Write Tests `[activity: test-execution]`
        - [ ] Test /loras command outputs directory and files `[ref: PRD/Feature 8]`
        - [ ] Test /loras with empty directory shows helpful message
        - [ ] Test interactive loop uses new parse_batch_params() return
    
    - [ ] T5.1.3 Implement `[activity: component-development]`
        - [ ] Add handle_loras_command() function
        - [ ] Add /loras command handling in interactive loop
        - [ ] Update generation call to pass loras from parser
    
    - [ ] T5.1.4 Validate
        - [ ] Run tests `uv run pytest tests/test_cli.py -v`

- [ ] **T5.2 Server Integration** `[parallel: true]` `[component: backend]`

    - [ ] T5.2.1 Prime Context
        - [ ] Read settings API extension `[ref: SDD/Settings API Extension]`
        - [ ] Review existing /api/settings/models `[ref: src/z_explorer/server.py]`
    
    - [ ] T5.2.2 Write Tests `[activity: test-execution]`
        - [ ] Test GET /api/loras returns available LoRAs `[ref: PRD/Feature 5]`
        - [ ] Test POST /api/settings/models accepts lora_dir `[ref: PRD/Feature 4]`
        - [ ] Test lora_dir creates directory if missing
        - [ ] Test SSE stream includes LoRA progress messages `[ref: PRD/Feature 6]`
    
    - [ ] T5.2.3 Implement `[activity: api-development]`
        - [ ] Add lora_dir to ModelSettingsUpdate
        - [ ] Add GET /api/loras endpoint
        - [ ] Update settings handler for lora_dir
        - [ ] Pass LoRAs through SSE generation endpoint
    
    - [ ] T5.2.4 Validate
        - [ ] Run tests `uv run pytest tests/test_server.py -v`

---

### Phase 6: GUI Integration

- [ ] **T6.1 Settings Dialog** `[parallel: true]` `[component: frontend]`

    - [ ] T6.1.1 Prime Context
        - [ ] Review Settings.svelte structure `[ref: src/z_explorer/gui/src/lib/components/Settings.svelte]`
        - [ ] Read settings store pattern `[ref: src/z_explorer/gui/src/lib/stores/]`
    
    - [ ] T6.1.2 Implement `[activity: component-development]`
        - [ ] Add lora_dir to settings store
        - [ ] Add LoRA Directory input field in Models tab
        - [ ] Add validation and save logic
    
    - [ ] T6.1.3 Validate
        - [ ] Run type check `cd src/z_explorer/gui && npm run check`
        - [ ] Manual test: Settings dialog shows LoRA directory field

- [ ] **T6.2 FakeCLI Autocomplete** `[parallel: true]` `[component: frontend]`

    - [ ] T6.2.1 Prime Context
        - [ ] Read autocomplete integration spec `[ref: SDD/GUI Autocomplete Integration]`
        - [ ] Review FakeCLI.svelte `[ref: src/z_explorer/gui/src/lib/components/FakeCLI.svelte]`
    
    - [ ] T6.2.2 Implement `[activity: component-development]`
        - [ ] Fetch available LoRAs from /api/loras on mount
        - [ ] Add LoRA suggestions after ':' in input
        - [ ] Show weight hint in suggestions (e.g., "anime:0.8")
    
    - [ ] T6.2.3 Validate
        - [ ] Run type check `cd src/z_explorer/gui && npm run check`
        - [ ] Manual test: Typing ":" shows LoRA suggestions

- [ ] **T6.3 Build GUI**
    - [ ] T6.3.1 Run `cd src/z_explorer/gui && npm run build`
    - [ ] T6.3.2 Verify build succeeds without errors

---

### Phase 7: Integration & End-to-End Validation

- [ ] **T7 Final Validation** `[activity: test-execution]`

    - [ ] T7.1 All unit tests passing
        - [ ] `uv run pytest --cov`
        - [ ] Coverage meets standards (>80% for new code)
    
    - [ ] T7.2 Integration tests
        - [ ] Test full flow: prompt with LoRA → parsed → loaded → generated
        - [ ] Test CLI mode end-to-end
        - [ ] Test web UI mode end-to-end
    
    - [ ] T7.3 Manual E2E tests
        - [ ] Test: Drop anime.safetensors in loras/, type "a cat : anime", verify styled output
        - [ ] Test: "a cat : anime:0.7, sketch:0.5, x2" generates 2 styled images
        - [ ] Test: "a cat : missing" shows warning, generates without LoRA
        - [ ] Test: /loras command shows available LoRAs
        - [ ] Test: Settings dialog LoRA directory field works
        - [ ] Test: Autocomplete shows LoRAs after ":"
    
    - [ ] T7.4 Performance validation `[ref: SDD/Quality Requirements]`
        - [ ] LoRA load time <500ms
        - [ ] Generation overhead <5% vs without LoRA
    
    - [ ] T7.5 Error handling validation
        - [ ] Invalid weight clamped with warning
        - [ ] Missing LoRA warned, generation continues
        - [ ] Corrupted LoRA skipped, generation continues
    
    - [ ] T7.6 PRD acceptance criteria verification
        - [ ] Feature 1: LoRA File Discovery ✓
        - [ ] Feature 2: Prompt Syntax ✓
        - [ ] Feature 3: Multiple LoRA Support ✓
        - [ ] Feature 4: Directory Configuration ✓
        - [ ] Feature 5: Autocomplete ✓
        - [ ] Feature 6: Progress Feedback ✓
        - [ ] Feature 7: Metadata File (optional) ✓
        - [ ] Feature 8: /loras Command ✓
    
    - [ ] T7.7 Code quality
        - [ ] `uv run ruff check .` passes
        - [ ] `uv run ruff format --check .` passes
    
    - [ ] T7.8 Documentation
        - [ ] Update README if needed
        - [ ] Update CLAUDE.md with LoRA info

---

## Dependency Graph

```
T1 (LoRA Config)
    ↓
T2 (Parser) ←── depends on T1 for LoraSpec, get_lora_config()
    ↓
T3 (Image Generator) ←── depends on T1 for LoraSpec
    ↓
T4 (Core Generator) ←── depends on T2, T3
    ↓
T5.1 (CLI) ←── depends on T2, T4 ──┐
T5.2 (Server) ←── depends on T1, T4 ─┼── [parallel]
    ↓                                 │
T6.1 (Settings) ←── depends on T5.2 ─┤
T6.2 (Autocomplete) ←── depends on T5.2 ─┘ [parallel]
    ↓
T7 (Integration) ←── depends on all above
```

---

## Estimated Effort

| Phase | Effort | Notes |
|-------|--------|-------|
| T1: LoRA Config | 1-2 hours | New module, straightforward |
| T2: Parser | 1-2 hours | Modify existing, well-defined |
| T3: Image Generator | 1-2 hours | peft integration |
| T4: Core Generator | 1 hour | Wire up existing pieces |
| T5: CLI & Server | 1-2 hours | Parallel, mostly wiring |
| T6: GUI | 1-2 hours | Parallel, Svelte updates |
| T7: Integration | 1-2 hours | Testing and validation |
| **Total** | **7-13 hours** | |
