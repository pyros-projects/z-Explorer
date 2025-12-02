# Spec 005: Variable Editor

## Quick Summary

**What**: A standalone sub-application for creating and editing prompt variables with AI-powered expansion. Accessible at `/var-editor` route.

**Why**: Currently, variable files must be edited manually with a text editor. This adds friction when creating new variables or expanding existing ones with AI-generated content.

**Status**: ✅ Ready for Implementation

## Specification Documents

| Document | Purpose | Status |
|----------|---------|--------|
| [product-requirements.md](./product-requirements.md) | What to build and why | ✅ Complete |
| [solution-design.md](./solution-design.md) | How to build it | ✅ Complete |
| [implementation-plan.md](./implementation-plan.md) | Step-by-step tasks | ✅ Complete |

## Key Deliverables

1. **Three-Panel Layout** - Sidebar (list) + Editor (text) + AI Panel (generation)
2. **Variable CRUD** - Create, read, update, delete variable files
3. **AI Expansion** - Generate new items using LLM with optional guidance
4. **Route Navigation** - `/var-editor` within existing SPA
5. **Keyboard Shortcuts** - Ctrl+S to save, standard text editing

## UI Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  [← Back]              Variable Editor                          │
├───────────┬─────────────────────────────────┬───────────────────┤
│           │                                 │                   │
│ Variables │                                 │    AI Panel       │
│ ────────  │                                 │    ─────────      │
│ [Search]  │   # Art style categories        │                   │
│           │   abstract                      │  Count: [20 ▼]    │
│ ● animals │   expressionist                 │                   │
│   art_sty │   impressionist                 │  Guidance:        │
│   colors  │   minimalist                    │  [____________]   │
│   moods   │   photorealistic                │                   │
│           │   surrealist                    │  [Generate ↻]     │
│           │   watercolor                    │                   │
│           │   |                             │  Preview:         │
│ [+ New]   │                                 │  - neo-baroque    │
│           │                 [● unsaved]     │  - art deco       │
│           │                                 │  [Add All]        │
├───────────┴─────────────────────────────────┴───────────────────┤
│  Items: 7 | Lines: 12 | File: library/art_style.txt  [Save ⌘S] │
└─────────────────────────────────────────────────────────────────┘
```

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Layout | Three-panel (sidebar + editor + AI) | Context always visible, matches mockup |
| Navigation | Route-based (`/var-editor`) | Clean URL, proper back button behavior |
| AI Function | Reuse `generate_prompt_variable_values()` | Already handles local/cloud modes |
| Storage | File-based (library/*.txt) | Existing system works, git-friendly |

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/variables` | GET | List all variables (existing) |
| `/api/variables/{name}` | GET | Get variable content |
| `/api/variables/{name}` | PUT | Update variable content |
| `/api/variables` | POST | Create new variable |
| `/api/variables/{name}` | DELETE | Delete variable |
| `/api/variables/generate` | POST | Generate items with AI |

## Implementation Phases

```
T1: Backend CRUD API
     ↓
T2: AI Generation Endpoint
     ↓
T3: Frontend Routing & Shell
     ↓
T4: VarSidebar Component
     ↓
T5: VarTextEditor Component
     ↓
T6: VarAIPanel Component
     ↓
T7: Integration & Full Flow
```

**Estimated Effort**: ~7-8 hours

## Confidence Assessment

| Dimension | Level | Notes |
|-----------|-------|-------|
| Requirements Clarity | 🟢 High | Mockup exists, behavior well-defined |
| Technical Feasibility | 🟢 High | Standard CRUD + existing LLM integration |
| Scope Containment | 🟢 High | Self-contained sub-app, clear boundaries |
| Risk Level | 🟢 Low | No external dependencies beyond existing |
| Estimation Accuracy | 🟡 Medium | Frontend work can vary |

**Overall Confidence**: 🟢 **High** - Ready to ship

## Dependencies

- **004: LiteLLM Integration** - Variable Editor uses the LLM configuration from this spec. Can be developed in parallel but AI features require 004 to be complete.

## Related Specs

- **002**: Info Flyout & Metadata (no dependency)
- **003**: Gallery Search (no dependency)
- **004**: LiteLLM Integration (AI features depend on this)

## How to Implement

```bash
/start:implement 005
```

## Feature Walkthrough

### Creating a New Variable

1. Navigate to `/var-editor`
2. Click "+ New" in sidebar
3. Enter variable name (e.g., "weather")
4. File `library/weather.txt` is created
5. Type values, one per line
6. Press Ctrl+S to save

### AI-Powered Expansion

1. Select a variable with some existing content
2. In AI Panel, set count (e.g., 30)
3. Optionally add guidance: "more extreme weather events"
4. Click "Generate"
5. Review preview (duplicates auto-filtered)
6. Click "Add All" to append to editor
7. Save the file

### Variable File Format

```
# Weather conditions for atmospheric prompts
sunny
cloudy
rainy
stormy
foggy

# Extreme weather
blizzard
hurricane
tornado
```

Lines starting with `#` are comments. They're preserved and used as context for AI generation.
