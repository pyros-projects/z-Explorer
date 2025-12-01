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
Empower users to customize Z-Explorer's interface and model configuration without editing environment files, making local AI image generation accessible and personalized.

### Problem Statement
Z-Explorer currently offers a fixed UI layout with no user customization options:

1. **Gallery Inflexibility:** Fixed thumbnail size (200px height) and single layout style (flex-row) don't suit different content types or screen sizes. Users with portrait-heavy galleries see poorly cropped thumbnails; landscape-heavy users waste vertical space.

2. **Configuration Friction:** Changing models requires editing `.env` files and restarting the server. Technical users want to experiment with different models without leaving the UI.

3. **Wasted Screen Real Estate:** A large empty void exists between the gallery and CLI. The tips section consumes prime space on every visit.

4. **No Persistence:** CLI height preferences reset on reload. Users repeatedly resize panels to their preferred layout.

**Evidence:** Direct user feedback from project owner during UI review session (2025-12-01).

### Value Proposition
Z-Explorer becomes the only local AI image generation tool that combines CLI-first power with GUI-level customization:
- **Instant Personalization:** Adjust gallery layout, thumbnail sizes, and display preferences in seconds
- **Model Hot-Swapping:** Switch between models from a settings dialog without server restarts
- **Space Efficiency:** Every pixel serves a purpose with collapsible sections and flexible layouts
- **Persistent Preferences:** Your setup remembers how you like it

## User Personas

### Primary Persona: The Power Creator
- **Demographics:** 25-45 years old, technical artist or developer, comfortable with CLI tools, generates 20+ images per session
- **Goals:** Rapid iteration on prompts, quick visual comparison of outputs, minimal friction between idea and image
- **Pain Points:**
  - Can't see enough images at once with current thumbnail size
  - Switching models requires editing files and restarting
  - Wasted screen space could show more content

### Secondary Personas

#### The Experimenter
- **Demographics:** Developer or ML enthusiast, tries different models frequently, values flexibility
- **Goals:** Test various image and LLM models, compare outputs across configurations
- **Pain Points:** Model switching is cumbersome, no way to quickly A/B test configurations

#### The Curator
- **Demographics:** Artist or content creator, generates many images, needs organization
- **Goals:** Review and compare generated images efficiently, maintain creative flow
- **Pain Points:** Gallery doesn't adapt to content types, can't customize view to workflow

## User Journey Maps

### Primary User Journey: First-Time Customization
1. **Awareness:** User notices thumbnails are too small to evaluate image quality, or layout doesn't fit their content type
2. **Consideration:** User looks for settings/preferences (gear icon, `/settings` command)
3. **Adoption:** User opens settings dialog, sees clear options with visual previews
4. **Usage:** User selects larger thumbnails and masonry layout, sees immediate preview
5. **Retention:** Settings persist across sessions; user returns to a personalized experience

### Secondary User Journeys

#### Model Experimentation Journey
1. **Trigger:** User wants to try a different image model (e.g., SDNQ variant)
2. **Discovery:** User opens Settings → Models tab
3. **Configuration:** User enters new model repo/path, clicks "Test Connection"
4. **Application:** User clicks "Reload Models" to apply changes
5. **Validation:** Model info bar updates to show new configuration

#### Layout Optimization Journey
1. **Trigger:** User generates batch of portrait images, current layout crops them poorly
2. **Action:** User opens Settings → Gallery → Layout Style
3. **Selection:** User chooses "Masonry Vertical" for better portrait display
4. **Result:** Gallery immediately re-renders with new layout

## Feature Requirements

### Must Have Features

#### Feature 1: Settings Dialog
- **User Story:** As a power creator, I want to access all preferences in one place so that I can customize my experience without editing files
- **Acceptance Criteria:**
  - [ ] Settings dialog opens via gear icon in header
  - [ ] Settings dialog opens via `/settings` CLI command
  - [ ] Dialog has tabbed navigation (Gallery, CLI, Generation, Models)
  - [ ] Settings persist to localStorage and survive browser refresh
  - [ ] "Reset to Defaults" button restores factory settings
  - [ ] Dialog closes on Escape key or clicking outside

