# Spec 002: Info Flyout & Metadata Foundation

## Quick Summary

**What**: Add an info flyout panel to the lightbox that displays image metadata, with JSON sidecar files for persistence.

**Why**: Currently the prompt steals vertical space from the image. Users want metadata on-demand, not always visible. Original prompts (with `__variables__`) are lost after substitution.

**Status**: ✅ Ready for Implementation

## Specification Documents

| Document | Purpose | Status |
|----------|---------|--------|
| [product-requirements.md](./product-requirements.md) | What to build and why | ✅ Complete |
| [solution-design.md](./solution-design.md) | How to build it | ✅ Complete |
| [implementation-plan.md](./implementation-plan.md) | Step-by-step tasks | ✅ Complete |

## Key Deliverables

1. **Metadata Sidecar Files** - JSON files alongside images storing both prompts, seed, dimensions
2. **Info Button** - Unobtrusive ⓘ button in lightbox corner
3. **Info Panel** - Slide-in panel (320px from right) with all metadata
4. **Copy Actions** - Copy original or final prompt to clipboard

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Metadata storage | JSON sidecar files | Human-readable, no dependencies, survives restarts |
| Panel style | Slide-in from right | Doesn't cover image, works for all aspect ratios |
| Metadata loading | Lazy (on panel open) | Faster gallery load |
| API changes | Additive only | Backward compatible |

## Implementation Phases

```
T1: Backend Metadata Foundation (metadata.py, types.py)
     ↓
T2: Generator Integration (save sidecar on image creation)
     ↓
T3: API Extension (/api/images returns metadata)
     ↓
T4: InfoButton Component ───┬─── T5: InfoPanel Component
                            │         (parallel)
                            ↓
                    T6: Lightbox Integration
                            ↓
                    T7: E2E Validation
```

**Estimated Effort**: 8-9 hours

## Confidence Assessment

| Dimension | Level | Notes |
|-----------|-------|-------|
| Requirements Clarity | 🟢 High | User feedback incorporated, mockups approved |
| Technical Feasibility | 🟢 High | Extends existing patterns, no new dependencies |
| Scope Containment | 🟢 High | Clear boundaries, "Won't Have" list defined |
| Risk Level | 🟢 Low | Additive changes, graceful degradation for edge cases |
| Estimation Accuracy | 🟡 Medium | Generator integration may have hidden complexity |

**Overall Confidence**: 🟢 **High** - Ready to ship

## Dependencies

- None for this spec (foundation for future specs)

## Related Specs

- **003** (future): Gallery Search - will use metadata for filtering
- **004** (future): LiteLLM Integration - app-wide LLM config
- **005** (future): Variable Editor - uses same LLM config

## How to Implement

```bash
# Start implementation
/start:implement 002

# Or manually follow implementation-plan.md
```
