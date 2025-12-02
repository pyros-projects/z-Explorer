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

- `docs/specs/003-gallery-search/product-requirements.md` - Product Requirements
- `docs/specs/003-gallery-search/solution-design.md` - Solution Design
- `docs/specs/002-info-flyout-metadata/solution-design.md` - Dependency: metadata sidecar format

**Key Design Decisions**:

- **ADR-1**: Client-side filtering for Gallery (instant feedback)
- **ADR-2**: Server-side search for CLI (structured response)
- **ADR-3**: AND logic for multiple search terms
- **ADR-4**: Extend existing `/api/images` endpoint with optional `q` parameter

**Implementation Context**:

- Backend commands: `uv run pytest`, `uv run ruff check .`, `uv run ruff format .`
- Frontend commands: `npm run check`, `npm run test`, `npm run build` (in `src/z_explorer/gui/`)
- Key files: `Gallery.svelte`, `FakeCLI.svelte`, `server.py`
- Dependency: Spec 002 must be implemented first (metadata sidecars)

**Pre-requisite Check**:
Before implementing this spec, verify spec 002 is complete:
- [ ] `src/z_explorer/core/metadata.py` exists with `load_metadata()` function
- [ ] Images have `.json` sidecar files with `original_prompt` and `final_prompt`

---

## Implementation Phases

### T1: Backend Search Endpoint

*Deliverable: `/api/images` extended with search query parameter.*

- [ ] T1.1 Prime Context
    - [ ] T1.1.1 Read `src/z_explorer/server.py` focusing on `ImageInfo` model and `list_images` endpoint `[ref: SDD/Internal API Changes]`
    - [ ] T1.1.2 Read `src/z_explorer/core/metadata.py` for `load_metadata()` usage `[ref: spec 002]`
    - [ ] T1.1.3 Review search algorithm in SDD `[ref: SDD/Runtime View - Search Algorithm]`

- [ ] T1.2 Write Tests `[activity: test-execution]`
    - [ ] T1.2.1 Create/extend `tests/test_server/test_search.py`:
        - `test_search_returns_filtered_images()` - basic search with `q` param
        - `test_search_case_insensitive()` - "CAT" matches "cat"
        - `test_search_multiple_terms_and()` - all terms must match
        - `test_search_creates_snippet()` - snippet around match
        - `test_search_no_query_returns_all()` - empty/missing `q` returns all
        - `test_search_missing_sidecar_excluded()` - graceful handling
        - `test_search_echoes_query()` - response includes query field
        `[ref: PRD/Feature 2 Acceptance Criteria]`

- [ ] T1.3 Implement `[activity: api-development]`
    - [ ] T1.3.1 Add `match_field` and `snippet` to `ImageInfo` model
    - [ ] T1.3.2 Add `query` field to `ImagesResponse` model
    - [ ] T1.3.3 Create `matches_query()` helper function:
        ```python
        def matches_query(metadata: ImageMetadata, query: str) -> tuple[bool, str, str]:
            # AND logic for multiple terms, case-insensitive
        ```
    - [ ] T1.3.4 Create `create_snippet()` helper function:
        ```python
        def create_snippet(text: str, term: str, context: int = 30) -> str:
            # ~60 char snippet centered on match
        ```
    - [ ] T1.3.5 Modify `list_images()` to accept optional `q: str = None` parameter
    - [ ] T1.3.6 When `q` is provided, filter images using `matches_query()`
        `[ref: SDD/Search Algorithm]`

- [ ] T1.4 Validate
    - [ ] T1.4.1 Run `uv run ruff check src/z_explorer/server.py` `[activity: lint-code]`
    - [ ] T1.4.2 Run `uv run ruff format src/z_explorer/server.py` `[activity: format-code]`
    - [ ] T1.4.3 Run `uv run pytest tests/test_server/test_search.py -v` `[activity: run-tests]`
    - [ ] T1.4.4 Manual test: `curl "localhost:8345/api/images?q=cat"` `[activity: exploratory-testing]`

---

### T2: Frontend SearchBox Component `[parallel: true]` `[component: SearchBox]`

*Deliverable: Reusable search input component with debounce.*

- [ ] T2.1 Prime Context
    - [ ] T2.1.1 Review SearchBox pattern in SDD `[ref: SDD/Component Structure Pattern]`
    - [ ] T2.1.2 Review existing Svelte patterns in `src/z_explorer/gui/src/lib/`