#### Feature 2: Gallery Layout Options
- **User Story:** As a curator, I want to choose how my gallery displays images so that I can optimize for my content type
- **Acceptance Criteria:**
  - [ ] Five layout options available: Flex Row (current), Masonry Vertical, Masonry Horizontal, Grid Square, Grid Auto
  - [ ] Layout selection shows visual preview/icon for each option
  - [ ] Layout change applies immediately (no save required for preview)
  - [ ] Selected layout persists across sessions

#### Feature 3: Thumbnail Size Configuration
- **User Story:** As a power creator, I want to adjust thumbnail sizes so that I can see more detail or fit more images on screen
- **Acceptance Criteria:**
  - [ ] Preset sizes: Small (120px), Medium (180px), Large (250px), XL (350px)
  - [ ] Custom size input (80-500px range) with validation
  - [ ] Size change applies immediately to gallery
  - [ ] Selected size persists across sessions

#### Feature 4: Model Settings Override
- **User Story:** As an experimenter, I want to change models from the UI so that I can test different configurations without editing files
- **Acceptance Criteria:**
  - [ ] Models tab shows current active configuration (from .env)
  - [ ] User can override image model: mode (hf_download, hf_local, sdnq, components) and repo/path
  - [ ] User can override LLM model: mode (hf_download, hf_local, gguf, z_image) and repo/path
  - [ ] "Test Connection" validates the configuration before applying
  - [ ] "Reload Models" triggers model unload/reload on backend
  - [ ] Clear indication of which settings are overridden vs. using .env defaults

### Should Have Features

#### Feature 5: Collapsible Tips Section
- **User Story:** As a returning user, I want tips hidden after my first visit so that I have more space for content
- **Acceptance Criteria:**
  - [ ] Tips section collapsed by default for returning users (hasSeenTips flag)
  - [ ] Expandable via "💡 Tips [▼]" toggle
  - [ ] First-time users see tips expanded
  - [ ] Collapse state persists

#### Feature 6: CLI Preferences
- **User Story:** As a power creator, I want my CLI panel size to persist so that I don't resize it every session
- **Acceptance Criteria:**
  - [ ] CLI height persists across sessions
  - [ ] Font size option (Small/Medium/Large)
  - [ ] Option to hide tips on startup

#### Feature 7: Full-Height Gallery Layout
- **User Story:** As a curator, I want the gallery to use available vertical space so that I see more images
- **Acceptance Criteria:**
  - [ ] Gallery expands to fill space between header and CLI
  - [ ] No empty void between gallery and CLI panel
  - [ ] Proper scrolling when images exceed viewport

### Could Have Features

#### Feature 8: Generation Defaults
- **User Story:** As a power creator, I want to set my preferred default dimensions so that I don't specify them every time
- **Acceptance Criteria:**
  - [ ] Default width/height configurable
  - [ ] Default batch count configurable
  - [ ] Auto-enhance toggle (always use LLM enhancement)

#### Feature 9: Prompt on Hover
- **User Story:** As a curator, I want to see the prompt when hovering over an image so that I can recall what generated it
- **Acceptance Criteria:**
  - [ ] Hovering over gallery image shows prompt tooltip
  - [ ] Tooltip styled consistently with app theme
  - [ ] Feature can be disabled in settings

#### Feature 10: Gallery Sort Order
- **User Story:** As a curator, I want to change the order images are displayed so that I can find recent or specific images faster
- **Acceptance Criteria:**
  - [ ] Sort options: Newest First, Oldest First
  - [ ] Sort preference persists

