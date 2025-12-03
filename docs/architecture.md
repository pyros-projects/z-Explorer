---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments:
  - docs/prd.md
  - docs/index.md
  - docs/architecture-backend.md
  - docs/architecture-gui.md
  - docs/integration-architecture.md
  - docs/analysis/prompt-operators-brief.md
workflowType: 'architecture'
lastStep: 8
status: 'complete'
completedAt: '2025-12-03'
project_name: 'z-Explorer'
user_name: 'Andre'
date: '2025-12-03'
---

# Architecture Decision Document - Prompt Operators System

**Project:** z-Explorer
**Feature:** Prompt Operators System
**Author:** Andre
**Date:** 2025-12-03
**Status:** Ready for Implementation

---

## Project Context Analysis

### Brownfield Project Context

This architecture extends an **existing, well-documented codebase**. z-Explorer is a multi-part monolith:

| Part | Technology | Root | Entry Points |
|------|------------|------|--------------|
| **Backend** | Python 3.12, FastAPI, PyTorch, Diffusers | `src/z_explorer/` | `cli.py`, `server.py`, `core/generator.py` |
| **GUI** | Svelte 4, TypeScript 5.3, Vite 5 | `src/z_explorer/gui/` | `main.ts`, `App.svelte` |

### Existing Patterns to Follow

The codebase has established patterns we MUST maintain:

**Python Backend:**
- `uv` for package management
- FastAPI for REST API with SSE streaming
- Two-phase generation pipeline (LLM → Image)
- `core/generator.py` as single source of truth for generation

**GUI:**
- Svelte stores for state management
- SSE connection for real-time progress
- FakeCLI component for terminal-style input

### Requirements Overview

**Functional Requirements:** 30 FRs organized into:
- Prompt Parsing (FR1-6)
- Latent Operations (FR7-12)
- Temporal Operations (FR13-15)
- Generation Control (FR16-19)
- Advanced Operations (FR20-23)
- Integration (FR24-27)
- Output & Feedback (FR28-30)

**Non-Functional Requirements:**
- Parsing speed: <100ms for complex prompts
- Memory overhead: <50MB for parser/AST
- Parser accuracy: 99.9% correct parsing
- Graceful degradation: Fallback to raw prompt on error

### Scale & Complexity

| Dimension | Assessment |
|-----------|------------|
| **Primary Domain** | Developer Tool (DSL creation) |
| **Complexity Level** | Medium |
| **Integration Points** | 4 (llm_provider, image_generator, cli, server) |
| **New Components** | 3 (parser, operator_executor, operator_registry) |

### Technical Constraints

- **Memory**: LLM and Image model cannot coexist in VRAM
- **Two-Phase Pipeline**: All operator parsing/embedding happens in Phase 1 (LLM)
- **Existing APIs**: Must use `callback_on_step_end` from diffusers for temporal ops
- **Python Version**: 3.12+

---

## Starter Template Evaluation

### NOT APPLICABLE — Brownfield Project

This is an **existing project** with established structure. We are **extending**, not creating from scratch.

**Existing Tech Stack (Locked In):**
- Python 3.12 + `uv` package manager
- FastAPI + Uvicorn
- PyTorch + HuggingFace Diffusers/Transformers/PEFT
- Svelte 4 + TypeScript + Vite

**What We're Adding:**
- Prompt parsing module (`src/z_explorer/core/operators/`)
- Operator execution logic integrated into `generator.py`
- API endpoints for operator validation

---

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
1. Parser architecture and syntax handling
2. Integration points with existing pipeline
3. Embedding manipulation strategy

**Important Decisions (Shape Architecture):**
4. Operator registry pattern
5. Error handling strategy
6. Multi-output handling (interpolation, grids)

**Deferred Decisions (Post-MVP):**
7. GUI syntax highlighting
8. Recipe saving/loading format
9. Plugin architecture for user-defined operators

---

### Parser Architecture

**Decision:** Recursive Descent Parser with Tokenizer

**Rationale:**
- Simple, maintainable, easy to extend
- Good error messages with location tracking
- No external dependencies required
- Well-suited for DSL parsing

