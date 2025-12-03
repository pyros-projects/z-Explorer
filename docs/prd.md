---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
inputDocuments:
  - docs/analysis/brainstorming-session-2025-12-02.md
  - docs/analysis/prompt-operators-brief.md
  - docs/index.md
  - docs/project-overview.md
  - docs/architecture-backend.md
  - docs/architecture-gui.md
  - docs/integration-architecture.md
workflowType: 'prd'
lastStep: 11
project_name: 'z-Explorer'
user_name: 'Andre'
date: '2025-12-03'
---

# Product Requirements Document - z-Explorer Prompt Operators System

**Author:** Andre
**Date:** 2025-12-03
**Version:** 1.0

---

## Executive Summary

### Vision

The **Prompt Operators System** extends z-Explorer's existing prompt manipulation capabilities with an elegant, minimal-syntax language for exploring AI image generation latent space. Users can perform powerful operations—interpolation, blending, temporal scheduling, and more—through intuitive single-character operators that feel natural and expressive.

**Design Philosophy:** *"Wild shit with elegant syntax"* — Maximum power, minimum effort.

### What Makes This Special

1. **Single-Character Elegance**: Core operations use intuitive symbols (`%`, `|`, `+`, `-`, `@`) that read naturally in prompts
2. **Latent Space Access**: Exposes powerful latent space operations without requiring coding or node graphs
3. **Denoising-Level Control**: Manipulate the image generation process at the step level through simple syntax
4. **Progressive Complexity**: Easy operators for beginners, advanced combinations for power users
5. **Built on Proven Stack**: Leverages existing HuggingFace diffusers/transformers APIs for reliable implementation

### Problem Statement

Current prompt engineering for AI image generation exists at two extremes:
- **Too Simple**: Plain text prompts offer limited control over the generation process
- **Too Complex**: Node-based tools like ComfyUI require technical expertise and complex workflows

Users want to **explore the latent space creatively**—morphing between concepts, blending styles, scheduling prompts across denoising steps—without learning new tools or writing code. They want expressiveness through elegance.

## Project Classification

| Dimension | Classification | Rationale |
|-----------|---------------|-----------|
| **Project Type** | `developer_tool` | Creating a DSL (Domain Specific Language) for prompt manipulation |
| **Domain** | `scientific` | AI/ML image generation, latent space exploration |
| **Complexity** | Medium | Novel paradigm built on mature HuggingFace libraries |

---

## Success Criteria

### User Success

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Learning Curve** | User creates first operator-enhanced prompt within 5 minutes | Time to first successful generation |
| **Expressiveness** | Users can achieve effects previously requiring code/nodes | Feature parity check |
| **Adoption** | 70% of active users try operators within first week | Usage analytics |
| **Satisfaction** | "This feels magical" sentiment in feedback | User surveys |

**Success Moments:**
- First successful `cat % dog : 5` interpolation reveals the morph animation
- User discovers `@` scheduling creates effects they couldn't achieve before
- Complex operator chains feel intuitive rather than confusing

### Technical Success

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Parser Reliability** | 99.9% of valid syntax parses correctly | Unit test coverage |
| **Generation Quality** | Operator results match expected behavior | Visual QA + automated tests |
| **Performance** | <100ms parsing overhead per prompt | Benchmarks |
| **Memory Efficiency** | No additional VRAM for operator processing | Memory profiling |

### Business Success

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Feature Adoption** | 50% of generations use at least one operator | Usage analytics |
| **Community Engagement** | Users share operator discoveries/recipes | Social monitoring |
| **Differentiation** | z-Explorer recognized for elegant prompt syntax | Market positioning |

---

## Product Scope

### MVP Strategy: Problem-Solving MVP

Focus on delivering the core latent space exploration capabilities that users can't easily achieve elsewhere. Ship the operators that provide immediate, visible value with minimal implementation complexity.

### Phase 1: Core MVP (Week 1-2)

**10 Operators — The Foundation**

| Operator | Name | Effort | Value |
|----------|------|--------|-------|
| `#` | Seed Control | 🟢 Easy | Reproducibility |
| `+` | Latent Blend | 🟢 Easy | Concept mixing |
| `-` | Latent Subtract | 🟢 Easy | Concept removal |
| `*` | Emphasis | 🟢 Easy | Amplification |
| `!` | Negation | 🟢 Easy | Strong negative |
| `?` | Variation | 🟢 Easy | Exploration |
| `%` | Interpolation | 🟡 Medium | Morph walks |
| `\|` | Alternating | 🟡 Medium | Hybrid creation |
| `@` | Temporal Schedule | 🟡 Medium | Phase control |
| `~` | Smooth Transition | 🟡 Medium | Eased morphs |