#### Feature 11: Frontend Test Suite
- **User Story:** As a developer, I want comprehensive frontend tests so that I can refactor and add features with confidence
- **Acceptance Criteria:**
  - [ ] Vitest configured as test runner with Svelte support
  - [ ] @testing-library/svelte for component testing
  - [ ] Unit tests for SettingsService (localStorage read/write/validation)
  - [ ] Component tests for Settings dialog (tab navigation, input validation, save/cancel)
  - [ ] Component tests for Gallery layouts (each layout renders correctly)
  - [ ] Integration tests for settings → gallery reactivity (changing settings updates gallery)
  - [ ] E2E tests via Playwright for critical user flows (open settings, change layout, verify persistence)
  - [ ] Test coverage target: 80% for new code
  - [ ] Tests run in CI pipeline (npm run test)

### Won't Have (This Phase)

- **Theme Customization:** Light mode, custom accent colors (future enhancement)
- **Keyboard Shortcuts Configuration:** Custom key bindings
- **Prompt Templates/Favorites:** Saving and loading prompt presets
- **Image Actions Menu:** Download, delete, copy prompt buttons on hover
- **Mobile/Responsive Layout:** Focus on desktop experience first
- **Model Download from UI:** Only switching between already-available models

## Detailed Feature Specifications

### Feature: Settings Dialog

**Description:** A modal dialog providing centralized access to all user preferences, organized into logical tabs. The dialog is the primary interface for customization.

**User Flow:**
1. User clicks gear icon in gallery header OR types `/settings` in CLI
2. System displays modal dialog with tabs: Gallery | CLI | Generation | Models
3. User navigates tabs and adjusts preferences
4. Changes preview immediately where applicable (gallery layout, thumbnail size)
5. User clicks "Save" to persist all changes OR "Cancel" to discard
6. System saves to localStorage and closes dialog

**Business Rules:**
- Rule 1: Settings must persist across browser sessions using localStorage
- Rule 2: Invalid inputs (e.g., thumbnail size outside 80-500px) show inline validation error
- Rule 3: Model changes require explicit "Reload Models" action (not automatic)
- Rule 4: "Reset to Defaults" requires confirmation before executing
- Rule 5: Settings dialog is non-blocking - user can still see gallery behind it

**Edge Cases:**
- Scenario 1: localStorage is full/unavailable → Expected: Show warning, allow session-only settings
- Scenario 2: User enters invalid model path → Expected: "Test Connection" fails with clear error message
- Scenario 3: User closes browser mid-edit → Expected: Unsaved changes are lost, last saved state restored
- Scenario 4: Backend offline when changing model settings → Expected: Show connection error, disable model actions

### Feature: Model Settings Override

**Description:** Allows users to override `.env` model configuration from the UI without editing files or restarting the server.

**User Flow:**
1. User opens Settings → Models tab
2. System displays current active configuration (from .env or previous override)
3. User selects new mode from dropdown (hf_download, hf_local, etc.)
4. User enters repository name or local path
5. User clicks "Test Connection"
6. System validates path exists (for local) or repo is accessible (for HF)
7. User clicks "Reload Models" to apply
8. System unloads current models and loads new configuration
9. Model info bar in CLI updates to reflect new configuration

**Business Rules:**
- Rule 1: Override settings are stored in localStorage, NOT written to .env
- Rule 2: Override settings take precedence over .env when present
- Rule 3: "Use .env default" option clears the override for that setting
- Rule 4: Model reload may take 30+ seconds; show loading indicator
- Rule 5: Failed model load should rollback to previous working configuration

**Edge Cases:**
- Scenario 1: User enters non-existent local path → Expected: Test Connection fails with "Path not found" error
- Scenario 2: User enters invalid HF repo → Expected: Test Connection fails with "Repository not accessible" error
- Scenario 3: Model reload fails mid-process → Expected: Rollback to previous config, show error with details
- Scenario 4: User clears all overrides → Expected: System reverts to .env configuration on next reload

## Success Metrics

### Key Performance Indicators

