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
- `[ref: document/section; lines: 1, 2-3]` - Links to specifications, patterns, or interfaces and (if applicable) line(s)
- `[activity: type]` - Activity hint for specialist agent selection

---

## Context Priming

*GATE: You MUST fully read all files mentioned in this section before starting any implementation.*

**Specification**:

- `docs/specs/002-info-flyout-metadata/product-requirements.md` - Product Requirements
- `docs/specs/002-info-flyout-metadata/solution-design.md` - Solution Design
- `docs/specs/concepts/info-flyout/DESIGN.md` - Original design notes and mockups
- `docs/specs/concepts/info-flyout/mockup-info-overlay.html` - Visual reference for panel design

**Key Design Decisions**:

- **ADR-1**: JSON sidecar files for metadata (not PNG metadata chunks)
- **ADR-2**: Slide-in panel from right, 320px fixed width
- **ADR-3**: Lazy loading metadata (load on panel open, not gallery load)
- **ADR-4**: Additive API changes only (backward compatible)

**Implementation Context**:

- Backend commands: `uv run pytest`, `uv run ruff check .`, `uv run ruff format .`
- Frontend commands: `npm run check`, `npm run test`, `npm run build` (in `src/z_explorer/gui/`)
- Patterns: SSE streaming, Pydantic models, Svelte stores
- Key interfaces: `ImageData` (frontend), `ImageMetadata` (backend), `ImageInfo` (API)

---

## Implementation Phases

### T1: Backend Metadata Foundation

*Deliverable: Metadata utilities for saving/loading JSON sidecar files alongside images.*

- [ ] T1.1 Prime Context
    - [ ] T1.1.1 Read `src/z_explorer/core/types.py` for existing models `[ref: SDD/Application Data Models]`
    - [ ] T1.1.2 Read `src/z_explorer/core/generator.py` for image_saved event `[ref: SDD/Runtime View]`
    - [ ] T1.1.3 Read `src/z_explorer/server.py` for ImageInfo model `[ref: SDD/Internal API Changes]`

- [ ] T1.2 Write Tests `[activity: test-execution]`
    - [ ] T1.2.1 Create `tests/test_metadata.py` with:
        - `test_metadata_save_creates_sidecar()` - saves JSON alongside image path
        - `test_metadata_load_returns_data()` - round-trip write/read
        - `test_metadata_load_missing_returns_none()` - graceful None for missing file
        - `test_metadata_load_corrupted_returns_none()` - graceful None for invalid JSON
        - `test_sidecar_path_calculation()` - `.png` → `.json` path conversion
        `[ref: PRD/Feature 1 Acceptance Criteria]`

- [ ] T1.3 Implement `[activity: domain-modeling]`
    - [ ] T1.3.1 Add `ImageMetadata` model to `src/z_explorer/core/types.py`:
        ```python
        class ImageMetadata(BaseModel):
            original_prompt: str
            final_prompt: str
            seed: int
            width: int
            height: int
            created_at: str  # ISO 8601
            enhanced: bool = False
            model: Optional[str] = None
        ```
        `[ref: SDD/Application Data Models]`
    
    - [ ] T1.3.2 Create `src/z_explorer/core/metadata.py` with:
        - `get_sidecar_path(image_path: Path) -> Path`
        - `save_metadata(image_path: Path, metadata: ImageMetadata) -> bool`
        - `load_metadata(image_path: Path) -> Optional[ImageMetadata]`
        - Use atomic writes (temp file + rename)
        `[ref: SDD/Metadata Utility Pattern]`

- [ ] T1.4 Validate
    - [ ] T1.4.1 Run `uv run ruff check src/z_explorer/core/metadata.py` `[activity: lint-code]`
    - [ ] T1.4.2 Run `uv run ruff format src/z_explorer/core/metadata.py` `[activity: format-code]`
    - [ ] T1.4.3 Run `uv run pytest tests/test_metadata.py -v` `[activity: run-tests]`
    - [ ] T1.4.4 Verify all tests pass `[activity: business-acceptance]`

---

### T2: Generator Integration

*Deliverable: Generator saves metadata sidecar files when images are created.*

- [ ] T2.1 Prime Context
    - [ ] T2.1.1 Read `src/z_explorer/core/generator.py` fully, note `_emit` function and `image_saved` event
    - [ ] T2.1.2 Trace prompt flow: original → variable substitution → enhancement → final
    - [ ] T2.1.3 Identify where to capture `original_prompt` before processing

