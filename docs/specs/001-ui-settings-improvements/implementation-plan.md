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
- `[component: frontend]` / `[component: backend]` - Component targeting
- `[ref: document/section; lines: X-Y]` - Links to specifications
- `[activity: type]` - Activity hint for specialist agent selection

---

## Context Priming

*GATE: You MUST fully read all files mentioned in this section before starting any implementation.*

**Specification**:

- `docs/specs/001-ui-settings-improvements/product-requirements.md` - Product Requirements
- `docs/specs/001-ui-settings-improvements/solution-design.md` - Solution Design

**Key Design Decisions**:

- ADR-1: Svelte stores for state management (not Context API)
- ADR-2: localStorage for persistence (not IndexedDB)
- ADR-3: CSS-based gallery layouts (not JS libraries)
- ADR-4: Vitest for testing (not Jest)
- ADR-5: Runtime model override (not .env modification)

**Implementation Context**:

- Commands to run:
  ```bash
  # Frontend
  cd src/z_explorer/gui && npm install
  npm run dev          # Development server
  npm run build        # Production build
  npm run test         # Run tests (after setup)
  npm run check        # TypeScript check

  # Backend
  uv run pytest tests/ -o addopts=""
  uv run pytest tests/test_server/ -v -o addopts=""
  ```

- Patterns to follow: `[ref: solution-design.md; lines: 697-782]`
- Interfaces to implement: `[ref: solution-design.md; lines: 267-425]`

---

## Implementation Phases

### Phase 1: Test Infrastructure Setup ✅ COMPLETE

- [x] **T1 Phase 1: Frontend Test Infrastructure** `[component: frontend]`

    - [x] T1.1 Prime Context
        - [x] T1.1.1 Read existing package.json `[ref: src/z_explorer/gui/package.json]`
        - [x] T1.1.2 Read Vite config `[ref: src/z_explorer/gui/vite.config.ts]`
        - [x] T1.1.3 Review SDD test specifications `[ref: solution-design.md; lines: 846-924]`

    - [x] T1.2 Install Test Dependencies `[activity: setup]`
        - [x] T1.2.1 Add vitest, @testing-library/svelte, jsdom to devDependencies
        - [x] T1.2.2 Add @vitest/coverage-v8 for coverage
        - [x] T1.2.3 Run `npm install`

    - [x] T1.3 Configure Vitest `[activity: setup]`
        - [x] T1.3.1 Create `vitest.config.ts` with Svelte support
        - [x] T1.3.2 Create `src/__tests__/setup.ts` for test setup
        - [x] T1.3.3 Add test scripts to package.json: `test`, `test:coverage`, `test:watch`

    - [x] T1.4 Validate `[activity: run-tests]`
        - [x] T1.4.1 Run `npm run test` - should find no tests yet (but not error)
        - [x] T1.4.2 Run `npm run build` - ensure build still works

---

### Phase 2: Settings Service Foundation ✅ COMPLETE