**Components:**

```
PromptInput → Tokenizer → TokenStream → Parser → OperatorAST → Executor
```

| Component | Responsibility |
|-----------|---------------|
| `Tokenizer` | Convert raw prompt to token stream |
| `Parser` | Build AST from tokens using recursive descent |
| `OperatorAST` | Tree representation of operators and operands |
| `Executor` | Walk AST, apply operators, produce embeddings/callbacks |

**Token Types:**
```python
class TokenType(Enum):
    TEXT = "TEXT"           # Regular prompt text
    OPERATOR = "OPERATOR"   # %, |, +, -, *, @, #, ?, !, ~, X
    MULTI_OP = "MULTI_OP"   # ::, ->, ??, @@, !!, =>
    NUMBER = "NUMBER"       # Numeric parameters
    COLON = "COLON"         # Parameter separator
    LPAREN = "LPAREN"       # (
    RPAREN = "RPAREN"       # )
    PERCENT = "PERCENT"     # % in ranges like @0-50%
    DASH = "DASH"           # - in ranges like @0-50%
    EOF = "EOF"
```

---

### Operator Precedence

**Decision:** Explicit precedence with parenthetical override

| Precedence | Operators | Description |
|------------|-----------|-------------|
| 1 (highest) | `*` | Emphasis |
| 2 | `!` | Negation |
| 3 | `+`, `-` | Blend, Subtract |
| 4 | `%`, `~` | Interpolation |
| 5 | `\|` | Alternating |
| 6 | `@` | Temporal scheduling |
| 7 | `#` | Seed control |
| 8 | `::`, `->` | Style, Direction |
| 9 (lowest) | `??`, `@@`, `!!` | Exploration operators |

**Parentheses:** Override precedence: `(cat + dog) % airplane`

---

### Integration with Existing Pipeline

**Decision:** Hook into Phase 1 (LLM phase) for parsing and embedding prep

**Integration Points:**

```
┌─────────────────────────────────────────────────────────────┐
│                     PHASE 1: LLM                             │
├─────────────────────────────────────────────────────────────┤
│  1. User Input                                               │
│         ↓                                                    │
│  2. Variable Substitution (__animal__ → cat)                │
│         ↓                                                    │
│  3. ★ OPERATOR PARSING ★  ← NEW                             │
│         ↓                                                    │
│  4. Enhancement (> operator) via LLM                         │
│         ↓                                                    │
│  5. ★ EMBEDDING PREPARATION ★  ← NEW                        │
│         ↓                                                    │
│  6. Unload LLM                                               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                     PHASE 2: IMAGE                           │
├─────────────────────────────────────────────────────────────┤
│  7. Load Image Model                                         │
│         ↓                                                    │
│  8. ★ EXECUTE OPERATORS ★  ← NEW                            │
│     - Apply pre-computed embeddings                          │
│     - Use callbacks for temporal operators                   │
│     - Generate single or multiple images                     │
│         ↓                                                    │
│  9. Output Images                                            │
└─────────────────────────────────────────────────────────────┘
```

**Key Files Modified:**

| File | Changes |
|------|---------|
| `core/generator.py` | Import operator module, call parser, handle multi-output |
| `llm_provider.py` | Add embedding extraction method |
| `image_generator.py` | Add callback support for temporal operators |
| `server.py` | Add `/api/operators/validate` endpoint |
| `cli.py` | No changes needed (prompts flow through generator) |

---

### Embedding Manipulation Strategy

**Decision:** Use HuggingFace transformers for embedding extraction, torch for manipulation

**API Surface:**

```python
# Embedding extraction
def get_prompt_embedding(prompt: str) -> torch.Tensor:
    """Extract text embedding using CLIP/T5 encoder."""

# Embedding operations
def blend_embeddings(a: Tensor, b: Tensor, ratio: float) -> Tensor:
    """Weighted blend: a * ratio + b * (1 - ratio)"""

def subtract_embeddings(a: Tensor, b: Tensor, strength: float) -> Tensor:
    """Subtract: a - b * strength"""

def interpolate_embeddings(a: Tensor, b: Tensor, steps: int) -> List[Tensor]:
    """Generate N embeddings walking from a to b."""
```

