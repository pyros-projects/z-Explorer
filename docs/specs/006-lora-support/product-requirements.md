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
Enable z-Explorer users to apply LoRA style adapters with the same zero-friction experience as other features: drop files in a folder, use by name in prompts, no configuration required.

### Problem Statement
Users who want consistent visual styles or character appearances across generations currently have no way to apply trained LoRA adapters in z-Explorer. This forces them to:
1. Use more complex tools (ComfyUI, A1111) with steep learning curves
2. Rely solely on prompt engineering, which produces inconsistent results
3. Abandon z-Explorer for style-consistent workflows

The consequence: z-Explorer loses users to more complex alternatives for anything requiring style consistency.

### Value Proposition
Unlike ComfyUI's node-based LoRA system or A1111's separate configuration panels, z-Explorer's LoRA support:
- **Zero setup**: Drop `.safetensors` files in a folder, immediately usable by filename
- **Familiar syntax**: Uses existing batch parameter pattern (`: lora:0.8`) users already know
- **Progressive disclosure**: Beginners ignore it; power users get precise control
- **No spaghetti**: No extra UI panels, nodes, or configuration files required

## User Personas

### Primary Persona: The Experimenter
- **Demographics:** 25-45, hobbyist or semi-professional artist, comfortable with command-line basics
- **Goals:** Test different visual styles quickly, find the right look through iteration, combine styles creatively
- **Pain Points:** Frustrated by ComfyUI's complexity; wants quick A/B testing of styles without managing nodes or configs

### Secondary Persona: The Creative
- **Demographics:** 18-35, casual user, minimal technical experience
- **Goals:** Apply a consistent look to all generations without learning technical details
- **Pain Points:** "My character looks different every time" - wants one-click style consistency

## User Journey Maps

### Primary User Journey: First-Time LoRA Usage
1. **Awareness:** User downloads a LoRA from Civitai/HuggingFace for their favorite art style
2. **Consideration:** Wonders "can z-Explorer use this?" - checks docs or Settings
3. **Adoption:** Drops `.safetensors` file into `loras/` folder, types `a cat : anime`, sees styled output
4. **Usage:** Experiments with weights (`anime:0.5`), combines multiple LoRAs (`anime:0.8, sketch:0.4`)
5. **Retention:** LoRAs become part of regular workflow; creates personal LoRA collection

### Secondary User Journey: Style Iteration
1. **Trigger:** User wants to find the perfect weight for a character LoRA
2. **Action:** Uses batch syntax `portrait : character:0.5, x5` then `portrait : character:0.7, x5`
3. **Comparison:** Reviews gallery, identifies ideal weight
4. **Refinement:** Combines with other LoRAs `portrait : character:0.7, lighting:0.4`

## Feature Requirements

### Must Have Features

#### Feature 1: LoRA File Discovery
- **User Story:** As a user, I want to drop LoRA files in a folder and use them by filename so that I don't need to configure anything
- **Acceptance Criteria:**
  - [ ] System scans `LORA_DIR` (default: `./loras`) for `.safetensors` files at generation time
  - [ ] LoRA identifier = filename without extension (e.g., `anime.safetensors` → `anime`)
  - [ ] Files with spaces/special chars work when quoted in prompt
  - [ ] Invalid/corrupted files are skipped with warning in progress stream, don't break generation
  - [ ] New LoRAs available immediately (no restart required)

#### Feature 2: Prompt Syntax for LoRA Application
- **User Story:** As a user, I want to apply LoRAs using the same batch parameter syntax I already know so that I don't learn new patterns
- **Acceptance Criteria:**
  - [ ] `prompt : lora_name` applies LoRA at default weight (0.8)
  - [ ] `prompt : lora_name:0.7` applies LoRA at specified weight
  - [ ] `prompt : lora1, lora2:0.5, x4` combines multiple LoRAs with batch params
  - [ ] LoRA params can appear in any position among batch params
  - [ ] Unknown LoRA names produce warning but don't fail generation