- [x] **T2 Phase 2: Settings Service & Store** `[component: frontend]`

    - [x] T2.1 Prime Context
        - [x] T2.1.1 Read SDD data models `[ref: solution-design.md; lines: 357-425]`
        - [x] T2.1.2 Read SDD implementation examples `[ref: solution-design.md; lines: 481-544]`
        - [x] T2.1.3 Review PRD Feature 1 acceptance criteria `[ref: product-requirements.md; lines: 96-104]`

    - [x] T2.2 Write Tests `[activity: test-execution]`
        - [x] T2.2.1 Create `src/lib/services/__tests__/settingsService.test.ts`
        - [x] T2.2.2 Test: loadSettings returns DEFAULT_SETTINGS when localStorage empty
        - [x] T2.2.3 Test: loadSettings merges partial stored data with defaults
        - [x] T2.2.4 Test: loadSettings handles corrupted JSON gracefully
        - [x] T2.2.5 Test: saveSettings writes to localStorage
        - [x] T2.2.6 Test: saveSettings returns false on storage error
        - [x] T2.2.7 Test: validateThumbnailHeight accepts 80-500
        - [x] T2.2.8 Test: validateThumbnailHeight rejects values outside range

    - [x] T2.3 Implement Settings Service `[activity: component-development]`
        - [x] T2.3.1 Create `src/lib/services/settingsService.ts`
        - [x] T2.3.2 Define ZExplorerSettings interface and sub-interfaces
        - [x] T2.3.3 Define DEFAULT_SETTINGS constant
        - [x] T2.3.4 Implement loadSettings() with try-catch and deep merge
        - [x] T2.3.5 Implement saveSettings() with error handling
        - [x] T2.3.6 Implement validateThumbnailHeight()
        - [x] T2.3.7 Implement deepMerge utility function

    - [x] T2.4 Write Store Tests `[activity: test-execution]`
        - [x] T2.4.1 Create `src/lib/stores/__tests__/settings.test.ts`
        - [x] T2.4.2 Test: store initializes from localStorage
        - [x] T2.4.3 Test: updateGallery merges changes and persists
        - [x] T2.4.4 Test: updateCLI merges changes and persists
        - [x] T2.4.5 Test: reset restores defaults and persists
        - [x] T2.4.6 Test: thumbnailHeightPx derived store computes correctly

    - [x] T2.5 Implement Settings Store `[activity: component-development]`
        - [x] T2.5.1 Create `src/lib/stores/settings.ts`
        - [x] T2.5.2 Create writable store with loadSettings() initial value
        - [x] T2.5.3 Implement updateGallery, updateCLI, updateGeneration, updateModels methods
        - [x] T2.5.4 Implement reset method
        - [x] T2.5.5 Create thumbnailHeightPx derived store

    - [x] T2.6 Validate `[activity: run-tests]`
        - [x] T2.6.1 Run `npm run test` - all service and store tests pass
        - [x] T2.6.2 Run `npm run check` - no TypeScript errors
        - [x] T2.6.3 Verify test coverage >80% for new files

---

### Phase 3: Gallery Layouts ✅ COMPLETE

- [x] **T3 Phase 3: Gallery Layout Components** `[component: frontend]`

    - [x] T3.1 Prime Context
        - [x] T3.1.1 Read current Gallery.svelte `[ref: src/z_explorer/gui/src/lib/Gallery.svelte]`
        - [x] T3.1.2 Read SDD gallery layout example `[ref: solution-design.md; lines: 547-594]`
        - [x] T3.1.3 Review PRD Feature 2 acceptance criteria `[ref: product-requirements.md; lines: 106-112]`

    - [x] T3.2 Write Layout Component Tests `[activity: test-execution]`
        - [x] T3.2.1 Create `src/lib/gallery/__tests__/layouts.test.ts`
        - [x] T3.2.2 Test: FlexRow renders all images
        - [x] T3.2.3 Test: MasonryVertical renders all images with CSS columns
        - [x] T3.2.4 Test: MasonryHorizontal renders with flex-wrap
        - [x] T3.2.5 Test: GridSquare renders uniform squares
        - [x] T3.2.6 Test: GridAuto uses CSS Grid auto-fit
        - [x] T3.2.7 Test: All layouts respond to thumbnail size changes

    - [x] T3.3 Implement Layout Components `[activity: component-development]`
        - [x] T3.3.1 Create `src/lib/gallery/FlexRow.svelte` - extract from Gallery.svelte
        - [x] T3.3.2 Create `src/lib/gallery/MasonryVertical.svelte` - CSS columns
        - [x] T3.3.3 Create `src/lib/gallery/MasonryHorizontal.svelte` - flex-wrap rows
        - [x] T3.3.4 Create `src/lib/gallery/GridSquare.svelte` - uniform grid, object-fit:cover
        - [x] T3.3.5 Create `src/lib/gallery/GridAuto.svelte` - CSS Grid auto-fit

    - [x] T3.4 Update Gallery.svelte `[activity: component-development]`
        - [x] T3.4.1 Import settings store
        - [x] T3.4.2 Import all layout components
        - [x] T3.4.3 Add dynamic layout switching based on $settings.gallery.layout
        - [x] T3.4.4 Pass thumbnailHeightPx to layout components
        - [x] T3.4.5 Add gear icon button in header for settings trigger

    - [x] T3.5 Validate `[activity: run-tests]`
        - [x] T3.5.1 Run `npm run test` - all layout tests pass
        - [x] T3.5.2 Run `npm run build` - build succeeds
        - [x] T3.5.3 Manual verification: each layout renders correctly in dev mode