- [ ] T2.2 Write Tests `[activity: test-execution]`
    - [ ] T2.2.1 Add to `tests/test_generator.py` or create new:
        - `test_generation_creates_sidecar_file()` - sidecar exists after generation
        - `test_sidecar_contains_both_prompts()` - original and final prompts differ when variables used
        - `test_sidecar_contains_seed_and_dimensions()` - metadata fields populated
        - `test_enhanced_flag_set_when_using_operator()` - `>` operator sets `enhanced=True`
        `[ref: PRD/Feature 1 Acceptance Criteria]`

- [ ] T2.3 Implement `[activity: domain-modeling]`
    - [ ] T2.3.1 Modify generator to track `original_prompt` before variable substitution
    - [ ] T2.3.2 After image save, call `save_metadata()` with collected data
    - [ ] T2.3.3 Extend `image_saved` SSE event to include new metadata fields:
        - `original_prompt`, `final_prompt`, `seed`, `width`, `height`, `created_at`, `enhanced`
        `[ref: SDD/Runtime View - Generate Image with Metadata]`

- [ ] T2.4 Validate
    - [ ] T2.4.1 Run `uv run ruff check src/z_explorer/core/generator.py` `[activity: lint-code]`
    - [ ] T2.4.2 Run `uv run pytest tests/ -k generator -v` `[activity: run-tests]`
    - [ ] T2.4.3 Manual test: generate image, verify `.json` sidecar created `[activity: exploratory-testing]`

---

### T3: API Extension

*Deliverable: `/api/images` endpoint returns metadata from sidecar files.*

- [ ] T3.1 Prime Context
    - [ ] T3.1.1 Read `src/z_explorer/server.py` focusing on `ImageInfo` model and `list_images` endpoint
    - [ ] T3.1.2 Note current `.txt` file reading for prompts

- [ ] T3.2 Write Tests `[activity: test-execution]`
    - [ ] T3.2.1 Add to `tests/test_server/test_endpoints.py`:
        - `test_list_images_includes_metadata()` - new fields in response
        - `test_list_images_graceful_without_sidecar()` - images without sidecar still listed
        - `test_image_metadata_endpoint()` - single image metadata retrieval
        `[ref: SDD/Internal API Changes]`

- [ ] T3.3 Implement `[activity: api-development]`
    - [ ] T3.3.1 Extend `ImageInfo` model with optional fields:
        ```python
        original_prompt: Optional[str] = None
        seed: Optional[int] = None
        width: Optional[int] = None
        height: Optional[int] = None
        created_at: Optional[str] = None
        enhanced: Optional[bool] = None
        ```
    - [ ] T3.3.2 Modify `list_images` to load metadata from sidecar files
    - [ ] T3.3.3 (Optional) Add `GET /api/images/{filename}/metadata` endpoint for lazy loading
        `[ref: SDD/Internal API Changes]`

- [ ] T3.4 Validate
    - [ ] T3.4.1 Run `uv run ruff check src/z_explorer/server.py` `[activity: lint-code]`
    - [ ] T3.4.2 Run `uv run pytest tests/test_server/ -v` `[activity: run-tests]`
    - [ ] T3.4.3 Manual test: call `/api/images`, verify metadata fields present `[activity: exploratory-testing]`

---

### T4: Frontend - Info Button Component `[parallel: true]` `[component: InfoButton]`

*Deliverable: ⓘ button overlay in lightbox.*

- [ ] T4.1 Prime Context
    - [ ] T4.1.1 Read `src/z_explorer/gui/src/App.svelte` focusing on lightbox (`preview-overlay`, `selectedImage`)
    - [ ] T4.1.2 Review mockup: `docs/specs/concepts/info-flyout/mockup-info-overlay.html`

- [ ] T4.2 Write Tests `[activity: test-execution]`
    - [ ] T4.2.1 Create `src/z_explorer/gui/src/lib/InfoButton.test.ts`:
        - `test_info_button_renders()` - button visible
        - `test_info_button_click_emits_event()` - dispatches toggle event
        - `test_info_button_keyboard_accessible()` - focusable, Enter/Space activate
        `[ref: PRD/Feature 2 Acceptance Criteria]`

