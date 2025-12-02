# Z-Explorer Specifications

This directory contains formal specifications for Z-Explorer features and enhancements.

## Specification Index

| ID | Name | Status | Effort | Dependencies |
|----|------|--------|--------|--------------|
| [001](./001-ui-settings-improvements/) | UI Settings & Improvements | ✅ Ready | ~10-12h | None |
| [002](./002-info-flyout-metadata/) | Info Flyout & Metadata | ✅ Ready | ~8-9h | None |
| [003](./003-gallery-search/) | Gallery Search | ✅ Ready | ~6h | 002 |
| [004](./004-litellm-integration/) | LiteLLM Integration | ✅ Ready | ~5.5h | None |
| [005](./005-variable-editor/) | Variable Editor | ✅ Ready | ~7-8h | 004 (AI features) |

**Total Estimated Effort**: ~37-41 hours

---

## Spec Summaries

### 001: UI Settings & Improvements ⚠️

**What**: Centralized settings dialog with gallery layouts, thumbnail sizes, collapsible tips, and runtime model override.

**Why**: Users can't customize the UI without editing files. Gallery layout is fixed, wasting screen space for different content types.

**Key Deliverables**:
- Settings dialog (gear icon + `/settings` command)
- Gallery layouts: Flex Row, Masonry, Grid Square, Grid Auto
- Thumbnail size presets (120px - 350px) + custom
- Runtime model override (without editing .env)
- Collapsible tips section
- Persistent preferences via localStorage

**Confidence**: 🟢 High — Ready to ship (largest scope)

---

### 002: Info Flyout & Metadata ✅

**What**: Slide-in info panel in lightbox showing image metadata, with JSON sidecar files for persistence.

**Why**: Current prompt display steals vertical space from images. Original prompts (with variables) are lost after substitution.

**Key Deliverables**:
- JSON sidecar files alongside images
- Info button (ⓘ) in lightbox corner
- Slide-in panel (320px) with all metadata
- Copy actions for original and final prompts

**Confidence**: 🟢 High — Ready to ship

---

### 003: Gallery Search ✅

**What**: Full-text search over prompts in gallery UI and via CLI `/search` command.

**Why**: Finding specific images among hundreds requires endless scrolling.

**Key Deliverables**:
- Search box in gallery header (real-time filtering)
- CLI `/search` command with snippets
- Full-text search over original AND final prompts
- Case-insensitive, multi-word AND logic

**Confidence**: 🟢 High — Ready to ship

**Requires**: Spec 002 (metadata sidecars provide searchable text)

---

### 004: LiteLLM Integration ✅

**What**: New `LLM_MODE=litellm` for cloud LLM providers (OpenAI, Anthropic, Ollama, etc.)

**Why**: Local LLMs need ~8GB VRAM. Cloud APIs offer better quality with zero VRAM.

**Key Deliverables**:
- `LLM_MODE=litellm` option
- `LLM_MODEL` variable (replaces `LLM_REPO`)
- Standard provider env vars (OPENAI_API_KEY, etc.)
- Setup wizard cloud option
- Full backward compatibility

**Confidence**: 🟢 High — Ready to ship

---

### 005: Variable Editor ✅

**What**: Standalone sub-app at `/var-editor` for managing prompt variables with AI expansion.

**Why**: Variable files must be edited manually. No way to AI-generate new values.

**Key Deliverables**:
- Three-panel layout (sidebar, editor, AI panel)
- CRUD API for variable files
- AI-powered item generation with guidance
- Route-based navigation (`/var-editor`)

**Confidence**: 🟢 High — Ready to ship

**Requires**: Spec 004 for AI features (uses same LLM config)

---

## Other Folders

### [concepts/](./concepts/)

Design explorations and mockups that inform specifications:
- `info-flyout/DESIGN.md` — Master design document covering all four UX improvements
- `info-flyout/mockup-*.html` — Interactive HTML mockups

---

## Dependency Graph

```
001 UI Settings ─────────────────────────────────────┐
                                                     │
002 Info Flyout & Metadata ──────────────────────────┼──→ All features
     │                                               │
     └──→ 003 Gallery Search ────────────────────────┤
                                                     │
004 LiteLLM Integration ──────────────────────────────┤
     │                                               │
     └──→ 005 Variable Editor (AI features) ─────────┘
```

---

## Recommended Implementation Order

Based on dependencies and value delivery:

1. **004 LiteLLM** (~5.5h) — Foundation for AI features, no dependencies
2. **002 Info Flyout** (~8-9h) — Metadata foundation for search, no dependencies
3. **003 Gallery Search** (~6h) — Quick win, requires 002
4. **005 Variable Editor** (~7-8h) — Uses 004's LLM config
5. **001 UI Settings** (~10-12h) — Largest scope, can be done anytime

**Parallel opportunities**:
- 004 and 002 can be developed simultaneously
- 001 can be developed in parallel with anything

---

## Dev-Readiness Assessment

### ✅ All Specs Ready for Implementation

| Spec | PRD | SDD | PLAN | README | Verdict |
|------|-----|-----|------|--------|---------|
| 001 | ✅ | ✅ | ✅ | ✅ | **Go** |
| 002 | ✅ | ✅ | ✅ | ✅ | **Go** |
| 003 | ✅ | ✅ | ✅ | ✅ | **Go** |
| 004 | ✅ | ✅ | ✅ | ✅ | **Go** |
| 005 | ✅ | ✅ | ✅ | ✅ | **Go** |

**Verdict: 🟢 DEV-READY** — All specifications complete with full documentation.

---

## How to Implement

```bash
# Start implementation of a specific spec
/start:implement <spec-id>

# Examples
/start:implement 004    # Start LiteLLM integration
/start:implement 002    # Start Info Flyout
```

---

## Specification Structure

Each spec folder follows this structure:

```
XXX-feature-name/
├── README.md              # Overview, confidence, quick reference
├── product-requirements.md # What & Why (PRD)
├── solution-design.md     # How (SDD)
└── implementation-plan.md # Step-by-step tasks (PLAN)
```

### Document Purposes

| Document | Audience | Contains |
|----------|----------|----------|
| **README** | Everyone | Quick summary, status, confidence |
| **PRD** | Product/Design | Problem, personas, features, acceptance criteria |
| **SDD** | Developers | Architecture, interfaces, patterns, decisions |
| **PLAN** | Implementers | Phased tasks with tests and validation |