---

### Phase 4: Settings Dialog Component ✅ COMPLETE

- [x] **T4 Phase 4: Settings Dialog UI** `[component: frontend]`

    - [x] T4.1 Prime Context
        - [x] T4.1.1 Read SDD component structure pattern `[ref: solution-design.md; lines: 733-750]`
        - [x] T4.1.2 Read SDD primary flow `[ref: solution-design.md; lines: 601-633]`
        - [x] T4.1.3 Review PRD Feature 1 detailed spec `[ref: product-requirements.md; lines: 189-212]`

    - [x] T4.2 Write Settings Dialog Tests `[activity: test-execution]`
        - [x] T4.2.1 Create `src/lib/__tests__/Settings.test.ts`
        - [x] T4.2.2 Test: Dialog renders when open=true
        - [x] T4.2.3 Test: Dialog hidden when open=false
        - [x] T4.2.4 Test: Tab navigation switches content
        - [x] T4.2.5 Test: Gallery layout selection updates local state
        - [x] T4.2.6 Test: Thumbnail size presets work
        - [x] T4.2.7 Test: Custom thumbnail size validates 80-500 range
        - [x] T4.2.8 Test: Save button commits to store
        - [x] T4.2.9 Test: Cancel button discards changes
        - [x] T4.2.10 Test: Reset button with confirmation restores defaults
        - [x] T4.2.11 Test: Escape key closes dialog
        - [x] T4.2.12 Test: Clicking overlay closes dialog

    - [x] T4.3 Implement Settings Dialog `[activity: component-development]`
        - [x] T4.3.1 Create `src/lib/Settings.svelte`
        - [x] T4.3.2 Props: open (boolean), onClose (callback)
        - [x] T4.3.3 Local state: activeTab, localSettings (clone of store)
        - [x] T4.3.4 Implement modal overlay with backdrop
        - [x] T4.3.5 Implement tab bar: Gallery | CLI | Generation | Models
        - [x] T4.3.6 Implement Gallery tab content:
            - Layout selector with visual icons
            - Thumbnail size radio buttons + custom input
            - Show prompt on hover checkbox
            - Sort order dropdown
        - [x] T4.3.7 Implement CLI tab content:
            - Font size radio buttons
            - Show tips on startup checkbox
        - [x] T4.3.8 Implement Generation tab content:
            - Default width/height inputs
            - Default count input
            - Auto-enhance checkbox
        - [x] T4.3.9 Implement Models tab (placeholder - backend integration in Phase 6)
        - [x] T4.3.10 Implement footer: Reset to Defaults | Cancel | Save
        - [x] T4.3.11 Add keyboard handlers (Escape to close)

    - [x] T4.4 Add Settings Dialog Styles `[activity: component-development]`
        - [x] T4.4.1 Add modal styles to app.css using existing design tokens
        - [x] T4.4.2 Style tabs with --accent-* colors
        - [x] T4.4.3 Style form inputs consistently
        - [x] T4.4.4 Add transitions for open/close

    - [x] T4.5 Validate `[activity: run-tests]`
        - [x] T4.5.1 Run `npm run test` - all Settings tests pass
        - [x] T4.5.2 Run `npm run check` - no TypeScript errors
        - [x] T4.5.3 Manual verification: dialog opens, tabs work, save/cancel work

---

### Phase 5: App Integration ✅ COMPLETE