**MVP Capabilities:**
- Parse and execute all 10 operators
- Combine operators in single prompts
- Clear error messages for invalid syntax
- Integration with existing variable system

### Phase 2: Power Features (Week 3-4)

| Operator | Name | Effort | Value |
|----------|------|--------|-------|
| `X` | Breeding/Crossover | 🟠 Hard | Genetic mixing |
| `::` | Style Transfer | 🟠 Hard | Style application |
| `??` | Exploration Mode | 🟠 Hard | Diversity generation |
| `@@` | Grid Exploration | 🟡 Medium | 2D parameter sweeps |
| `!!` | Chaos/Glitch | 🟡 Medium | Experimental effects |

### Phase 3: Advanced (Future)

| Operator | Name | Effort | Value |
|----------|------|--------|-------|
| `->` | Direction Vectors | 🟠 Hard | Semantic navigation |
| `=>` | Semantic Gradient | 🟠 Hard | Meaningful progressions |
| Latent Arithmetic | `king - man + woman` | 🟠 Hard | Concept algebra |
| Animation Syntax | Temporal generation | 🔴 Very Hard | Video creation |

### Out of Scope (Not in This PRD)

- LoRA management UI (separate feature)
- Model switching mid-generation
- Cloud/API-based generation
- Multi-image composition tools

---

## User Journeys

### Journey 1: Alex the AI Artist — First Morph Discovery

Alex is a digital artist who uses AI image generation for concept art. They've been frustrated with the randomness of generation—they want to explore the "space between" concepts but don't know how. One evening, they're generating character designs and wonder "what would a warrior-mage hybrid look like at different blend levels?"

They discover z-Explorer's new operators and try:
```
warrior % mage : 10
```

Ten images appear, walking from pure warrior to pure mage. At step 4, they find the perfect balance—a battle-worn spellcaster that's exactly what they imagined. Alex saves the seed and shares the discovery on social media.

**Capabilities Revealed:**
- Latent interpolation (`%` operator)
- Step-based output generation
- Seed capture and saving
- Result visualization

---

### Journey 2: Sam the Prompt Engineer — Style Scheduling Mastery

Sam works with AI-generated marketing images and needs precise control over style application. They've learned that early denoising steps control composition while late steps control style. Previously, this required complex ComfyUI workflows.

With z-Explorer's temporal scheduling, they type:
```
product photography @0-50% cyberpunk aesthetic @50-100%
```

The result: a product shot with dramatic cyberpunk lighting and color grading, but the product placement and composition remain clean and commercial. Sam realizes they can now achieve in one line what took 20 nodes before.

**Capabilities Revealed:**
- Temporal scheduling (`@` operator)
- Percentage-based step ranges
- Multiple prompt segments
- Professional workflow integration

---

### Journey 3: Jordan the Explorer — Chaos and Discovery

Jordan uses AI generation for pure experimentation. They don't have a specific goal—they want to discover unexpected results and happy accidents. They're tired of manually tweaking prompts and want the AI to surprise them.

They try the exploration operators:
```
abstract landscape ?? 20
dragon !! 0.3
cat X robot
```

Each generates something unexpected. The exploration mode (`??`) produces 20 maximally diverse landscapes. The chaos operator (`!!`) creates glitchy, broken-but-beautiful dragons. The breeding operator (`X`) creates bizarre cat-robot hybrids by mixing latent features.

**Capabilities Revealed:**
- Exploration mode (`??` operator)
- Chaos injection (`!!` operator)
- Breeding/crossover (`X` operator)
- Diversity maximization

---

### Journey 4: Dev the Power User — Complex Compositions

Dev is a technical user who wants maximum control. They chain multiple operators together:
```
(warrior + mage : 0.7) @0-30% (detailed * 1.5) @30-70% style :: oil_painting @70-100% #42
```

This creates a 70/30 warrior-mage blend for composition, emphasizes detail in the middle phase, applies oil painting style at the end, all with reproducible seed 42. Dev documents their "recipes" and shares them with the community.

**Capabilities Revealed:**
- Operator chaining
- Parenthetical grouping
- Multi-operator expressions
- Recipe documentation

---

### Journey Requirements Summary

| Journey | Primary Operators | Capability Areas |
|---------|------------------|------------------|
| Alex (Artist) | `%`, `#` | Interpolation, seed control |
| Sam (Professional) | `@` | Temporal scheduling |
| Jordan (Explorer) | `??`, `!!`, `X` | Exploration, chaos, breeding |
| Dev (Power User) | All + chaining | Complex expressions |

---

## Innovation & Novel Patterns

### Detected Innovation Areas

**1. DSL for Latent Space Operations**

z-Explorer creates a new category: a Domain Specific Language for prompt manipulation. While individual operations exist in code form, no tool offers this level of expressiveness through simple syntax.