- [ ] T2.2 Write Tests `[activity: test-execution]`
    - [ ] T2.2.1 Create `src/z_explorer/gui/src/lib/__tests__/SearchBox.test.ts`:
        - `test_search_box_renders()` - component displays input
        - `test_debounce_fires_after_300ms()` - event timing
        - `test_escape_clears_input()` - keyboard handling
        - `test_filter_event_dispatched()` - event with query
        - `test_result_count_displayed()` - count formatting
        `[ref: PRD/Feature 1 Acceptance Criteria]`

- [ ] T2.3 Implement `[activity: component-development]`
    - [ ] T2.3.1 Create `src/z_explorer/gui/src/lib/SearchBox.svelte`:
        - Props: `totalCount`, `resultCount`, `isActive`
        - Events: `filter` (with query), `clear`
        - 300ms debounce on input
        - Escape key clears and dispatches `clear`
        - Search icon and result count display
        `[ref: SDD/Component Structure Pattern]`
    - [ ] T2.3.2 Add CSS styling matching Gallery header aesthetic

- [ ] T2.4 Validate
    - [ ] T2.4.1 Run `npm run check` in gui directory `[activity: lint-code]`
    - [ ] T2.4.2 Run `npm run test` `[activity: run-tests]`

---

### T3: Gallery Integration `[component: Gallery]`

*Deliverable: Search box in Gallery header with client-side filtering.*

- [ ] T3.1 Prime Context
    - [ ] T3.1.1 Read `src/z_explorer/gui/src/lib/Gallery.svelte` fully
    - [ ] T3.1.2 Note `images` prop and how it's passed to layout components

- [ ] T3.2 Write Tests `[activity: test-execution]`
    - [ ] T3.2.1 Add to `src/z_explorer/gui/src/lib/__tests__/Gallery.test.ts`:
        - `test_gallery_includes_search_box()` - SearchBox rendered
        - `test_gallery_filters_on_search()` - filtered images passed to layout
        - `test_gallery_shows_result_count()` - count updates
        - `test_gallery_clears_filter_on_escape()` - full gallery restored
        - `test_empty_search_shows_all()` - no filter applied
        `[ref: PRD/Feature 1 Acceptance Criteria]`

- [ ] T3.3 Implement `[activity: component-development]`
    - [ ] T3.3.1 Import `SearchBox` component
    - [ ] T3.3.2 Add search state variables:
        ```typescript
        let searchQuery = '';
        let filteredImages: ImageData[] = [];
        $: filteredImages = filterImages(images, searchQuery);
        ```
    - [ ] T3.3.3 Create `filterImages()` function:
        ```typescript
        function filterImages(images: ImageData[], query: string): ImageData[] {
          if (!query || query.length < 2) return images;
          const terms = query.toLowerCase().split(' ');
          return images.filter(img => {
            const original = (img.originalPrompt || '').toLowerCase();
            const final = (img.finalPrompt || img.prompt || '').toLowerCase();
            return terms.every(term => original.includes(term) || final.includes(term));
          });
        }
        ```
    - [ ] T3.3.4 Add SearchBox to gallery header:
        ```svelte
        <SearchBox
          totalCount={images.length}
          resultCount={filteredImages.length}
          isActive={searchQuery.length >= 2}
          on:filter={(e) => searchQuery = e.detail.query}
          on:clear={() => searchQuery = ''}
        />
        ```
    - [ ] T3.3.5 Pass `filteredImages` to layout components instead of `images`
    - [ ] T3.3.6 Add empty state for no search results:
        ```svelte
        {#if filteredImages.length === 0 && searchQuery.length >= 2}
          <div class="no-results">No images found for "{searchQuery}"</div>
        {/if}
        ```
        `[ref: SDD/Runtime View - Primary Flow]`

- [ ] T3.4 Validate
    - [ ] T3.4.1 Run `npm run check` `[activity: lint-code]`
    - [ ] T3.4.2 Run `npm run test` `[activity: run-tests]`
    - [ ] T3.4.3 Manual test: type in search, verify filtering works `[activity: exploratory-testing]`

---

### T4: CLI Search Command `[component: FakeCLI]`

*Deliverable: `/search` command in CLI with backend integration.*

- [ ] T4.1 Prime Context
    - [ ] T4.1.1 Read `src/z_explorer/gui/src/lib/FakeCLI.svelte` focusing on `handleCommand`
    - [ ] T4.1.2 Review CLI command pattern in SDD `[ref: SDD/CLI Command Pattern]`

- [ ] T4.2 Write Tests `[activity: test-execution]`
    - [ ] T4.2.1 Add to FakeCLI tests:
        - `test_search_command_recognized()` - /search is valid command
        - `test_search_no_args_shows_usage()` - help text displayed
        - `test_search_displays_results()` - formatted output
        `[ref: PRD/Feature 3 Acceptance Criteria]`

