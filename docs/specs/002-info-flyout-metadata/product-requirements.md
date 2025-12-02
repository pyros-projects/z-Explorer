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
Let the generated image be the star — metadata available on demand, never stealing attention from the art.

### Problem Statement
Currently, Z-Explorer's lightbox displays the prompt below the image, which:

1. **Steals vertical space** — The prompt card takes ~140px of vertical space, reducing the image display area by 15-20% on typical screens
2. **Always visible** — Users who just want to admire their art must see the prompt whether they want to or not
3. **Limited to final prompt only** — The original template with variables (e.g., `a __animal__ > enhance`) is lost; only the substituted result is shown
4. **No additional metadata** — Useful information like seed, dimensions, creation date, and file size are not accessible
5. **Not persistent** — Prompt data is lost after app restart; no way to know what generated an image from a previous session

Evidence: Screenshots show the prompt card taking significant space below images. User workflow observation confirms users frequently want to see "just the image" or need to recall original prompts to regenerate variations.

### Value Proposition
Z-Explorer gives users the best of both worlds: maximum screen real estate for their generated art by default, with all metadata (both prompts, seed, dimensions, date) available instantly via a single click. Original prompts are preserved for easy regeneration, and metadata persists across sessions via sidecar files.

## User Personas

### Primary Persona: The Prolific Creator
- **Demographics:** Age 20-45, digital artist or AI art enthusiast, moderate technical expertise, uses Z-Explorer daily
- **Goals:** Generate many image variations quickly, find and reuse successful prompts, compare different generation parameters
- **Pain Points:** Loses track of which prompt created which image, can't easily copy the original template to generate more variations, prompt display distracts from evaluating the actual art

### Secondary Persona: The Curator
- **Demographics:** Age 25-50, content creator or designer, selects best images for projects
- **Goals:** Review generated images cleanly, select the best ones, organize and export favorites
- **Pain Points:** Can't view images without prompt clutter, needs to know generation parameters for documentation, wants to regenerate with same seed

## User Journey Maps

### Primary User Journey: Reviewing and Reusing Prompts
1. **Awareness:** User generates a batch of images using variables (`a __animal__ in forest : x10`)
2. **Consideration:** User clicks through gallery to find favorite results
3. **Adoption:** User clicks on an image to open lightbox — sees just the image, full screen
4. **Usage:** User clicks `ⓘ` button to reveal metadata panel → sees original prompt with variables, final substituted prompt, seed, dimensions
5. **Retention:** User copies original prompt to generate more variations, or notes the seed to recreate exact image

### Secondary User Journey: Returning to Previous Session
1. **Awareness:** User opens Z-Explorer the next day, wants to continue from yesterday's work
2. **Consideration:** User browses gallery, sees image they liked
3. **Adoption:** User clicks image, then `ⓘ` button
4. **Usage:** Metadata panel shows all information including original prompt (loaded from sidecar file)
5. **Retention:** User can regenerate or build upon previous work without guessing what settings were used

## Feature Requirements

### Must Have Features

#### Feature 1: Metadata Sidecar Files
- **User Story:** As a creator, I want my generation metadata saved alongside images so that I can access it even after restarting the app
- **Acceptance Criteria:**
  - [x] Each generated image has a corresponding `.json` file with same name
  - [x] Sidecar contains: original prompt, final prompt, seed, width, height, creation timestamp
  - [x] Gallery loads metadata from sidecar files when listing images
  - [x] Images without sidecar files display gracefully with partial/no metadata

#### Feature 2: Info Button Overlay
- **User Story:** As a creator, I want an unobtrusive way to access image metadata so that I can view images without distraction
- **Acceptance Criteria:**
  - [x] Small `ⓘ` button appears in bottom-right corner of lightbox image
  - [x] Button is semi-transparent, doesn't distract from art
  - [x] Button has hover state with visual feedback
  - [x] Button is keyboard accessible

#### Feature 3: Info Panel (Slide-in)
- **User Story:** As a creator, I want to see all metadata about an image in one place so that I can understand how it was generated
- **Acceptance Criteria:**
  - [x] Panel slides in from right when `ⓘ` button clicked
  - [x] Panel displays: original prompt, final prompt, dimensions, seed, creation date, file size
  - [x] Panel has close button and can be dismissed by clicking outside
  - [x] Panel can be toggled with `i` keyboard shortcut
  - [x] Escape key closes panel (or lightbox if panel closed)

#### Feature 4: Copy Prompt Actions
- **User Story:** As a creator, I want to quickly copy prompts so that I can reuse them for new generations
- **Acceptance Criteria:**
  - [x] "Copy Original" button copies the template prompt with variables
  - [x] "Copy Final" button copies the substituted/enhanced prompt
  - [x] Visual feedback confirms copy action (brief highlight or toast)

### Should Have Features

#### Feature 5: Extended Metadata Display
- **User Story:** As a power user, I want to see additional generation details so that I can understand and reproduce results
- **Acceptance Criteria:**
  - [x] Display whether enhancement was used (`>` operator)
  - [x] Display model used (sdnq, hf, etc.) if available
  - [x] Metadata grid layout is scannable and organized