**Memory Management:**
- Embeddings computed during Phase 1 while LLM is loaded
- Stored as tensors in generation context
- Applied during Phase 2 via `prompt_embeds` parameter

---

### Temporal Operator Execution

**Decision:** Use diffusers `callback_on_step_end` for step-level control

**Callback Pattern:**

```python
def create_temporal_callback(schedule: TemporalSchedule):
    """Create callback for @, | operators."""

    def callback(pipe, step, timestep, callback_kwargs):
        # Determine which prompt applies at this step
        active_prompt = schedule.get_prompt_for_step(step, total_steps)
        callback_kwargs["prompt_embeds"] = active_prompt.embedding
        return callback_kwargs

    return callback
```

**Temporal Schedule Types:**

| Operator | Schedule Type | Example |
|----------|--------------|---------|
| `@` | Range-based | `cat @0-50% dog @50-100%` |
| `\|` | Alternating | `cat \| dog` → step 0: cat, step 1: dog, ... |

---

### Multi-Output Handling

**Decision:** Operators that produce multiple images return a list

**Multi-Output Operators:**

| Operator | Output Count | Pattern |
|----------|--------------|---------|
| `%` | N (specified) | `a % b : 10` → 10 images |
| `~` | N (specified) | `a ~ b : 10` → 10 images |
| `??` | N (specified) | `a ?? 20` → 20 diverse images |
| `@@` | N×M (grid) | `a @@ b : 5x5` → 25 images |

**Generator Return Type:**

```python
@dataclass
class GenerationResult:
    images: List[Image]           # 1 or more images
    seeds: List[int]              # Corresponding seeds
    operator_metadata: Optional[Dict]  # For interpolation: step indices, etc.
```

---

### Error Handling Strategy

**Decision:** Graceful degradation with informative errors

**Error Levels:**

| Level | Behavior | Example |
|-------|----------|---------|
| **Parse Error** | Return error, don't generate | `cat % (missing operand)` |
| **Execution Warning** | Generate with warning | `cat * 100` (excessive emphasis) |
| **Fallback** | Use raw prompt | Operator unsupported by model |

**Error Message Format:**

```python
@dataclass
class OperatorError:
    message: str
    position: int        # Character position in prompt
    length: int          # Length of problematic token
    suggestion: str      # How to fix
```

---

## Implementation Patterns & Consistency Rules

### Naming Patterns

**Python Module Naming:**
- Lowercase with underscores: `operator_parser.py`, `embedding_ops.py`
- Classes: PascalCase: `OperatorParser`, `TemporalSchedule`
- Functions: snake_case: `parse_prompt`, `blend_embeddings`

**Operator Registry:**
```python
# Operators registered by symbol
OPERATORS = {
    "%": InterpolationOperator,
    "|": AlternatingOperator,
    "+": BlendOperator,
    # ...
}
```

**File Naming in operators/ module:**
```
operators/
├── __init__.py          # Exports parse_prompt, execute_operators
├── parser.py            # Tokenizer + Parser
├── ast.py               # AST node definitions
├── executor.py          # AST execution logic
├── registry.py          # Operator registration
├── embeddings.py        # Embedding manipulation utilities
├── temporal.py          # Temporal operator callbacks
└── operators/           # Individual operator implementations
    ├── __init__.py
    ├── interpolation.py # % operator
    ├── alternating.py   # | operator
    ├── blend.py         # + operator
    ├── subtract.py      # - operator
    ├── emphasis.py      # * operator
    ├── temporal.py      # @ operator
    ├── seed.py          # # operator
    ├── variation.py     # ? operator
    ├── negation.py      # ! operator
    └── smooth.py        # ~ operator
```

### Code Patterns

**Operator Base Class:**
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class OperatorResult:
    embeddings: List[torch.Tensor]
    callbacks: List[Callable]
    output_count: int