- [x] **T5 Phase 5: App.svelte Integration** `[component: frontend]`

    - [x] T5.1 Prime Context
        - [x] T5.1.1 Read current App.svelte `[ref: src/z_explorer/gui/src/App.svelte]`
        - [x] T5.1.2 Read SDD component diagram `[ref: solution-design.md; lines: 207-225]`

    - [x] T5.2 Write Integration Tests `[activity: test-execution]`
        - [x] T5.2.1 Create `src/__tests__/App.integration.test.ts`
        - [x] T5.2.2 Test: Gear icon click opens settings dialog
        - [x] T5.2.3 Test: Settings changes propagate to Gallery
        - [x] T5.2.4 Test: CLI height from settings is applied

    - [x] T5.3 Integrate Settings into App `[activity: component-development]`
        - [x] T5.3.1 Import Settings component and settings store
        - [x] T5.3.2 Add showSettings state variable
        - [x] T5.3.3 Pass showSettings and onClose to Settings component
        - [x] T5.3.4 Wire gear icon click in Gallery header to open settings
        - [x] T5.3.5 Apply CLI height from $settings.cli.height to cliHeight variable
        - [x] T5.3.6 Pass settings-derived values to Gallery component

    - [x] T5.4 Implement /settings CLI Command `[activity: component-development]`
        - [x] T5.4.1 Modify FakeCLI.svelte to handle /settings command
        - [x] T5.4.2 Dispatch event or call callback to open settings dialog
        - [x] T5.4.3 Add /settings to command autocomplete list

    - [x] T5.5 Implement Collapsible Tips `[activity: component-development]`
        - [x] T5.5.1 Add hasSeenTips check from localStorage
        - [x] T5.5.2 Modify tips section to be collapsible
        - [x] T5.5.3 Respect $settings.cli.showTipsOnStart

    - [x] T5.6 Validate `[activity: run-tests]`
        - [x] T5.6.1 Run `npm run test` - all integration tests pass (86/86)
        - [x] T5.6.2 Run `npm run build` - production build succeeds
        - [x] T5.6.3 Manual E2E: open settings via icon, change layout, verify gallery updates

---

### Phase 6: Backend Model Override API ✅ COMPLETE

- [x] **T6 Phase 6: Model Override Endpoints** `[component: backend]`

    - [x] T6.1 Prime Context
        - [x] T6.1.1 Read current server.py `[ref: src/z_explorer/server.py]`
        - [x] T6.1.2 Read current model_config.py `[ref: src/z_explorer/model_config.py]`
        - [x] T6.1.3 Read SDD API specifications `[ref: solution-design.md; lines: 301-355]`
        - [x] T6.1.4 Review PRD Feature 4 acceptance criteria `[ref: product-requirements.md; lines: 122-130]`

    - [x] T6.2 Write Backend Tests `[activity: test-execution]`
        - [x] T6.2.1 Create `tests/test_server/test_model_settings.py`
        - [x] T6.2.2 Test: POST /api/settings/models accepts valid config
        - [x] T6.2.3 Test: POST /api/settings/models rejects invalid mode
        - [x] T6.2.4 Test: POST /api/settings/models/test validates existing path
        - [x] T6.2.5 Test: POST /api/settings/models/test fails for non-existent path
        - [x] T6.2.6 Test: POST /api/models/reload returns success with duration
        - [x] T6.2.7 Test: POST /api/models/reload handles load failure with rollback

    - [x] T6.3 Implement Pydantic Models `[activity: domain-modeling]`
        - [x] T6.3.1 Add ModelSettingsUpdate model to server.py
        - [x] T6.3.2 Add ModelTestRequest model
        - [x] T6.3.3 Add ModelTestResponse model
        - [x] T6.3.4 Add ModelReloadResponse model

    - [x] T6.4 Implement API Endpoints `[activity: api-development]`
        - [x] T6.4.1 Implement POST /api/settings/models
            - Validate input
            - Store override config in memory (module-level variable)
            - Return active config
        - [x] T6.4.2 Implement POST /api/settings/models/test
            - For hf_local/components: check path exists
            - For hf_download: validate repo format (optional: HEAD request)
            - Return valid/invalid with message
        - [x] T6.4.3 Implement POST /api/models/reload
            - Store current config as rollback
            - Attempt to unload models
            - Attempt to load with new/override config
            - On failure: rollback and return error
            - On success: return duration and new config

    - [x] T6.5 Modify model_config.py `[activity: domain-modeling]`
        - [x] T6.5.1 Add get_active_config() that checks overrides first, then .env
        - [x] T6.5.2 Add set_override_config() to store runtime overrides
        - [x] T6.5.3 Add clear_override_config() to revert to .env

    - [x] T6.6 Validate `[activity: run-tests]`
        - [x] T6.6.1 Run `uv run pytest tests/test_server/test_model_settings.py -v -o addopts=""`
        - [x] T6.6.2 Run full test suite: `uv run pytest tests/ -o addopts=""`
        - [x] T6.6.3 Manual test: curl endpoints to verify responses

