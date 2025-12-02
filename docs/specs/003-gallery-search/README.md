# Spec 003: Gallery Search

## Quick Summary

**What**: Add full-text search to find images by prompt content — both in the gallery UI and via CLI command.

**Why**: As users generate hundreds of images, finding specific ones becomes impossible. "Where's that emo girl with the corset?" requires endless scrolling.

**Status**: ✅ Ready for Implementation

**Dependency**: Requires [Spec 002](../002-info-flyout-metadata/) (metadata sidecars)

## Specification Documents

| Document | Purpose | Status |
|----------|---------|--------|
| [product-requirements.md](./product-requirements.md) | What to build and why | ✅ Complete |
| [solution-design.md](./solution-design.md) | How to build it | ✅ Complete |
| [implementation-plan.md](./implementation-plan.md) | Step-by-step tasks | ✅ Complete |

## Key Deliverables

1. **Gallery Search Box** - Real-time filtering in gallery header
2. **Full-Text Search** - Matches both original and final prompts
3. **CLI `/search` Command** - Search from terminal without switching views
4. **Smart Snippets** - Show matched text context in CLI results

## Search Features

| Feature | Description |
|---------|-------------|
| Case-insensitive | "CAT" matches "cat" |
| Multi-word AND | "emo corset" finds images with BOTH words |
| Debounced | 300ms delay prevents excessive filtering |
| Client-side | Gallery filters instantly without API call |
| Server-side | CLI gets structured results with snippets |

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Gallery filtering | Client-side | Instant feedback, no network latency |
| CLI search | Server-side | Structured response with snippets |
| Multiple terms | AND logic | More precise results |
| API design | Extend `/api/images` | Single endpoint, optional `q` parameter |

## Implementation Phases

```
T1: Backend Search (/api/images?q=...)
     ↓
T2: SearchBox Component ─────┐
                              ├─── T3: Gallery Integration
                              │
                              ↓
                        T4: CLI /search Command
                              ↓
                        T5: E2E Validation
```

**Estimated Effort**: ~6 hours

## Confidence Assessment

| Dimension | Level | Notes |
|-----------|-------|-------|
| Requirements Clarity | 🟢 High | Clear use cases, decided on AND logic |
| Technical Feasibility | 🟢 High | Simple substring matching, no dependencies |
| Scope Containment | 🟢 High | Fuzzy search explicitly out of scope |
| Risk Level | 🟢 Low | Additive changes, graceful degradation |
| Estimation Accuracy | 🟢 High | Straightforward implementation |

**Overall Confidence**: 🟢 **High** - Ready to ship

## Dependencies

- **Requires**: Spec 002 (metadata sidecar files provide searchable prompt text)

## Related Specs

- **002**: Info Flyout & Metadata (dependency - provides sidecar files)
- **004** (future): LiteLLM Integration
- **005** (future): Variable Editor

## How to Implement

```bash
# Ensure spec 002 is complete first, then:
/start:implement 003
```

## Usage Examples

**Gallery Search**:
```
🔍 [Search prompts...    ]  Gallery (147)
```
Type "emo corset" → Gallery filters to matching images → "3 of 147"

**CLI Search**:
```
>>> /search emo corset
🔍 Found 3 images matching "emo corset":
  1. z_image_20251202_081226_3534366672.png
     "...beautiful emo woman wearing a sleek black lace corset..."
  2. z_image_20251202_081217_5437692633.png
     "...emo woman in a flat 2D style, wearing a sheer black dress..."
```
