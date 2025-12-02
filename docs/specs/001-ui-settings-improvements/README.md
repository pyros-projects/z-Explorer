# Spec 001: UI Settings & Improvements

## Quick Summary

**What**: Centralized settings dialog with gallery layout options, thumbnail sizes, runtime model override, and persistent preferences.

**Why**: Z-Explorer's fixed UI doesn't adapt to different content types or user preferences. Changing models requires editing files and restarting.

**Status**: ✅ Ready for Implementation

## Specification Documents

| Document | Purpose | Status |
|----------|---------|--------|
| [product-requirements.md](./product-requirements.md) | What to build and why | ✅ Complete |
| [solution-design.md](./solution-design.md) | How to build it | ✅ Complete |
| [implementation-plan.md](./implementation-plan.md) | Step-by-step tasks | ✅ Complete |

## Key Deliverables

1. **Settings Dialog** - Gear icon + `/settings` command, tabbed navigation
2. **Gallery Layouts** - Flex Row, Masonry Vertical/Horizontal, Grid Square, Grid Auto
3. **Thumbnail Sizes** - Presets (120-350px) + custom input
4. **Model Override** - Runtime model switching without .env edits
5. **Collapsible Tips** - Hidden by default for returning users
6. **Persistent Preferences** - localStorage for all settings

## Settings Tabs

| Tab | Features |
|-----|----------|
| **Gallery** | Layout style, thumbnail size, sort order |
| **CLI** | Font size, tips visibility, height persistence |
| **Generation** | Default dimensions, batch count, auto-enhance |
| **Models** | Image model override, LLM override, test connection |

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| State management | Svelte stores | Native, simple, reactive |
| Persistence | localStorage | Browser-based, no backend needed |
| Gallery layouts | CSS-based | No JS layout libraries, performant |
| Testing | Vitest | Svelte-native, fast |

## Implementation Phases

```
T1: Settings Infrastructure (stores, service, types)
     ↓
T2: Settings Dialog Shell (modal, tabs)
     ↓
T3: Gallery Tab ───────────────────┐
T4: CLI Tab (parallel) ────────────┼──→ T7: Integration
T5: Generation Tab (parallel) ─────┤
T6: Models Tab ────────────────────┘
     ↓
T8: E2E Validation
```

**Estimated Effort**: ~10-12 hours

## Confidence Assessment

| Dimension | Level | Notes |
|-----------|-------|-------|
| Requirements Clarity | 🟢 High | Detailed PRD with acceptance criteria |
| Technical Feasibility | 🟢 High | Standard Svelte patterns, localStorage |
| Scope Containment | 🟡 Medium | Large feature set, needs discipline |
| Risk Level | 🟡 Medium | Model override requires backend coordination |
| Estimation Accuracy | 🟡 Medium | Many UI components to build |

**Overall Confidence**: 🟢 **High** - Ready to ship (largest scope of all specs)

## Dependencies

- **None required** - This is a standalone enhancement

## Related Specs

- **002**: Info Flyout (no dependency, different UI area)
- **003**: Gallery Search (no dependency, can coexist)
- **004**: LiteLLM (model settings tab could reference, but independent)
- **005**: Variable Editor (no dependency)

## How to Implement

```bash
/start:implement 001
```

## Feature Previews

### Gallery Layouts

| Layout | Best For |
|--------|----------|
| Flex Row (default) | Mixed aspect ratios |
| Masonry Vertical | Portrait-heavy galleries |
| Masonry Horizontal | Landscape-heavy galleries |
| Grid Square | Uniform thumbnails |
| Grid Auto | Auto-fit to viewport |

### Model Override

```
Settings → Models Tab
┌─────────────────────────────────────┐
│ Image Model                         │
│ Mode: [SDNQ ▼]                      │
│ Path: [/models/sdnq_v1.safetensors] │
│ [Test Connection] [Reload Models]   │
│                                     │
│ ⚠️ Override active (not using .env) │
│ [Reset to .env defaults]            │
└─────────────────────────────────────┘
```

Changes apply at runtime without server restart.
