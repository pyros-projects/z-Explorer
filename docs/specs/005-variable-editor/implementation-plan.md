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

- `docs/specs/005-variable-editor/product-requirements.md` - Product Requirements
- `docs/specs/005-variable-editor/solution-design.md` - Solution Design

**Key Design Decisions**:

- **ADR-1**: Three-panel layout (sidebar, editor, AI panel)
- **ADR-2**: Route-based navigation at `/var-editor`
- **ADR-3**: Reuse `generate_prompt_variable_values()` for AI
- **ADR-4**: File-based storage (no database) - continue using `library/`

**Implementation Context**:

- Backend commands: `uv run pytest`, `uv run ruff check .`, `uv run ruff format .`
- Frontend commands: `npm run dev`, `npm run build`, `npm run check`, `npm run test` (from `src/z_explorer/gui/`)
- Patterns: Three-panel layout, optimistic UI, hash-based SPA routing
- Key interfaces: `VariableContent`, `VariableGenerateRequest`, SDD Interface Specifications

**Effort Estimate**: ~7-8 hours

---

## Implementation Phases

- [ ] T1 Phase 1: Backend CRUD API `[activity: backend-development]`

    - [ ] T1.1 Prime Context
        - [ ] T1.1.1 Read existing prompt_vars.py `[ref: src/z_explorer/models/prompt_vars.py]`
        - [ ] T1.1.2 Read existing /api/variables endpoint `[ref: src/z_explorer/server.py; lines: 200-250]`
        - [ ] T1.1.3 Review SDD interface specifications `[ref: SDD/Interface Specifications]`
    
    - [ ] T1.2 Write Tests `[activity: test-implementation]`
        - [ ] T1.2.1 Test GET /api/variables/{name} returns content for existing variable
        - [ ] T1.2.2 Test GET /api/variables/{name} returns 404 for non-existent
        - [ ] T1.2.3 Test PUT /api/variables/{name} saves content
        - [ ] T1.2.4 Test POST /api/variables creates new file
        - [ ] T1.2.5 Test DELETE /api/variables/{name} removes file
        - [ ] T1.2.6 Test validation rejects dangerous names (../evil, /etc/passwd)
    
    - [ ] T1.3 Implement `[activity: backend-development]`
        - [ ] T1.3.1 Add Pydantic models: VariableContent, VariableUpdateRequest, VariableCreateRequest
        - [ ] T1.3.2 Implement GET /api/variables/{name} endpoint
        - [ ] T1.3.3 Implement PUT /api/variables/{name} endpoint
        - [ ] T1.3.4 Implement POST /api/variables endpoint
        - [ ] T1.3.5 Implement DELETE /api/variables/{name} endpoint
        - [ ] T1.3.6 Add name validation function (reject special characters)
    
    - [ ] T1.4 Validate
        - [ ] T1.4.1 Run `uv run ruff check . && uv run ruff format .`
        - [ ] T1.4.2 Run `uv run pytest tests/test_server/` 
        - [ ] T1.4.3 Manual test with curl/httpie

- [ ] T2 Phase 2: AI Generation Endpoint `[activity: backend-development]`

    - [ ] T2.1 Prime Context
        - [ ] T2.1.1 Read generate_prompt_variable_values `[ref: src/z_explorer/llm_provider.py]`
        - [ ] T2.1.2 Review SDD AI generation interface `[ref: SDD/Interface Specifications; POST /api/variables/generate]`
    
    - [ ] T2.2 Write Tests `[activity: test-implementation]`
        - [ ] T2.2.1 Test POST /api/variables/generate returns items (mock LLM)
        - [ ] T2.2.2 Test duplicate filtering works
        - [ ] T2.2.3 Test error handling when LLM not configured
        - [ ] T2.2.4 Test guidance parameter is passed through
    
    - [ ] T2.3 Implement `[activity: backend-development]`
        - [ ] T2.3.1 Add VariableGenerateRequest, VariableGenerateResponse models
        - [ ] T2.3.2 Implement POST /api/variables/generate endpoint
        - [ ] T2.3.3 Integrate with generate_prompt_variable_values()
        - [ ] T2.3.4 Add duplicate filtering logic
        - [ ] T2.3.5 Handle LLM errors gracefully
    
    - [ ] T2.4 Validate
        - [ ] T2.4.1 Run `uv run pytest` for all tests
        - [ ] T2.4.2 Manual test with actual LLM if configured

- [ ] T3 Phase 3: Frontend Routing & Shell `[activity: frontend-development]`

    - [ ] T3.1 Prime Context
        - [ ] T3.1.1 Read App.svelte for current routing `[ref: src/z_explorer/gui/src/App.svelte]`
        - [ ] T3.1.2 Review SDD component structure `[ref: SDD/Directory Map]`
    
    - [ ] T3.2 Write Tests `[activity: test-implementation]`
        - [ ] T3.2.1 Test route navigation to /var-editor
        - [ ] T3.2.2 Test back navigation to main app
        - [ ] T3.2.3 Test VarEditor component mounts
    
    - [ ] T3.3 Implement `[activity: frontend-development]`
        - [ ] T3.3.1 Create var-editor/ directory in lib/
        - [ ] T3.3.2 Create VarEditor.svelte shell with three-panel layout
        - [ ] T3.3.3 Add route handling in App.svelte
        - [ ] T3.3.4 Add "Variables" link in navigation
        - [ ] T3.3.5 Style three-panel layout (grid/flexbox)
    
    - [ ] T3.4 Validate
        - [ ] T3.4.1 Run `npm run check` for TypeScript
        - [ ] T3.4.2 Run `npm run test`
        - [ ] T3.4.3 Visual verification of layout