- **Adoption:** 80% of active users open settings dialog within first 3 sessions
- **Engagement:** 60% of users change at least one gallery setting (layout or thumbnail size)
- **Quality:** <5% error rate on model configuration changes
- **Satisfaction:** Settings dialog task completion rate >90% (user successfully saves preferences)

### Tracking Requirements

| Event | Properties | Purpose |
|-------|------------|---------|
| `settings_opened` | `trigger: 'icon' \| 'command'` | Measure discovery methods |
| `settings_tab_viewed` | `tab: string` | Understand which settings matter most |
| `setting_changed` | `category, setting, old_value, new_value` | Track specific preferences |
| `settings_saved` | `changes_count` | Measure successful completions |
| `settings_reset` | - | Track reset frequency |
| `model_test_connection` | `model_type, mode, success` | Monitor model config reliability |
| `model_reload` | `model_type, mode, success, duration_ms` | Track model switching performance |
| `gallery_layout_changed` | `layout` | Most popular layout choices |
| `thumbnail_size_changed` | `size_preset \| custom_px` | Popular size preferences |
| `test_suite_run` | `passed, failed, coverage_pct` | CI/development quality tracking |

---

## Constraints and Assumptions

### Constraints
- **Browser Storage:** localStorage has ~5MB limit; settings should use <10KB
- **No Backend Changes for Preferences:** Gallery/CLI settings are frontend-only (localStorage)
- **Backend Model API:** Model override requires new/extended API endpoint
- **Single User:** No multi-user or cloud sync for settings
- **Desktop Focus:** Optimized for 1280px+ viewport widths

### Assumptions
- Users have modern browsers with localStorage support (Chrome, Firefox, Safari, Edge)
- Users understand the concept of model modes (hf_download vs hf_local) from setup wizard
- Backend can handle model unload/reload requests via API
- Model reload time is acceptable (30-60 seconds for typical models)

## Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Model reload fails, leaves system in broken state | High | Medium | Implement rollback mechanism; keep previous config until new one validates |
| localStorage gets corrupted | Medium | Low | Validate settings on load; fallback to defaults if invalid |
| Settings dialog overwhelms new users | Medium | Low | Start with sensible defaults; progressive disclosure of advanced options |
| Performance impact from custom layouts | Medium | Medium | Test all layouts with 100+ images; optimize rendering |
| Users confuse override vs .env settings | Medium | Medium | Clear visual distinction; "Using override" vs "Using .env" labels |

## Open Questions

- [x] ~~Should model overrides persist to .env or stay runtime-only?~~ **Decision: Runtime-only (localStorage)**
- [x] ~~Full gallery (Option A) or split with focus preview (Option B)?~~ **Decision: Option A (full-height gallery)**
- [x] ~~Include prompt favorites in Phase 1?~~ **Decision: No, Won't Have for this phase**
- [x] ~~Any mobile/responsive consideration?~~ **Decision: Desktop-first, mobile out of scope**

---

## Supporting Research

### Competitive Analysis

| Tool | Settings Approach | Gallery Customization | Model Switching |
|------|-------------------|----------------------|-----------------|
| **ComfyUI** | Node-based, no centralized settings | Fixed layout | Requires workflow edit |
| **Automatic1111** | Settings tab with 100+ options | Limited (grid only) | Dropdown in header |
| **Midjourney** | No settings (Discord-based) | N/A | `/settings` command |
| **InvokeAI** | Comprehensive settings panel | Gallery view options | Model manager panel |

**Key Insight:** Most tools either have no customization (Midjourney) or overwhelming options (A1111). InvokeAI strikes a balance we can learn from.

### User Research
- Direct feedback from project owner (Pyro) during 2025-12-01 UI review session
- Pain points identified: wasted space, fixed thumbnails, model switching friction
- Explicit request for settings system with gallery layouts, thumbnail sizes, and model overrides

### Market Data
- Local AI image generation tools growing rapidly post-Stable Diffusion release
- Technical users prefer customization but abandon tools with steep learning curves
- CLI-first approach differentiates from GUI-heavy competitors