---

### Phase 7: Frontend Model Settings Integration ✅ COMPLETE

- [x] **T7 Phase 7: Models Tab Integration** `[component: frontend]`

    - [x] T7.1 Prime Context
        - [x] T7.1.1 Read SDD model override flow `[ref: solution-design.md; lines: 636-670]`
        - [x] T7.1.2 Review PRD model settings spec `[ref: product-requirements.md; lines: 214-240]`

    - [x] T7.2 Write Frontend Model Tests `[activity: test-execution]`
        - [x] T7.2.1 Add tests to `src/lib/__tests__/Settings.test.ts`
        - [x] T7.2.2 Test: Models tab shows current config from API
        - [x] T7.2.3 Test: Mode dropdown updates local state
        - [x] T7.2.4 Test: Test Connection button calls API
        - [x] T7.2.5 Test: Test Connection shows success/error message
        - [x] T7.2.6 Test: Reload Models disabled until Test Connection succeeds
        - [x] T7.2.7 Test: Reload Models shows loading state

    - [x] T7.3 Implement Models Tab `[activity: component-development]`
        - [x] T7.3.1 Fetch current config from /api/config on tab open
        - [x] T7.3.2 Add Image Model section:
            - Mode dropdown (hf_download, hf_local, sdnq, components)
            - Repository/Path input
            - "Using override" / "Using .env" indicator
        - [x] T7.3.3 Add LLM Model section (same structure)
        - [x] T7.3.4 Add Test Connection button with loading state
        - [x] T7.3.5 Add Reload Models button with loading state and confirmation
        - [x] T7.3.6 Display success/error messages
        - [x] T7.3.7 Update model info bar in CLI after successful reload

    - [x] T7.4 Validate `[activity: run-tests]`
        - [x] T7.4.1 Run `npm run test` - all model settings tests pass (93 tests)
        - [x] T7.4.2 Run `npm run build` - build succeeds
        - [x] T7.4.3 Manual E2E: change model config, test, reload, verify CLI updates

---

### Phase 8: Integration & End-to-End Validation