**Innovation Signals:**
- "New paradigm" — Rethinking prompt input as a programming interface
- "DSL creation" — Novel syntax for existing operations

**2. Denoising-Level Control via Syntax**

The `@` temporal scheduling operator exposes denoising step control through syntax. This is typically only available through node-based tools or custom code.

**3. Latent Arithmetic Made Accessible**

Operations like `king - man + woman` bring Word2Vec-style arithmetic to image generation through intuitive syntax.

### Validation Approach

1. **Proof of Concept**: Implement `%` and `|` first to validate the parser architecture
2. **User Testing**: Alpha test with 5-10 power users for syntax feedback
3. **Iteration**: Refine syntax based on "what would you expect this to do?" sessions

### Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Parser complexity | Start with simple recursive descent, expand incrementally |
| Latent operations don't work as expected | Validate each operator in isolation before integration |
| Syntax conflicts with prompts | Use operators unlikely to appear in natural text |
| User confusion | Extensive examples and clear error messages |

---

## Developer Tool Specific Requirements

### Project-Type Overview

As a **developer tool** creating a DSL, the Prompt Operators System requires:

1. **Clear Language Specification**: Formal grammar for the operator syntax
2. **Robust Parsing**: Handle edge cases, provide helpful errors
3. **Documentation & Examples**: Code samples, recipes, tutorials
4. **Extensibility**: Architecture that allows adding new operators

### Technical Architecture Considerations

**Parser Design:**
- Tokenizer separates operators from prompt text
- Recursive descent parser handles nesting and grouping
- AST (Abstract Syntax Tree) representation for execution
- Error recovery for helpful diagnostics

**Integration Points:**
- Hooks into existing `llm_provider.py` for prompt processing
- Interfaces with `image_generator.py` for generation control
- Uses diffusers `callback_on_step_end` for temporal operations

**API Surface:**
- `parse_prompt(text: str) -> PromptAST`
- `execute_operators(ast: PromptAST, generator: ImageGenerator) -> List[Image]`
- `validate_syntax(text: str) -> ValidationResult`

### Language Design Requirements

| Requirement | Specification |
|-------------|--------------|
| Operator precedence | Defined order (e.g., `*` before `+`) |
| Parenthetical grouping | Support `(a + b) % c` |
| Error messages | Point to exact location of syntax errors |
| Escape sequences | Allow literal `%` via `\%` if needed |

---

## Functional Requirements

### Prompt Parsing

- **FR1**: System can parse prompts containing single-character operators (`%`, `|`, `+`, `-`, `*`, `@`, `#`, `?`, `!`, `~`, `X`)
- **FR2**: System can parse prompts containing multi-character operators (`::`, `->`, `??`, `@@`, `!!`, `=>`)
- **FR3**: System can parse operator parameters (e.g., `: 10`, `: 0.7`, `@0-50%`)
- **FR4**: System can parse parenthetical groupings for operator precedence
- **FR5**: System can parse chained operators in a single prompt
- **FR6**: System provides clear error messages with location for invalid syntax

### Latent Operations

- **FR7**: Users can interpolate between two prompts with specified steps (`%` operator)
- **FR8**: Users can blend two prompts with specified ratio (`+` operator)
- **FR9**: Users can subtract concepts from prompts (`-` operator)
- **FR10**: Users can amplify prompt emphasis (`*` operator)
- **FR11**: Users can add variation noise to prompts (`?` operator)
- **FR12**: Users can negate concepts as strong negative guidance (`!` operator)

### Temporal Operations

- **FR13**: Users can schedule prompts for specific denoising step ranges (`@` operator)
- **FR14**: Users can alternate prompts during denoising (`|` operator)
- **FR15**: System respects step ranges specified as percentages or absolute values

### Generation Control

- **FR16**: Users can specify seed for reproducible generation (`#` operator)
- **FR17**: Users can create eased interpolation with curve control (`~` operator)
- **FR18**: Users can generate maximally diverse variations (`??` operator)
- **FR19**: Users can inject controlled chaos/glitch effects (`!!` operator)

### Advanced Operations

- **FR20**: Users can perform genetic crossover between concepts (`X` operator)
- **FR21**: Users can apply style transfer via content/style separation (`::` operator)
- **FR22**: Users can create 2D grids exploring two parameter axes (`@@` operator)
- **FR23**: Users can push prompts in semantic directions (`->` operator)

### Integration

- **FR24**: Operators integrate with existing variable system (`__variable__`)
- **FR25**: Operators integrate with existing enhancement operator (`>`)
- **FR26**: Operators integrate with planned LoRA syntax
- **FR27**: System generates multiple images for multi-output operators (interpolation, grids)

### Output & Feedback