- [ ] T4.3 Implement `[activity: component-development]`
    - [ ] T4.3.1 Add `/search` to `commands` array
    - [ ] T4.3.2 Update `/help` command to include `/search` documentation
    - [ ] T4.3.3 Add `/search` case to `handleCommand` switch:
        - Show usage if no args
        - Call `/api/images?q=...` endpoint
        - Format and display results with snippets
        - Handle 0 results and 20+ results cases
        `[ref: SDD/CLI Command Pattern]`

- [ ] T4.4 Validate
    - [ ] T4.4.1 Run `npm run check` `[activity: lint-code]`
    - [ ] T4.4.2 Run `npm run test` `[activity: run-tests]`
    - [ ] T4.4.3 Manual test: run `/search` commands in CLI `[activity: exploratory-testing]`

---

### T5: Integration & End-to-End Validation

*Deliverable: Complete feature verified end-to-end.*

- [ ] T5.1 Backend Validation
    - [ ] T5.1.1 All unit tests passing: `uv run pytest` `[activity: run-tests]`
    - [ ] T5.1.2 Code quality: `uv run ruff check .` passes `[activity: lint-code]`
    - [ ] T5.1.3 Code formatting: `uv run ruff format --check .` passes `[activity: format-code]`

- [ ] T5.2 Frontend Validation
    - [ ] T5.2.1 Type checking: `npm run check` passes `[activity: lint-code]`
    - [ ] T5.2.2 Unit tests: `npm run test` passes `[activity: run-tests]`
    - [ ] T5.2.3 Production build: `npm run build` succeeds `[activity: run-tests]`

- [ ] T5.3 End-to-End Tests `[activity: exploratory-testing]`
    - [ ] T5.3.1 **Scenario 1**: Generate images with various prompts
    - [ ] T5.3.2 **Scenario 2**: Type in gallery search → verify filtering works
    - [ ] T5.3.3 **Scenario 3**: Press Escape → verify full gallery restored
    - [ ] T5.3.4 **Scenario 4**: Search for non-existent term → verify "no results" message
    - [ ] T5.3.5 **Scenario 5**: Use `/search` in CLI → verify results with snippets
    - [ ] T5.3.6 **Scenario 6**: Multi-word search ("emo corset") → verify AND logic
    - [ ] T5.3.7 **Scenario 7**: Images without sidecars → verify excluded from search but visible in gallery
        `[ref: SDD/Test Specifications]`

- [ ] T5.4 Performance Validation `[ref: SDD/Quality Requirements]`
    - [ ] T5.4.1 Gallery filter completes in <50ms for 100 images
    - [ ] T5.4.2 API search responds in <200ms
    - [ ] T5.4.3 Debounce timing is correct (300ms)

- [ ] T5.5 PRD Acceptance Verification `[ref: PRD/Feature Requirements]`
    - [ ] T5.5.1 Feature 1: Gallery Search Box - all criteria met
    - [ ] T5.5.2 Feature 2: Full-Text Prompt Search - all criteria met
    - [ ] T5.5.3 Feature 3: CLI Search Command - all criteria met

---

## Implementation Notes

### Dependency on Spec 002

This spec **requires** spec 002 (Info Flyout & Metadata) to be implemented first:
- Search reads from `.json` sidecar files
- Uses `load_metadata()` from `core/metadata.py`
- Relies on `original_prompt` and `final_prompt` fields

If spec 002 is not complete, T1 will fail on metadata loading.

### Parallel Execution Strategy

T2 (SearchBox component) can be developed in parallel with T1 (backend search):

```
T1 (Backend) ───────┬─── T3 (Gallery Integration) ─── T4 (CLI) ─── T5 (Validation)
                    │
T2 (SearchBox) ─────┘
```

### Estimated Effort

| Phase | Effort | Notes |
|-------|--------|-------|
| T1 | 1.5h | Server-side search logic |
| T2 | 1h | Simple component with debounce |
| T3 | 1.5h | Gallery integration and filtering |
| T4 | 1h | CLI command implementation |
| T5 | 1h | Testing and validation |

**Total: ~6 hours**

---

## Glossary

| Term | Definition |
|------|------------|
| Debounce | Delay action until input stops for 300ms |
| Snippet | ~60 char text excerpt around search match |
| AND Logic | All search terms must be present |
| Client-side Filter | Filtering in browser without API call |
| Sidecar File | JSON metadata file alongside image |