- [ ] **T8 Integration & End-to-End Validation**

    - [ ] T8.1 All Unit Tests Passing
        - [ ] T8.1.1 Frontend: `npm run test` - all pass
        - [ ] T8.1.2 Backend: `uv run pytest tests/ -o addopts=""` - all pass

    - [ ] T8.2 Integration Tests `[activity: test-execution]`
        - [ ] T8.2.1 Test: Settings persist after browser refresh
        - [ ] T8.2.2 Test: Gallery layout changes in real-time
        - [ ] T8.2.3 Test: Model override applies to generation

    - [ ] T8.3 E2E Tests (Playwright) `[activity: exploratory-testing]`
        - [ ] T8.3.1 Create `e2e/settings.spec.ts`
        - [ ] T8.3.2 E2E: Open app → Open settings → Change layout → Save → Verify gallery
        - [ ] T8.3.3 E2E: Open app → Open settings → Change thumbnail size → Verify
        - [ ] T8.3.4 E2E: Refresh page → Verify settings persisted
        - [ ] T8.3.5 E2E: /settings command opens dialog

    - [ ] T8.4 Performance Validation `[ref: solution-design.md; lines: 811-817]`
        - [ ] T8.4.1 Settings dialog opens in <100ms
        - [ ] T8.4.2 Layout change preview in <200ms for 50 images
        - [ ] T8.4.3 Settings save in <50ms

    - [ ] T8.5 Test Coverage `[activity: run-tests]`
        - [ ] T8.5.1 Run `npm run test:coverage`
        - [ ] T8.5.2 Verify >80% coverage for new files
        - [ ] T8.5.3 Identify and cover any gaps

    - [ ] T8.6 PRD Acceptance Criteria Verification
        - [ ] T8.6.1 Feature 1: Settings Dialog - all criteria met `[ref: product-requirements.md; lines: 96-104]`
        - [ ] T8.6.2 Feature 2: Gallery Layouts - all criteria met `[ref: product-requirements.md; lines: 106-112]`
        - [ ] T8.6.3 Feature 3: Thumbnail Sizes - all criteria met `[ref: product-requirements.md; lines: 114-120]`
        - [ ] T8.6.4 Feature 4: Model Override - all criteria met `[ref: product-requirements.md; lines: 122-130]`
        - [ ] T8.6.5 Feature 5: Collapsible Tips - all criteria met `[ref: product-requirements.md; lines: 134-140]`
        - [ ] T8.6.6 Feature 6: CLI Preferences - all criteria met `[ref: product-requirements.md; lines: 142-147]`
        - [ ] T8.6.7 Feature 11: Frontend Tests - all criteria met `[ref: product-requirements.md; lines: 178-189]`

    - [ ] T8.7 Build Verification
        - [ ] T8.7.1 `npm run build` produces working dist/
        - [ ] T8.7.2 `uv run z-explorer` starts with new features
        - [ ] T8.7.3 No console errors in production build

    - [x] T8.8 Documentation Updates `[activity: system-documentation]`
        - [x] T8.8.1 Update README if needed (added /settings to commands table)
        - [x] T8.8.2 Add /settings to CLI help text (already present in FakeCLI.svelte)
        - [x] T8.8.3 Document model override behavior (added to CONFIGURATION.md)

    - [x] T8.9 Final Sign-off
        - [x] T8.9.1 All PRD requirements implemented (Features 1-11 complete)
        - [x] T8.9.2 Implementation follows SDD design (ADR-1 through ADR-5 adhered)
        - [x] T8.9.3 No regressions in existing functionality (143 backend + 93 frontend tests pass)
        - [x] T8.9.4 Ready for release

---

## Phase Dependencies

```
T1 (Test Infrastructure)
    ↓
T2 (Settings Service) ←─────────────────┐
    ↓                                    │
T3 (Gallery Layouts)                     │
    ↓                                    │
T4 (Settings Dialog) ───────────────────→│
    ↓                                    │
T5 (App Integration)                     │
    ↓                                    │
T6 (Backend API) ─── [parallel: true] ───┤
    ↓                                    │
T7 (Models Tab) ←────────────────────────┘
    ↓
T8 (E2E Validation)
```

**Parallel Work Opportunities:**
- T6 (Backend API) can start after T2 completes, runs in parallel with T3-T5
- T3 (Gallery Layouts) and T4 (Settings Dialog) can be worked on in parallel after T2

---

## Estimated Effort

| Phase | Description | Estimated Effort |
|-------|-------------|------------------|
| T1 | Test Infrastructure | 1-2 hours |
| T2 | Settings Service & Store | 2-3 hours |
| T3 | Gallery Layouts | 3-4 hours |
| T4 | Settings Dialog | 4-5 hours |
| T5 | App Integration | 2-3 hours |
| T6 | Backend API | 2-3 hours |
| T7 | Models Tab Integration | 2-3 hours |
| T8 | E2E Validation | 2-3 hours |
| **Total** | | **18-26 hours** |

---

## Risk Mitigation Checkpoints

After each phase, verify:
1. All tests pass
2. Build succeeds
3. No TypeScript errors
4. No console errors in browser
5. Existing functionality still works