- **FR28**: System displays real-time progress for multi-image operations
- **FR29**: System provides visual preview of interpolation/grid layouts
- **FR30**: System allows saving and loading operator "recipes"

---

## Non-Functional Requirements

### Performance

| Requirement | Target | Rationale |
|-------------|--------|-----------|
| **Parsing Speed** | <100ms for complex prompts | User shouldn't notice parsing overhead |
| **Memory Overhead** | <50MB for parser/AST | Minimal impact on VRAM-constrained systems |
| **Operator Execution** | No additional latency per step | Operations happen within existing pipeline |

### Reliability

| Requirement | Target | Rationale |
|-------------|--------|-----------|
| **Parser Accuracy** | 99.9% correct parsing | Users trust their prompts work as written |
| **Graceful Degradation** | Fallback to raw prompt on error | Never block generation entirely |
| **Error Recovery** | Identify multiple errors in one pass | Efficient user correction |

### Usability

| Requirement | Target | Rationale |
|-------------|--------|-----------|
| **Learnability** | First operator success in <5 minutes | Low barrier to adoption |
| **Documentation** | Complete operator reference + examples | Self-serve learning |
| **Error Messages** | Point to exact character position | Easy debugging |

### Extensibility

| Requirement | Target | Rationale |
|-------------|--------|-----------|
| **New Operators** | Add operator in <1 day | Room for growth |
| **Plugin Architecture** | Support user-defined operators (future) | Community extensions |

---

## Technical Constraints

### Existing Architecture Integration

The Prompt Operators System must integrate with z-Explorer's existing architecture:

| Component | Integration Point |
|-----------|------------------|
| `llm_provider.py` | Prompt processing before enhancement |
| `image_generator.py` | Generation control and callbacks |
| `cli.py` | Command-line prompt input |
| `server.py` | API endpoint for operator validation |
| GUI (`FakeCLI.svelte`) | Operator syntax highlighting (future) |

### HuggingFace Stack Leverage

**diffusers:**
- `callback_on_step_end` for temporal operators
- `prompt_embeds` for pre-encoded blending
- `generator` for seed control

**transformers:**
- Text encoder for prompt embedding
- Embedding manipulation for blend/subtract

**peft:**
- LoRA integration for style operators (future)

### Memory Constraints

z-Explorer's two-phase pipeline (LLM then Image) means:
- All prompt parsing happens before image model loads
- Embeddings can be computed during LLM phase
- No additional VRAM during image generation

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Parser complexity exceeds estimate | Medium | Schedule slip | Start minimal, expand incrementally |
| Latent operations produce poor results | Low | User disappointment | Validate each operator thoroughly |
| Syntax conflicts with natural prompts | Low | User confusion | Choose unlikely operator characters |
| Performance degradation | Low | UX impact | Profile early and often |
| User adoption resistance | Medium | Feature failure | Extensive documentation and examples |

---

## Appendix: Operator Quick Reference

### Phase 1 (MVP)

| Operator | Syntax | Example | Output |
|----------|--------|---------|--------|
| `#` | `prompt #seed` | `cat #123` | Single image with seed |
| `+` | `a + b : ratio` | `cat + dog : 0.6` | Single blended image |
| `-` | `a - b` | `cat - stripes` | Single subtracted image |
| `*` | `a * n` | `fluffy * 2` | Single emphasized image |
| `!` | `!concept` | `!blur` | Strong negative |
| `?` | `a ? amount` | `cat ? 0.2` | Single varied image |
| `%` | `a % b : n` | `cat % dog : 10` | N interpolated images |
| `\|` | `a \| b` | `cat \| airplane` | Single hybrid image |
| `@` | `a @range` | `cat @0-50%` | Scheduled prompt |
| `~` | `a ~ b : n` | `cat ~ dog : 10` | N eased images |

### Phase 2 (Power)

| Operator | Syntax | Example | Output |
|----------|--------|---------|--------|
| `X` | `a X b` | `cat X robot` | Single crossover image |
| `::` | `content :: style` | `cat :: anime` | Single styled image |
| `??` | `a ?? n` | `cat ?? 20` | N diverse images |
| `@@` | `a @@ b : NxM` | `cat @@ dog : 5x5` | NxM grid image |
| `!!` | `a !! amount` | `cat !! 0.3` | Single glitched image |

---

## Document Metadata

**PRD Status:** Complete
**Generated Via:** BMad Method PRD Workflow
**Workflow Completion:** 2025-12-03

**Next Recommended Steps:**
1. Architecture Design — Define parser and execution architecture
2. Epic Creation — Break FRs into implementable stories
3. Phase 1 Implementation — Ship MVP operators

---

*This PRD serves as the capability contract for the z-Explorer Prompt Operators System. All design, architecture, and development work should trace back to requirements documented here.*