- [ ] T4.3 Implement `[activity: component-development]`
    - [ ] T4.3.1 Create `src/z_explorer/gui/src/lib/InfoButton.svelte`:
        - Positioned bottom-right of lightbox image
        - Semi-transparent with hover effect
        - Emits `toggle` event on click
        - Supports keyboard activation
        ```svelte
        <button class="info-button" on:click={() => dispatch('toggle')}>ⓘ</button>
        ```
        `[ref: SDD/Building Block View]`

- [ ] T4.4 Validate
    - [ ] T4.4.1 Run `npm run check` in gui directory `[activity: lint-code]`
    - [ ] T4.4.2 Run `npm run test` `[activity: run-tests]`

---

### T5: Frontend - Info Panel Component `[parallel: true]` `[component: InfoPanel]`

*Deliverable: Slide-in metadata panel.*

- [ ] T5.1 Prime Context
    - [ ] T5.1.1 Review mockup: `docs/specs/concepts/info-flyout/mockup-info-overlay.html`
    - [ ] T5.1.2 Note ImageData interface extension needed

- [ ] T5.2 Write Tests `[activity: test-execution]`
    - [ ] T5.2.1 Create `src/z_explorer/gui/src/lib/InfoPanel.test.ts`:
        - `test_panel_renders_with_metadata()` - shows all fields
        - `test_panel_shows_not_available()` - graceful for missing data
        - `test_copy_original_button_works()` - clipboard integration
        - `test_copy_final_button_works()` - clipboard integration
        - `test_panel_close_button()` - dispatches close event
        `[ref: PRD/Feature 3, Feature 4 Acceptance Criteria]`

- [ ] T5.3 Implement `[activity: component-development]`
    - [ ] T5.3.1 Extend `ImageData` interface in `App.svelte`:
        ```typescript
        interface ImageData {
          url: string;
          prompt?: string;
          originalPrompt?: string;
          finalPrompt?: string;
          seed?: number;
          width?: number;
          height?: number;
          createdAt?: string;
          enhanced?: boolean;
        }
        ```
    - [ ] T5.3.2 Create `src/z_explorer/gui/src/lib/InfoPanel.svelte`:
        - 320px width, slides from right
        - Uses Svelte `fly` transition (x: 320, duration: 300)
        - Displays all metadata fields
        - Copy buttons with clipboard API
        - Close button and outside click handler
        `[ref: SDD/Component Structure Pattern]`

- [ ] T5.4 Validate
    - [ ] T5.4.1 Run `npm run check` `[activity: lint-code]`
    - [ ] T5.4.2 Run `npm run test` `[activity: run-tests]`

---

### T6: Frontend - Lightbox Integration

*Deliverable: Info button and panel wired into existing lightbox.*

- [ ] T6.1 Prime Context
    - [ ] T6.1.1 Re-read `App.svelte` lightbox section after T4/T5 complete
    - [ ] T6.1.2 Plan state management: `showInfoPanel: boolean`

- [ ] T6.2 Implement `[activity: component-development]`
    - [ ] T6.2.1 Import `InfoButton` and `InfoPanel` in `App.svelte`
    - [ ] T6.2.2 Add `showInfoPanel` state variable
    - [ ] T6.2.3 Add keyboard handler for `i` key to toggle panel
    - [ ] T6.2.4 Modify Escape handler: close panel first, then lightbox
    - [ ] T6.2.5 Wire up components in lightbox template:
        ```svelte
        {#if selectedImage}
          <div class="preview-overlay">
            <!-- existing image display -->
            <InfoButton on:toggle={() => showInfoPanel = !showInfoPanel} />
            <InfoPanel 
              imageData={selectedImage}
              visible={showInfoPanel}
              onClose={() => showInfoPanel = false}
            />
          </div>
        {/if}
        ```
    - [ ] T6.2.6 Close panel when `selectedImage` changes (navigation)
        `[ref: SDD/Runtime View - View Image Metadata]`

- [ ] T6.3 Validate
    - [ ] T6.3.1 Run `npm run check` `[activity: lint-code]`
    - [ ] T6.3.2 Run `npm run build` - ensure production build succeeds `[activity: run-tests]`
    - [ ] T6.3.3 Manual test: full user flow (lightbox → button → panel → copy → close) `[activity: exploratory-testing]`