class BaseOperator(ABC):
    symbol: str

    @abstractmethod
    def execute(
        self,
        left: OperatorResult,
        right: Optional[OperatorResult],
        params: Dict[str, Any]
    ) -> OperatorResult:
        """Execute the operator and return result."""
        pass

    @abstractmethod
    def validate(
        self,
        left: Any,
        right: Optional[Any],
        params: Dict[str, Any]
    ) -> Optional[str]:
        """Validate operands. Return error message or None."""
        pass
```

**AST Node Pattern:**
```python
@dataclass
class ASTNode:
    pass

@dataclass
class TextNode(ASTNode):
    text: str

@dataclass
class BinaryOpNode(ASTNode):
    operator: str
    left: ASTNode
    right: ASTNode
    params: Dict[str, Any]

@dataclass
class UnaryOpNode(ASTNode):
    operator: str
    operand: ASTNode
    params: Dict[str, Any]
```

### Testing Patterns

**Test Location:** `tests/test_operators/`

**Test Structure:**
```
tests/
└── test_operators/
    ├── __init__.py
    ├── test_parser.py       # Parser unit tests
    ├── test_executor.py     # Executor unit tests
    ├── test_embeddings.py   # Embedding ops unit tests
    ├── test_integration.py  # Full pipeline integration
    └── fixtures/
        └── prompts.py       # Test prompt fixtures
```

**Test Pattern:**
```python
def test_interpolation_operator():
    """Test % operator parses and executes correctly."""
    result = parse_prompt("cat % dog : 5")
    assert isinstance(result.ast, BinaryOpNode)
    assert result.ast.operator == "%"
    assert result.ast.params["steps"] == 5
```

---

## Project Structure & Boundaries

### New Files to Create

```
src/z_explorer/
├── core/
│   ├── generator.py          # MODIFY: Add operator integration
│   └── operators/             # NEW: Operator module
│       ├── __init__.py
│       ├── parser.py
│       ├── ast.py
│       ├── executor.py
│       ├── registry.py
│       ├── embeddings.py
│       ├── temporal.py
│       └── operators/
│           ├── __init__.py
│           ├── interpolation.py
│           ├── alternating.py
│           ├── blend.py
│           ├── subtract.py
│           ├── emphasis.py
│           ├── temporal.py
│           ├── seed.py
│           ├── variation.py
│           ├── negation.py
│           └── smooth.py
├── image_generator.py        # MODIFY: Add callback support
├── llm_provider.py           # MODIFY: Add embedding extraction
└── server.py                 # MODIFY: Add validation endpoint

tests/
└── test_operators/           # NEW: Operator tests
    ├── __init__.py
    ├── test_parser.py
    ├── test_executor.py
    ├── test_embeddings.py
    ├── test_integration.py
    └── fixtures/
        └── prompts.py
```

### Component Boundaries

**Operator Module Boundary:**
- **Owns:** Parsing, AST, operator execution
- **Exports:** `parse_prompt()`, `execute_operators()`, `validate_syntax()`
- **Imports:** torch, transformers (for embeddings)
- **Does NOT:** Load models, manage VRAM, handle I/O

**Generator Boundary:**
- **Owns:** Pipeline orchestration, VRAM management
- **Calls:** `operators.parse_prompt()`, `operators.execute_operators()`
- **Provides:** Model instances to operators when needed

**Image Generator Boundary:**
- **Owns:** Diffusion pipeline execution
- **Accepts:** Pre-computed embeddings, step callbacks
- **Provides:** `callback_on_step_end` support

### Data Flow

```
User Prompt
    ↓
[generator.py] - Orchestration
    ↓
[operators/parser.py] - Parse to AST
    ↓
[operators/executor.py] - Pre-compute what we can
    ↓
[llm_provider.py] - Extract embeddings (Phase 1)
    ↓
← LLM Unloaded →
    ↓
[image_generator.py] - Generate with embeddings/callbacks (Phase 2)
    ↓
[operators/executor.py] - Apply temporal operators via callbacks
    ↓