#### Feature 3: Multiple LoRA Support
- **User Story:** As a user, I want to combine multiple LoRAs so that I can mix styles (e.g., character + lighting)
- **Acceptance Criteria:**
  - [ ] Up to 4 LoRAs can be applied simultaneously
  - [ ] Each LoRA has independent weight control
  - [ ] LoRAs applied in order specified in prompt (left to right)
  - [ ] Warning shown if using more than 4 LoRAs

#### Feature 4: LoRA Directory Configuration
- **User Story:** As a user, I want to configure where my LoRAs are stored so that I can use my existing collection
- **Acceptance Criteria:**
  - [ ] `LORA_DIR` environment variable sets the directory
  - [ ] Settings API accepts `lora_dir` for session override
  - [ ] GUI Settings dialog includes LoRA directory field
  - [ ] Default: `./loras` in project root (created if doesn't exist)

### Should Have Features

#### Feature 5: LoRA Autocomplete
- **User Story:** As a user, I want to see available LoRAs while typing so that I don't need to remember filenames
- **Acceptance Criteria:**
  - [ ] FakeCLI shows available LoRA names after typing `:`
  - [ ] Autocomplete filters as user types
  - [ ] Shows weight syntax hint (e.g., `anime:0.8`)

#### Feature 6: Progress Feedback
- **User Story:** As a user, I want to see which LoRAs are being applied so that I know my syntax worked
- **Acceptance Criteria:**
  - [ ] Progress stream shows "✨ Found LoRA: anime (weight: 0.8)" for each detected LoRA
  - [ ] Progress stream shows "⚠️ LoRA not found: xyz" for missing LoRAs
  - [ ] Progress stream shows "⚠️ Weight clamped: 2.5 → 2.0" for invalid weights
  - [ ] All warnings appear in same progress stream as generation status (CLI and GUI)

### Could Have Features

#### Feature 7: Optional Metadata File
- **User Story:** As a power user, I want to set default weights and descriptions for my LoRAs
- **Acceptance Criteria:**
  - [ ] Optional `loras/loras.yaml` file with custom weights and descriptions
  - [ ] Metadata overrides default weight (0.8)
  - [ ] Works without YAML file (zero config baseline)
- **YAML Format Example:**
  ```yaml
  anime:
    weight: 0.85
    description: "Anime/manga visual style"
  sketch:
    weight: 0.6
  ```

#### Feature 8: List LoRAs Command
- **User Story:** As a user, I want to see what LoRAs are available without leaving the prompt
- **Acceptance Criteria:**
  - [ ] `/loras` command shows available LoRAs with default weights
  - [ ] Shows LoRA count and directory path
- **Output Format Example:**
  ```
  📁 LoRA Directory: ./loras (3 files)
  
    anime        (default: 0.85)
    sketch       (default: 0.6)
    cinematic    (default: 0.8)
  ```

### Won't Have (This Phase)

- **LoRA training integration**: Users train elsewhere, import here
- **LoRA preview thumbnails**: File-based discovery is sufficient
- **LoRA strength curves**: Varying weight during generation is complex
- **Online LoRA download**: Users manage their own files
- **Separate CLIP weight**: Single weight is sufficient for MVP
- **LoRA compatibility checking**: Trust users to use compatible LoRAs

## Detailed Feature Specifications

### Feature: Prompt Syntax for LoRA Application
**Description:** LoRAs are applied using the existing batch parameter syntax, appearing after the `:` separator. The parser distinguishes LoRAs from batch params by checking against known param names and the LoRA directory.

**User Flow:**
1. User types prompt with LoRA: `a portrait : anime:0.8, x3`
2. System parses batch params, identifies `anime` as LoRA (exists in LORA_DIR)
3. System shows progress: "Found LoRA: anime (weight: 0.8)"
4. System generates 3 images with LoRA applied

**Business Rules:**
- Rule 1: When weight is omitted, use default weight (0.8)
- Rule 2: When weight exceeds 2.0, clamp to 2.0 and warn user
- Rule 3: When weight is below 0, clamp to 0 and warn user
- Rule 4: When LoRA file not found, warn and continue without it
- Rule 5: When same LoRA specified twice, use last specified weight

**Edge Cases:**
- Scenario 1: LoRA name conflicts with batch param (e.g., user has `x4.safetensors`) → Expected: Known batch params (`x`, `w`, `h`, `seed`, `steps`) always take precedence; warn if LoRA name matches
- Scenario 2: Empty LORA_DIR → Expected: No autocomplete; LoRAs in prompt produce warnings
- Scenario 3: LoRA + variable: `__animal__ : anime` → Expected: Variable resolves first (Phase 1), LoRA applies in Phase 2
- Scenario 4: LORA_DIR doesn't exist → Expected: Create directory; continue normally
- Scenario 5: LORA_DIR changed mid-session via Settings API → Expected: New directory used for next generation; in-flight generations unaffected
- Scenario 6: LoRA file deleted while in use → Expected: Warning on next generation; graceful degradation

## Success Metrics

### Key Performance Indicators

- **Adoption:** 30% of active users try LoRA feature within first month
- **Engagement:** Users who try LoRAs use them in 50%+ of subsequent sessions
- **Quality:** <5% of LoRA-related generations produce errors/warnings
- **Retention:** No increase in user churn after feature launch

### Tracking Requirements

| Event | Properties | Purpose |
|-------|------------|---------|
| `lora_applied` | lora_name, weight, count_in_prompt | Track which LoRAs are popular |
| `lora_not_found` | attempted_name | Identify common typos or missing LoRAs |
| `lora_weight_clamped` | original_value, clamped_to | Track misuse of weight syntax |
| `lora_generation_complete` | lora_count, generation_time | Track performance impact |

---

## Constraints and Assumptions

### Constraints
- **Memory:** LoRAs must work within existing GPU memory budget (LoRAs are small, ~2-200MB)
- **Dependency:** Requires `peft` library for LoRA loading
- **Compatibility:** Only `.safetensors` format supported initially
- **Platform:** Must work on Windows, macOS, Linux like existing features

### Assumptions
- Users have LoRA files already (downloaded from Civitai, HuggingFace, or trained elsewhere)
- Users understand weight concept (0 = no effect, 1 = full effect)
- LoRAs are compatible with Z-Image-Turbo base model (user responsibility)
- Default weight of 0.8 is reasonable starting point for most LoRAs

## Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| LoRA causes corrupted output | High | Medium | Show weight recommendations; allow easy removal |
| Users confused by weight syntax | Medium | Low | Clear documentation; autocomplete hints |
| Memory issues with many LoRAs | Medium | Low | Limit to 4 simultaneous; show memory warnings |
| Incompatible LoRA crashes generation | High | Low | Catch errors gracefully; skip problematic LoRA |

## Open Questions

- [x] ~~Syntax: Use `@name` or reuse batch params `name:weight`?~~ → Decision: Reuse batch params for consistency
- [x] ~~Default weight: 0.8 or 1.0?~~ → Decision: 0.8 (common recommendation from LoRA community)
- [ ] Should we support nested LoRA directories or flat only? → Leaning flat for simplicity

---

## Supporting Research

### Competitive Analysis
- **ComfyUI:** Requires separate "Load LoRA" nodes per LoRA; powerful but complex. Users complain about "bloated workflows" with many LoRAs.
- **A1111:** Uses `<lora:name:weight>` inline syntax; familiar but different from z-Explorer patterns. Memory leak issues during long sessions.
- **InvokeAI:** GUI-based LoRA selection; cleaner than ComfyUI but requires UI interaction.

z-Explorer differentiator: Grammar-as-interface (prompt syntax) with zero configuration.

### User Research
- Users cite "consistent character appearance" as top LoRA use case
- Common frustration: Forgetting trigger words and optimal weights
- Users prefer inline syntax over separate configuration panels
- Weight range 0.5-0.8 is most commonly used

### Market Data
- Civitai hosts 100,000+ LoRA models
- LoRA is the most popular fine-tuning method for Stable Diffusion
- "LoRA" search volume has grown 300% in past year