---

### T7: Integration & End-to-End Validation

*Deliverable: Complete feature verified end-to-end.*

- [ ] T7.1 Backend Validation
    - [ ] T7.1.1 All unit tests passing: `uv run pytest` `[activity: run-tests]`
    - [ ] T7.1.2 Code quality: `uv run ruff check .` passes `[activity: lint-code]`
    - [ ] T7.1.3 Code formatting: `uv run ruff format --check .` passes `[activity: format-code]`

- [ ] T7.2 Frontend Validation
    - [ ] T7.2.1 Type checking: `npm run check` passes `[activity: lint-code]`
    - [ ] T7.2.2 Unit tests: `npm run test` passes `[activity: run-tests]`
    - [ ] T7.2.3 Production build: `npm run build` succeeds `[activity: run-tests]`

- [ ] T7.3 End-to-End Tests `[activity: exploratory-testing]`
    - [ ] T7.3.1 **Scenario 1**: Generate image with variables → verify sidecar created with both prompts
    - [ ] T7.3.2 **Scenario 2**: Generate with `>` enhancement → verify `enhanced: true` in sidecar
    - [ ] T7.3.3 **Scenario 3**: Open lightbox → click ⓘ → verify panel shows all metadata
    - [ ] T7.3.4 **Scenario 4**: Press `i` key → verify panel toggles
    - [ ] T7.3.5 **Scenario 5**: Press Escape → verify panel closes (lightbox stays)
    - [ ] T7.3.6 **Scenario 6**: Copy prompts → verify clipboard contains correct text
    - [ ] T7.3.7 **Scenario 7**: Image without sidecar → verify graceful "not available" message
        `[ref: SDD/Test Specifications - Critical Test Scenarios]`

- [ ] T7.4 Performance Validation `[ref: SDD/Quality Requirements]`
    - [ ] T7.4.1 Panel open animation completes in <300ms
    - [ ] T7.4.2 Metadata loads in <50ms (local files)
    - [ ] T7.4.3 Gallery load time not increased significantly

- [ ] T7.5 PRD Acceptance Verification `[ref: PRD/Feature Requirements]`
    - [ ] T7.5.1 Feature 1: Metadata Sidecar Files - all criteria met
    - [ ] T7.5.2 Feature 2: Info Button Overlay - all criteria met
    - [ ] T7.5.3 Feature 3: Info Panel - all criteria met
    - [ ] T7.5.4 Feature 4: Copy Prompt Actions - all criteria met
    - [ ] T7.5.5 Feature 5 (Should Have): Extended Metadata Display - enhanced flag, model shown

- [ ] T7.6 Documentation `[activity: system-documentation]`
    - [ ] T7.6.1 Update CLAUDE.md if new commands or patterns added
    - [ ] T7.6.2 Any API changes documented in relevant files

---

## Implementation Notes

### Parallel Execution Strategy

Phases T4 and T5 (InfoButton and InfoPanel components) can be developed in parallel since they are independent Svelte components. T6 (integration) depends on both completing first.

```
T1 → T2 → T3 → [T4, T5] → T6 → T7
                  ↓   ↓
              (parallel)
```

### Risk Mitigation

1. **Atomic file writes**: Use temp file + rename pattern in `metadata.py` to prevent corruption
2. **Clipboard API fallback**: If `navigator.clipboard` fails, show error toast with manual copy instructions  
3. **Backward compatibility**: All new API fields are `Optional`, existing clients unaffected

### Estimated Effort

| Phase | Effort | Notes |
|-------|--------|-------|
| T1 | 1h | Core utilities, straightforward |
| T2 | 2h | Generator has complexity, needs careful prompt tracking |
| T3 | 1h | Additive changes to existing endpoint |
| T4 | 30m | Simple button component |
| T5 | 2h | Panel with styling, copy functionality |
| T6 | 1h | Integration and keyboard handling |
| T7 | 1h | Testing and validation |

**Total: ~8-9 hours**

---

## Glossary

| Term | Definition |
|------|------------|
| Sidecar File | JSON file stored alongside image with metadata |
| Original Prompt | User's input before variable substitution |
| Final Prompt | Prompt after variables resolved and enhancement applied |
| Lightbox | Full-screen image preview overlay |
| Flyout/Panel | Slide-in metadata display from right edge |