Generated Images
```

---

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
- Parser architecture aligns with Python ecosystem
- Embedding strategy uses existing HuggingFace APIs
- Temporal callbacks use standard diffusers patterns
- All decisions compatible with existing z-Explorer architecture

**Pattern Consistency:**
- Naming follows existing z-Explorer patterns (snake_case, etc.)
- Module organization follows existing `core/` structure
- Test organization follows existing `tests/` patterns

**Structure Alignment:**
- New `operators/` module fits naturally in `core/`
- Minimal modifications to existing files
- Clear separation of concerns

### Requirements Coverage Validation ✅

| FR Category | Coverage | Notes |
|-------------|----------|-------|
| Prompt Parsing (FR1-6) | ✅ Full | Parser + AST architecture |
| Latent Operations (FR7-12) | ✅ Full | Embedding manipulation utilities |
| Temporal Operations (FR13-15) | ✅ Full | Callback-based execution |
| Generation Control (FR16-19) | ✅ Full | Executor + multi-output handling |
| Advanced Operations (FR20-23) | ✅ Full | Individual operator implementations |
| Integration (FR24-27) | ✅ Full | Integration points defined |
| Output & Feedback (FR28-30) | ✅ Full | GenerationResult + SSE streaming |

**Non-Functional Requirements:**
- Performance: Parser is simple, <100ms easily achievable
- Memory: Tensors only, no heavy objects, <50MB
- Reliability: Error handling with graceful degradation
- Extensibility: Registry pattern for new operators

### Implementation Readiness Validation ✅

**Decision Completeness:**
- All critical decisions documented
- Technology choices clear (Python, torch, diffusers)
- Implementation patterns comprehensive
- Examples provided for all major patterns

**Structure Completeness:**
- All files and directories defined
- Integration points clearly specified
- Component boundaries well-defined

**Pattern Completeness:**
- Naming conventions documented
- Code patterns with examples
- Testing patterns specified

---

## Architecture Completion Summary

### Workflow Completion

**Architecture Decision Workflow:** COMPLETED ✅
**Total Steps Completed:** 8
**Date Completed:** 2025-12-03
**Document Location:** `docs/architecture.md`

### Final Architecture Deliverables

**Complete Architecture Document:**
- Parser architecture with tokenizer and recursive descent
- Operator precedence and grouping rules
- Integration with existing two-phase pipeline
- Embedding manipulation strategies
- Temporal operator execution via callbacks
- Multi-output handling for interpolation/grids
- Error handling with graceful degradation

**Implementation Ready Foundation:**
- 15+ architectural decisions made
- 10+ implementation patterns defined
- 3 new components specified (parser, executor, registry)
- 30 functional requirements fully supported

### Implementation Handoff

**For AI Agents:**
This architecture document is your complete guide for implementing the Prompt Operators System. Follow all decisions, patterns, and structures exactly as documented.

**First Implementation Priority:**
1. Create `src/z_explorer/core/operators/` module structure
2. Implement tokenizer and parser
3. Add basic operator execution for `#` (seed) and `+` (blend)
4. Integrate with `generator.py`
5. Add tests

**Development Sequence:**
1. Parser + AST (no model dependencies)
2. Embedding utilities (needs text encoder)
3. Simple operators (`#`, `+`, `-`, `*`, `!`, `?`)
4. Complex operators (`%`, `|`, `@`, `~`)
5. Advanced operators (`X`, `::`, `??`, `@@`, `!!`)

### Quality Assurance Checklist

**✅ Architecture Coherence**
- [x] All decisions work together without conflicts
- [x] Technology choices are compatible
- [x] Patterns support the architectural decisions
- [x] Structure aligns with existing codebase

**✅ Requirements Coverage**
- [x] All 30 functional requirements supported
- [x] All non-functional requirements addressed
- [x] Cross-cutting concerns handled
- [x] Integration points defined

**✅ Implementation Readiness**
- [x] Decisions are specific and actionable
- [x] Patterns prevent agent conflicts
- [x] Structure is complete and unambiguous
- [x] Examples provided for clarity

---

**Architecture Status:** READY FOR IMPLEMENTATION ✅

**Next Phase:** Create epics and stories for implementation

**Document Maintenance:** Update this architecture when major technical decisions are made during implementation.
