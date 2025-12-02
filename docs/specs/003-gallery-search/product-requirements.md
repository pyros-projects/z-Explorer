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
Find any generated image instantly by searching the prompts that created it.

### Problem Statement
As users generate hundreds or thousands of images with Z-Explorer, finding specific ones becomes increasingly frustrating:

1. **No discovery mechanism** — Users must scroll through entire gallery to find images
2. **Memory-dependent** — "Where's that emo girl with the corset?" requires remembering approximate generation time
3. **Wasted time** — Searching for a specific image can take minutes of scrolling
4. **Lost inspiration** — Great prompts are buried among hundreds of results, never to be reused

Evidence: Users with 100+ generated images spend significant time scrolling through the gallery. The output directory quickly becomes unwieldy without any filtering capability. Prompt reuse is valuable but requires finding the original.

### Value Proposition
Z-Explorer lets users find any image in under 1 second by searching their prompts — both the original template with variables AND the final generated text. No more endless scrolling; just type and find.

## User Personas

### Primary Persona: The Prolific Creator
- **Demographics:** Age 20-45, digital artist or AI art enthusiast, generates 20-100+ images per session, returns daily
- **Goals:** Find successful prompts to iterate on, locate specific images for export/sharing, maintain creative momentum without getting bogged down searching
- **Pain Points:** Loses track of which prompt created which image, wastes time scrolling through hundreds of thumbnails, can't find that "perfect" image from last week

### Secondary Persona: The Prompt Engineer
- **Demographics:** Age 25-40, technical user, treats Z-Explorer as prompt laboratory, methodical approach
- **Goals:** Find prompts with specific keywords to analyze what worked, compare results across similar prompts, build a mental model of effective prompt patterns
- **Pain Points:** Can't search by specific keywords or phrases, no way to filter by prompt characteristics, hard to find all variations of a theme

## User Journey Maps

### Primary User Journey: Finding a Specific Image
1. **Awareness:** User remembers generating an image with certain keywords ("emo", "corset") but gallery shows hundreds of images
2. **Consideration:** User could scroll through gallery chronologically OR use search to filter directly
3. **Adoption:** User types keywords in search box and instantly sees matching images
4. **Usage:** User finds target image, clicks to view, copies prompt for regeneration
5. **Retention:** User learns to rely on search instead of scrolling, generates more freely knowing images are findable

### Secondary User Journey: CLI Search for Power Users
1. **Awareness:** User is in CLI mode generating images, wants to check if they've already generated something similar
2. **Consideration:** Could switch to gallery view OR use inline CLI search
3. **Adoption:** User types `/search emo corset` without leaving CLI context
4. **Usage:** Results appear inline, user sees filenames and prompt snippets
5. **Retention:** CLI workflow remains uninterrupted, search becomes natural part of generation process

## Feature Requirements

### Must Have Features

#### Feature 1: Gallery Search Box
- **User Story:** As a creator, I want to search my generated images by prompt text so that I can find specific images without scrolling
- **Acceptance Criteria:**
  - [x] Search input field visible in gallery header
  - [x] Real-time filtering as user types (debounced)
  - [x] Gallery updates to show only matching images
  - [x] Match count displayed (e.g., "12 of 147 images")
  - [x] Empty search restores full gallery view
  - [x] Escape key clears search
  - [x] Case-insensitive matching

#### Feature 2: Full-Text Prompt Search
- **User Story:** As a creator, I want search to find matches in both my original prompt AND the enhanced prompt so that I can find images regardless of which version contains my keywords
- **Acceptance Criteria:**
  - [x] Search matches against original prompt (with `__variables__`)
  - [x] Search matches against final prompt (after substitution/enhancement)
  - [x] Substring matching (partial words work)
  - [x] Results include images matching in either field

#### Feature 3: CLI Search Command
- **User Story:** As a power user, I want to search from the CLI so that I don't have to switch to the gallery view
- **Acceptance Criteria:**
  - [x] `/search <query>` command available in CLI
  - [x] Returns list of matching filenames with prompt snippets
  - [x] Shows total match count
  - [x] Query can contain multiple words (space-separated, all must match OR any can match?)

### Should Have Features

#### Feature 4: Search Result Highlighting
- **User Story:** As a user, I want to see why an image matched so that I can quickly identify the relevant content
- **Acceptance Criteria:**
  - [x] Matched keywords highlighted in search results (CLI)
  - [x] Hover/tooltip on gallery images shows match context

#### Feature 5: Empty State Guidance
- **User Story:** As a user, I want helpful feedback when no results found so that I can refine my search
- **Acceptance Criteria:**
  - [x] "No images found for '{query}'" message displayed
  - [x] Suggestion to try different keywords or check spelling

### Could Have Features

#### Feature 6: Search History
- **User Story:** As a user, I want to see my recent searches so that I can quickly repeat common queries
- **Acceptance Criteria:**
  - [x] Last 5-10 searches stored locally
  - [x] Dropdown shows history when search box focused
  - [x] Click to repeat a past search

#### Feature 7: Advanced Search Operators
- **User Story:** As a power user, I want to use operators for more precise searches
- **Acceptance Criteria:**
  - [x] Quotes for exact phrase: `"exact phrase"`
  - [x] Minus for exclusion: `-keyword`
  - [x] Field-specific: `original:variable` or `final:enhanced`

### Won't Have (This Phase)
- Fuzzy/semantic search (requires embedding model)
- Search by metadata fields (seed, date, dimensions)
- Saved search queries
- Search result sorting options
- Search within date ranges
- Image similarity search (visual)
- Full regex support

## Detailed Feature Specifications