### Could Have Features

#### Feature 6: Regenerate Action
- **User Story:** As a creator, I want to quickly regenerate with the same prompt so that I can create variations
- **Acceptance Criteria:**
  - [x] "Regenerate" button pre-fills CLI with original prompt
  - [x] Optional: include seed for exact reproduction

#### Feature 7: File Actions
- **User Story:** As a curator, I want quick access to file operations so that I can organize my images
- **Acceptance Criteria:**
  - [x] "Open Folder" button opens containing directory in file manager
  - [x] "Delete" button removes image with confirmation

### Won't Have (This Phase)
- Search functionality (separate spec: 003)
- Filtering by metadata fields
- Batch metadata editing
- Metadata export to CSV/JSON
- Image comparison view
- Tagging or categorization

## Detailed Feature Specifications

### Feature: Info Panel
**Description:** A slide-in panel that appears from the right side of the lightbox, displaying comprehensive metadata about the selected image.

**User Flow:**
1. User clicks on image in gallery to open lightbox
2. User sees image with small `ⓘ` button in corner
3. User clicks `ⓘ` or presses `i` key
4. Panel slides in from right (300ms animation)
5. User views metadata, copies prompts as needed
6. User clicks `×`, presses Escape, or clicks outside to dismiss
7. Panel slides out (200ms animation)

**Business Rules:**
- Rule 1: Original prompt must always be displayed if available, even if same as final prompt
- Rule 2: Missing metadata fields show placeholder text ("Not available") rather than being hidden
- Rule 3: Copy buttons only appear for fields that have content
- Rule 4: Panel width is fixed (320px) regardless of content length
- Rule 5: Long prompts should be scrollable within their container

**Edge Cases:**
- Image has no sidecar file → Show "Metadata not available" with explanation
- Sidecar file is corrupted/invalid JSON → Show partial data or error state
- Original and final prompts are identical → Show both with note "No enhancement applied"
- Very long prompts (>1000 chars) → Scrollable container with max-height
- Image deleted while panel open → Close panel, show toast notification

## Success Metrics

### Key Performance Indicators
- **Adoption:** 80% of lightbox sessions include at least one panel open within first week
- **Engagement:** Average 2+ prompt copies per session for users who open panel
- **Quality:** <1% error rate for metadata loading from sidecar files
- **Business Impact:** Increased session length as users engage more deeply with their creations

### Tracking Requirements

| Event | Properties | Purpose |
|-------|------------|---------|
| `lightbox_opened` | `has_metadata: boolean` | Track metadata availability |
| `info_panel_opened` | `trigger: button|keyboard` | Measure adoption and input preference |
| `info_panel_closed` | `method: button|escape|outside|keyboard` | Understand dismissal patterns |
| `prompt_copied` | `type: original|final` | Track which prompt type is more useful |
| `action_clicked` | `action: regenerate|open_folder|delete` | Measure action button usage |

---

## Constraints and Assumptions

### Constraints
- Must work within existing Svelte/FastAPI architecture
- Sidecar files must not break existing image loading behavior
- Panel must not interfere with existing lightbox navigation (if any)
- Must maintain current app performance (<100ms for panel open)

### Assumptions
- Users have sufficient disk space for sidecar files (~1KB per image)
- Original prompt is available at generation time (before variable substitution)
- File system supports creating JSON files alongside images
- Users prefer on-demand metadata over always-visible

## Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Sidecar files clutter output directory | Low | Medium | Use same filename with .json extension for easy association |
| Old images have no metadata | Medium | High | Graceful degradation — show what's available, explain missing data |
| Panel animation causes jank | Medium | Low | Use CSS transforms and will-change for GPU acceleration |
| Users don't discover the `ⓘ` button | High | Medium | Subtle pulse animation on first lightbox open, keyboard shortcut hint |

## Open Questions

- [x] Should panel stay open when navigating between images in lightbox? → **Decision: Close on navigation for cleaner UX**
- [x] What happens if sidecar file exists but image is deleted? → **Decision: Orphaned sidecars are ignored, cleanup is manual**
- [x] Should we migrate existing images by parsing filenames for seed? → **Decision: No, only new images get full metadata**

---

## Supporting Research

### Competitive Analysis
- **Midjourney:** Shows prompt in a bar below image, no hide option — cluttered but familiar
- **DALL-E:** Minimal metadata display, focuses on image — clean but lacks information
- **ComfyUI:** Embeds metadata in PNG, requires external tools to read — powerful but not user-friendly
- **Stable Diffusion WebUI (A1111):** Info tab with full generation parameters — comprehensive but separate view

**Conclusion:** Z-Explorer's approach (hidden by default, slide-in panel) balances clean display with comprehensive metadata access better than competitors.

### User Research
Based on observation of Z-Explorer usage patterns:
- Users frequently ask "what prompt made this image?"
- Users want to copy prompts to iterate on successful generations
- The `>` enhancement operator is popular, making original vs final prompt distinction valuable
- Batch generation with variables means users generate many images per session

### Market Data
- AI image generation tools market growing rapidly
- User expectation for metadata/provenance tracking increasing
- "Prompt engineering" as a skill means users value prompt preservation
