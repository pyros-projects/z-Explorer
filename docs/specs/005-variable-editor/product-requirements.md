# Product Requirements Document

## Validation Checklist

- [x] All required sections are complete
- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Problem statement is specific and measurable
- [x] Problem is validated by evidence (not assumptions)
- [x] Context → Problem → Solution flow makes sense
- [x] Every persona has at least one user journey
- [x] All MoSCoW categories addressed (Must/Should/Could/Won't)
- [x] Every feature has testable acceptance criteria
- [x] Every metric has corresponding tracking events
- [x] No feature redundancy (check for duplicates)
- [x] No contradictions between sections
- [x] No technical implementation details included
- [x] A new team member could understand this PRD

---

## Product Overview

### Vision
A dedicated sub-application for managing prompt variables with AI-powered expansion — curate your `__animal__` and `__art_style__` lists without touching files.

### Problem Statement
Currently, managing prompt variables in Z-Explorer is cumbersome:

1. **File editing required** — Users must manually edit `.txt` or `.md` files in the `library/` directory
2. **No visual feedback** — Can't see how many items exist or preview the file structure
3. **Manual expansion** — Adding new values requires creative effort; no AI assistance
4. **Context switching** — Must leave the app, open a text editor, make changes, return
5. **Discoverability** — New users don't know variables exist or how to create them
6. **No organization tools** — Can't search, filter, or categorize variables easily

Evidence: The `/vars` CLI command shows variables but offers no editing. Users frequently ask "how do I add more values?" and resort to external text editors. Power users want AI to generate variations (e.g., "give me 50 more art styles like these").

### Value Proposition
Z-Explorer's Variable Editor is a dedicated sub-app at `/var-editor` where you can browse, edit, and AI-expand your prompt variables — all without leaving the browser. Comments in your files steer the AI to generate contextually-appropriate additions. Uses the same LLM configuration as the main app (spec 004).

## User Personas

### Primary Persona: The Variable Curator
- **Demographics:** Age 20-45, regular Z-Explorer user, generates images with variables (`__animal__`, `__style__`)
- **Goals:** Build rich variable libraries for diverse image generation, keep variables organized by theme
- **Pain Points:** Manually editing files is tedious, hard to brainstorm 50+ variations, loses creative momentum

### Secondary Persona: The Prompt Engineer
- **Demographics:** Age 25-50, power user, treats variables as a strategic asset
- **Goals:** Create highly-curated lists that produce consistent quality, document variables with comments
- **Pain Points:** No way to categorize within a variable file, AI generation quality varies

### Tertiary Persona: The New User
- **Demographics:** Any age, just discovered variables, wants to try the feature
- **Goals:** Understand what variables are, create their first custom variable
- **Pain Points:** Doesn't know variables exist, intimidated by file editing

## User Journey Maps

### Primary User Journey: AI-Expanding a Variable List
1. **Awareness:** User has an `__art_style__` variable with 10 items, wants more variety
2. **Consideration:** Could manually brainstorm OR use AI to generate similar styles
3. **Adoption:** Opens Variable Editor (`/var-editor`), selects `art_style`
4. **Usage:** Sets count to 30, clicks "Generate", previews AI suggestions, adds to list
5. **Retention:** Saves file, returns to main app with enriched variable library

### Secondary User Journey: Creating a New Variable
1. **Awareness:** User wants a new variable type, e.g., `__camera_angle__`
2. **Consideration:** Needs to create file in correct location with correct format
3. **Adoption:** Opens Variable Editor, clicks "+ New Variable"
4. **Usage:** Names it `camera_angle`, adds initial values, optionally AI-generates more
5. **Retention:** Variable immediately available in main app for generation

### Tertiary User Journey: Discovering Variables
1. **Awareness:** New user sees `__animal__` in example prompts, wonders what it means
2. **Consideration:** Clicks `/vars` in CLI, sees list but wants to explore more
3. **Adoption:** Types `/vars edit` or navigates to `/var-editor`
4. **Usage:** Browses existing variables, understands the format, tries editing one
5. **Retention:** Creates their own variable, becomes power user

## Feature Requirements

### Must Have Features

#### Feature 1: Variable List Sidebar
- **User Story:** As a user, I want to see all my variables in one place so that I can quickly navigate between them
- **Acceptance Criteria:**
  - [x] Sidebar shows all `.txt` and `.md` files from `library/` directory
  - [x] Each variable shows name and item count (e.g., "art_style (47)")
  - [x] Click to select and load into editor
  - [x] Search/filter box to find variables
  - [x] "New Variable" button to create new files

#### Feature 2: Text Editor Panel
- **User Story:** As a user, I want to edit variable files directly in the browser so that I don't need external tools
- **Acceptance Criteria:**
  - [x] Full-height text editor with line numbers
  - [x] One value per line format preserved
  - [x] Comments with `#` prefix highlighted differently
  - [x] Standard keyboard shortcuts (Ctrl+S save, Ctrl+Z undo)
  - [x] Unsaved changes indicator

#### Feature 3: Save/Load Operations
- **User Story:** As a user, I want to save my changes and have them persist so that my work is preserved
- **Acceptance Criteria:**
  - [x] Save button writes changes to file
  - [x] Ctrl+S keyboard shortcut saves
  - [x] Confirmation when leaving with unsaved changes
  - [x] Files saved in correct `library/` location

#### Feature 4: AI Generation Panel
- **User Story:** As a user, I want AI to generate new variable values so that I can rapidly expand my lists
- **Acceptance Criteria:**
  - [x] "Generate" button triggers AI expansion
  - [x] Count selector (10, 20, 30, 50, custom)
  - [x] Generated items shown in preview before adding
  - [x] "Add All" button appends to editor
  - [x] Uses app's LLM configuration (LLM_MODE + LLM_MODEL from spec 004)

#### Feature 5: New Variable Creation
- **User Story:** As a user, I want to create new variables from the editor so that I don't need to manually create files
- **Acceptance Criteria:**
  - [x] "New Variable" button in sidebar
  - [x] Prompt for variable name (validated for file-safe characters)
  - [x] Creates file in `library/` directory
  - [x] New variable immediately selectable in sidebar

### Should Have Features

#### Feature 6: Comment-Driven AI Generation
- **User Story:** As a user, I want comments in my file to guide AI generation so that new items match my categories
- **Acceptance Criteria:**
  - [x] Comments (`# ...`) passed to AI as context
  - [x] AI respects category structure in file
  - [x] Example: `# Anime styles` section gets anime-related generations

#### Feature 7: Guidance Input
- **User Story:** As a user, I want to provide custom guidance for AI generation so that I can steer the output
- **Acceptance Criteria:**
  - [x] Text input for additional guidance (e.g., "focus on realistic photography")
  - [x] Guidance included in AI prompt
  - [x] Optional — generation works without guidance

#### Feature 8: Keyboard Navigation
- **User Story:** As a power user, I want keyboard shortcuts for efficiency
- **Acceptance Criteria:**
  - [x] Ctrl+S: Save current file
  - [x] Ctrl+G: Generate with AI
  - [x] Ctrl+N: New variable
  - [x] Escape: Return to main app

### Could Have Features

#### Feature 9: Regenerate Option
- **User Story:** As a user, I want to regenerate if AI output isn't good so that I can try again
- **Acceptance Criteria:**
  - [x] "Regenerate" button in preview
  - [x] Same settings, different output

#### Feature 10: Cherry-Pick Items
- **User Story:** As a user, I want to select individual generated items so that I only add the good ones
- **Acceptance Criteria:**
  - [x] Checkboxes or click-to-toggle on each generated item
  - [x] "Add Selected" button
  - [x] Counter shows "5 of 20 selected"

#### Feature 11: Delete Variable
- **User Story:** As a user, I want to delete variables I no longer need
- **Acceptance Criteria:**
  - [x] Delete button with confirmation
  - [x] File removed from `library/` directory

### Won't Have (This Phase)
- Drag-and-drop reordering of items
- Import from external sources (CSV, JSON)
- Export to other formats
- Variable usage analytics
- Collaborative editing
- Version history / undo beyond session
- Auto-save drafts

## Detailed Feature Specifications

### Feature: AI Generation Panel
**Description:** Right-side panel that uses the app's configured LLM to generate new variable values based on existing content and optional guidance.

**User Flow:**
1. User selects a variable file in sidebar
2. File content loads into editor (center)
3. AI Panel (right) shows generation options
4. User sets count (default 20) and optional guidance
5. User clicks "Generate"
6. Loading indicator while API call in progress
7. Generated items appear in preview list
8. User reviews, can regenerate or add to editor
9. "Add All" appends items to end of editor
10. User saves file with Ctrl+S

**Business Rules:**
- Rule 1: AI uses same LLM configuration as main app (`LLM_MODE`, `LLM_MODEL`)
- Rule 2: Comments in file are included in AI prompt for context
- Rule 3: Generated items must not duplicate existing values
- Rule 4: If LLM fails, show error with retry option
- Rule 5: Preview persists until user adds or regenerates

**Edge Cases:**
- Empty file → AI generates from variable name only
- Very long file (>500 lines) → Truncate context sent to AI, warn user
- LLM not configured → Show helpful message linking to settings
- Network error → Clear error message with retry button
- Generated duplicates → Filter out items already in list

## Success Metrics

### Key Performance Indicators
- **Adoption:** 40% of active users open Variable Editor within first month
- **Engagement:** Average 5+ AI generations per session for users who try the feature
- **Quality:** 80% of generated items are kept (not regenerated)
- **Business Impact:** Increased variable library sizes lead to more diverse generations

### Tracking Requirements

| Event | Properties | Purpose |
|-------|------------|---------|
| `var_editor_opened` | `source: cli\|direct\|link` | Track entry points |
| `variable_selected` | `name: string`, `item_count: number` | Popular variables |
| `variable_saved` | `name: string`, `item_count: number`, `items_added: number` | Edit patterns |
| `ai_generation_started` | `count: number`, `has_guidance: boolean` | AI feature usage |
| `ai_generation_completed` | `count: number`, `duration_ms: number`, `items_kept: number` | AI quality metrics |
| `variable_created` | `name: string` | New variable creation |

---

## Constraints and Assumptions

### Constraints
- **Same LLM config as main app** — No separate model selection in Variable Editor
- **File format preserved** — Must maintain `.txt`/`.md` compatibility with existing system
- **Svelte routing** — Must integrate with existing SPA architecture
- **No database** — Variables stored as files in `library/` directory

### Assumptions
- Users have existing variables or will create new ones
- LLM configuration is already set up (spec 004)
- `library/` directory exists and is writable
- Comments in variable files use `#` prefix consistently

## Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| LLM generates low-quality items | Medium | Medium | Preview before adding, regenerate option |
| Large files slow down editor | Low | Low | Lazy loading, virtualized list |
| File encoding issues | Medium | Low | UTF-8 with fallback, show encoding errors |
| Users overwrite important files | High | Low | Confirmation dialogs, auto-backup before overwrite |

## Open Questions

- [x] Should editor support markdown preview? → **No, just text editing for v1**
- [x] Should we show variable usage count (how often used in prompts)? → **Won't Have this phase**
- [x] Subdirectory support for organizing variables? → **Yes, preserve existing `library/subfolder/` structure**

---

## Supporting Research

### Competitive Analysis
- **ComfyUI**: No built-in variable/wildcard editor, uses external files
- **A1111 Dynamic Prompts**: Has wildcard files but no built-in editor
- **Midjourney**: No variable concept at all

**Conclusion:** Z-Explorer's Variable Editor would be a unique differentiator — no competitor offers integrated AI-powered variable management.

### User Research
From Z-Explorer usage patterns:
- Variables are heavily used by power users
- Most common variables: `__animal__`, `__art_style__`, `__color__`, `__emotion__`
- Users request "bulk add" functionality regularly
- Comments in files are already used for organization

### Market Data
- Prompt engineering tools gaining popularity
- "Wildcard" / variable systems common in SD ecosystem
- AI-assisted content generation becoming expected feature