### Feature: Gallery Search Box
**Description:** A search input field in the gallery header that filters displayed images in real-time based on prompt content.

**User Flow:**
1. User sees search input in gallery header with placeholder "Search prompts..."
2. User types query text
3. After 300ms debounce, gallery filters to show only matching images
4. Match count updates (e.g., "12 of 147 images")
5. User can click any matching image to open lightbox
6. User presses Escape or clears input to reset to full gallery

**Business Rules:**
- Rule 1: Search is case-insensitive ("CAT" matches "cat" and "Cat")
- Rule 2: Multiple words require ALL to match (AND logic) — "emo corset" finds images with BOTH words
- Rule 3: Minimum query length is 2 characters to avoid overwhelming results
- Rule 4: Search runs against metadata from `.json` sidecar files (dependency: spec 002)
- Rule 5: Images without sidecar files are NOT searched but remain visible in unfiltered view

**Edge Cases:**
- Empty query (whitespace only) → Show all images (no filter)
- No matches found → Show "No images found" message, empty gallery area
- Query shorter than 2 chars → Don't filter, show hint "Type 2+ characters"
- Special characters in query → Treat literally, no regex interpretation
- Very long query (>200 chars) → Truncate and search first 200 chars
- Gallery loading while searching → Show loading indicator, queue search

### Feature: CLI Search Command
**Description:** Command-line search that returns matching images without switching to gallery view.

**User Flow:**
1. User types `/search emo corset` in CLI input
2. Results appear in output area formatted as list
3. User can generate new images or run another search

**Output Format:**
```
🔍 Found 3 images matching "emo corset":
  1. z_image_20251202_081226_3534366672.png
     "...beautiful emo woman wearing a sleek black lace corset..."
  2. z_image_20251202_081217_5437692633.png  
     "...emo woman in a flat 2D style, wearing a sheer black dress..."
  3. z_image_20251201_143052_9182736455.png
     "...dark aesthetic, corset with intricate silver detailing..."
```

**Business Rules:**
- Rule 1: Same search logic as gallery (case-insensitive, AND for multiple words)
- Rule 2: Prompt snippets show ~60 chars centered on match with "..." truncation
- Rule 3: Maximum 20 results displayed; if more, show count and suggest narrowing search
- Rule 4: Results ordered by modification time (newest first)

**Edge Cases:**
- No query provided (`/search`) → Show usage hint: "Usage: /search <keywords>"
- No matches → "No images found matching 'query'"
- Query matches 100+ images → Show first 20 with "...and 80 more. Try a more specific query."

## Success Metrics

### Key Performance Indicators
- **Adoption:** 50% of gallery sessions include at least one search within first month
- **Engagement:** Average 3+ searches per session for users who try the feature
- **Quality:** 90% of searches return results (users find what they're looking for)
- **Business Impact:** Reduced time-to-find from 30+ seconds (scrolling) to <5 seconds (search)

### Tracking Requirements

| Event | Properties | Purpose |
|-------|------------|---------|
| `search_started` | `source: gallery\|cli`, `query_length: number` | Track adoption by interface |
| `search_completed` | `query: string`, `result_count: number`, `duration_ms: number` | Measure search quality |
| `search_result_clicked` | `query: string`, `result_index: number` | Understand result relevance |
| `search_cleared` | `method: escape\|clear_button\|new_query` | Track usage patterns |
| `search_no_results` | `query: string` | Identify search gaps |

---

## Constraints and Assumptions

### Constraints
- **Dependency on Spec 002**: Gallery search requires metadata sidecar files (`.json`) from spec 002 to function. Images without sidecars cannot be searched.
- **Client-side performance**: Search must remain responsive (<100ms) even with 1000+ images
- **No external services**: Search runs entirely locally; no cloud indexing or APIs

### Assumptions
- Users have spec 002 implemented (metadata sidecars exist)
- Average user has <1000 images in output directory
- Simple substring search is sufficient for v1 (no semantic/embedding-based search)
- Users primarily search by keywords in prompts, not by metadata fields

## Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Large galleries cause slow search | Medium | Medium | Implement search indexing or pagination if needed |
| Users expect fuzzy/typo-tolerant search | Low | Medium | Clear UX indicates exact matching; fuzzy is future enhancement |
| Many images lack sidecars (pre-spec-002) | Medium | High | Show all images when unfiltered; note "some images not searchable" |
| CLI search output too verbose | Low | Low | Limit to 20 results with option to narrow |

## Open Questions

- [x] Should multiple words be AND or OR? → **Decision: AND (all words must match)**
- [x] Should CLI `/search` open browser to filtered gallery or stay inline? → **Decision: Stay inline (CLI results)**
- [x] What's the minimum query length? → **Decision: 2 characters**

---

## Supporting Research

### Competitive Analysis
- **Midjourney**: Has `/describe` and web gallery search, but requires Discord context switching
- **DALL-E**: Basic gallery with no search, relies on recency
- **Stable Diffusion WebUI (A1111)**: Has image browser extension with keyword search — proven valuable
- **ComfyUI**: No built-in search; relies on file organization

**Conclusion:** Gallery search is a proven need in AI image tools. Most competitors lack robust local search; Z-Explorer can differentiate with fast, local, full-text search.

### User Research
Based on Z-Explorer usage patterns:
- Users generate batches (10-50 images at a time), leading to rapid gallery growth
- Common search queries: character descriptions ("emo", "witch"), styles ("watercolor", "anime"), objects ("sword", "dress")
- Users often want to find and reuse successful prompt templates

### Market Data
- AI image generation users increasingly generate 100+ images per session
- "Prompt management" is emerging as a category (Promptbase, PromptHero)
- Local-first tools valued for privacy and speed