- [ ] T4 Phase 4: VarSidebar Component `[activity: frontend-development]`

    - [ ] T4.1 Prime Context
        - [ ] T4.1.1 Review SDD VarSidebar interface `[ref: SDD/Building Block View]`
        - [ ] T4.1.2 Review existing /api/variables endpoint response format
    
    - [ ] T4.2 Write Tests `[activity: test-implementation]`
        - [ ] T4.2.1 Test sidebar fetches and displays variable list
        - [ ] T4.2.2 Test click dispatches select event
        - [ ] T4.2.3 Test "New Variable" button shows input
        - [ ] T4.2.4 Test search/filter functionality
    
    - [ ] T4.3 Implement `[activity: frontend-development]`
        - [ ] T4.3.1 Create VarSidebar.svelte
        - [ ] T4.3.2 Fetch variables from /api/variables
        - [ ] T4.3.3 Display list with item counts
        - [ ] T4.3.4 Handle selection with event dispatch
        - [ ] T4.3.5 Add "New Variable" button with name input
        - [ ] T4.3.6 Add search filter input
        - [ ] T4.3.7 Style sidebar (scrollable list, hover states)
    
    - [ ] T4.4 Validate
        - [ ] T4.4.1 Run `npm run check && npm run test`
        - [ ] T4.4.2 Visual verification with real data

- [ ] T5 Phase 5: VarTextEditor Component `[activity: frontend-development]`

    - [ ] T5.1 Prime Context
        - [ ] T5.1.1 Review SDD editor interface `[ref: SDD/Cross-Cutting Concepts; VarEditor Component Pattern]`
        - [ ] T5.1.2 Review keyboard shortcuts from PRD
    
    - [ ] T5.2 Write Tests `[activity: test-implementation]`
        - [ ] T5.2.1 Test content loads when variable selected
        - [ ] T5.2.2 Test dirty state on edit
        - [ ] T5.2.3 Test Ctrl+S triggers save
        - [ ] T5.2.4 Test save calls PUT endpoint
    
    - [ ] T5.3 Implement `[activity: frontend-development]`
        - [ ] T5.3.1 Create VarTextEditor.svelte
        - [ ] T5.3.2 Large textarea with monospace font
        - [ ] T5.3.3 Track dirty state (changes indicator)
        - [ ] T5.3.4 Implement Ctrl+S save shortcut
        - [ ] T5.3.5 Add Save button with loading state
        - [ ] T5.3.6 Show line count / item count
        - [ ] T5.3.7 Connect to PUT /api/variables/{name}
    
    - [ ] T5.4 Validate
        - [ ] T5.4.1 Run `npm run check && npm run test`
        - [ ] T5.4.2 Manual test with real file save

- [ ] T6 Phase 6: VarAIPanel Component `[activity: frontend-development]`

    - [ ] T6.1 Prime Context
        - [ ] T6.1.1 Review SDD AI panel interface `[ref: SDD/Runtime View; Secondary Flow: AI Generation]`
        - [ ] T6.1.2 Review PRD AI generation requirements
    
    - [ ] T6.2 Write Tests `[activity: test-implementation]`
        - [ ] T6.2.1 Test Generate button calls API
        - [ ] T6.2.2 Test preview displays generated items
        - [ ] T6.2.3 Test "Add All" dispatches event
        - [ ] T6.2.4 Test count slider works
    
    - [ ] T6.3 Implement `[activity: frontend-development]`
        - [ ] T6.3.1 Create VarAIPanel.svelte
        - [ ] T6.3.2 Count input/slider (5-100 range)
        - [ ] T6.3.3 Optional guidance textarea
        - [ ] T6.3.4 Generate button with loading state
        - [ ] T6.3.5 Preview list of generated items
        - [ ] T6.3.6 "Add All" button to dispatch items
        - [ ] T6.3.7 Error display for LLM issues
        - [ ] T6.3.8 Connect to POST /api/variables/generate
    
    - [ ] T6.4 Validate
        - [ ] T6.4.1 Run `npm run check && npm run test`
        - [ ] T6.4.2 Manual test with real LLM

- [ ] T7 Phase 7: Integration & Full Flow `[activity: integration-testing]`

    - [ ] T7.1 Wire Components Together
        - [ ] T7.1.1 Connect VarSidebar select to load content in VarTextEditor
        - [ ] T7.1.2 Connect VarAIPanel generated event to append in VarTextEditor
        - [ ] T7.1.3 Handle unsaved changes warning on variable switch
        - [ ] T7.1.4 Refresh sidebar after create/delete
    
    - [ ] T7.2 End-to-End Tests
        - [ ] T7.2.1 Full flow: select variable → edit → save → verify file
        - [ ] T7.2.2 Full flow: generate AI → preview → add → save
        - [ ] T7.2.3 Full flow: create new variable → edit → save
        - [ ] T7.2.4 Error case: LLM not configured
    
    - [ ] T7.3 Performance Validation `[ref: SDD/Quality Requirements]`
        - [ ] T7.3.1 Editor response <100ms for typing
        - [ ] T7.3.2 File load <500ms for files <1000 lines
        - [ ] T7.3.3 Route navigation <300ms
    
    - [ ] T7.4 Final Validation
        - [ ] T7.4.1 All unit tests pass: `uv run pytest && cd src/z_explorer/gui && npm run test`
        - [ ] T7.4.2 TypeScript clean: `npm run check`
        - [ ] T7.4.3 Linting clean: `uv run ruff check .`
        - [ ] T7.4.4 Production build works: `npm run build`
        - [ ] T7.4.5 PRD acceptance criteria verified
        - [ ] T7.4.6 Documentation updated if needed
