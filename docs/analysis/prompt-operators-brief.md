# z-Explorer Prompt Operators Reference Brief

**Generated:** 2025-12-02
**Purpose:** Detailed description of each proposed prompt manipulation operator
**Design Principle:** "Wild shit with elegant syntax" - Maximum power, minimum effort

---

## Table of Contents

1. [Core Single-Character Operators](#1-core-single-character-operators)
2. [Multi-Character Operators](#2-multi-character-operators)
3. [Function-Style Operators](#3-function-style-operators)
4. [Advanced Concepts](#4-advanced-concepts)

---

# 1. Core Single-Character Operators

## 1.1 `%` — Latent Interpolation (Walk)

**Syntax:** `prompt_a % prompt_b : steps`

**What it does:**
Takes two prompts, finds their positions in the model's latent space, and generates images at evenly-spaced points along the line connecting them. Think of it as "walking" from one concept to another through the AI's imagination.

**How it works technically:**
1. Encode `prompt_a` → get latent vector A
2. Encode `prompt_b` → get latent vector B
3. For each step i from 0 to N:
   - Calculate interpolated vector: `V = A + (B - A) * (i / N)`
   - Generate image from V

**Examples:**
```
cat % airplane : 10
→ Generates 10 images walking from "cat" to "airplane"
→ Image 1: Pure cat
→ Image 5: Weird cat-airplane hybrid
→ Image 10: Pure airplane

realistic photo % oil painting : 5
→ Style interpolation in 5 steps

happy face % sad face : 20
→ Emotional transition animation
```

**Use cases:**
- Exploring what's "between" two concepts
- Creating morph animations
- Finding interesting hybrid concepts
- Understanding how the model sees relationships

**Variations:**
- `a % b % c : 20` — Multi-point interpolation (walk A→B→C)
- `a % b : 10,ease` — Eased interpolation (slow at ends)

---

## 1.2 `|` — Alternating Prompt (Denoising Swap)

**Syntax:** `prompt_a | prompt_b`

**What it does:**
During the denoising process (where the image goes from noise to final result), this alternates which prompt guides each step. Step 1 uses prompt A, step 2 uses prompt B, step 3 uses A again, etc. This creates a unique blending effect where both concepts influence the result but in a "flickering" way.

**How it works technically:**
1. Start with noise
2. For each denoising step:
   - If step is odd: use prompt_a as guidance
   - If step is even: use prompt_b as guidance
3. The result is a strange hybrid influenced by both

**Examples:**
```
cat | airplane
→ Alternates between cat and airplane guidance
→ Result: Something that has qualities of both

realistic | cartoon
→ Style tug-of-war
→ Result: Semi-realistic, semi-stylized

detailed | abstract
→ Detail level oscillation
```

**Use cases:**
- Creating unique hybrid aesthetics
- Blending incompatible concepts
- Experimental/artistic effects
- Finding unexpected combinations

**Variations:**
- `a | b | c` — Cycle through 3 prompts
- `a |2 b |3 c` — Custom step counts (2 steps of A, 3 of B, then C...)
- `a |! b` — Random alternation

---

## 1.3 `+` — Latent Blend (Weighted Average)

**Syntax:** `prompt_a + prompt_b` or `prompt_a + prompt_b : ratio`

**What it does:**
Combines two prompts by averaging their latent representations. Unlike `|` (which alternates), this creates a single blended concept that has qualities of both simultaneously. The ratio controls how much of each.

**How it works technically:**
1. Encode `prompt_a` → vector A
2. Encode `prompt_b` → vector B
3. Blend: `V = A * ratio + B * (1 - ratio)`
4. Generate from blended vector V

**Examples:**
```
cat + dog
→ Default 50/50 blend
→ Result: Something cat-like and dog-like simultaneously

cat + airplane : 0.8
→ 80% cat, 20% airplane
→ Result: Mostly cat with subtle airplane qualities

realistic + dreamy : 0.6
→ 60% realistic, 40% dreamy
```

**Use cases:**
- Precise concept mixing
- Style blending with control
- Creating "average" of multiple concepts
- Subtle influence injection

**Comparison to `|`:**
- `+` = simultaneous blend (smooth mix)
- `|` = temporal alternation (flickering mix)

---

## 1.4 `-` — Latent Subtraction (Concept Removal)

**Syntax:** `prompt_a - concept`

**What it does:**
Removes or reduces the influence of a concept from a prompt. This is like saying "give me A, but NOT B." It subtracts the latent representation of the unwanted concept.

**How it works technically:**
1. Encode `prompt_a` → vector A
2. Encode `concept` → vector B
3. Subtract: `V = A - (B * strength)`
4. Generate from V

**Examples:**
```
cat - stripes
→ A cat, but actively avoiding stripe patterns

photo - blur
→ Photo that pushes away from blurriness

happy person - smile
→ Happy but... not smiling? (weird but interesting)

realistic - artifacts
→ Realistic while avoiding common AI artifacts
```

**Use cases:**
- Removing unwanted elements
- Refining concepts
- Negative guidance with precision
- "Everything except..." queries

**Notes:**
- Different from negative prompts in that it operates in latent space directly
- Can create unexpected results when subtracting fundamental qualities

---

## 1.5 `*` — Emphasis (Amplification)

**Syntax:** `prompt * multiplier` or `(concept) * multiplier`

**What it does:**
Amplifies the influence of a prompt or concept by scaling its latent representation. This is like "turning up the volume" on a concept.

**How it works technically:**
1. Encode `prompt` → vector A
2. Scale: `V = A * multiplier`
3. Generate from amplified vector V

**Examples:**
```
cat * 2
→ VERY cat-like, exaggerated cat features

(fluffy) * 3
→ Extremely fluffy

realistic * 1.5
→ Extra realistic

a house with (windows) * 0.5
→ House with de-emphasized windows
```

**Use cases:**
- Emphasizing specific qualities
- Exaggerating features
- Fine-tuning concept strength
- Creating stylized/exaggerated versions

**Notes:**
- Values > 1 amplify, values < 1 reduce
- Similar to attention weights but operates on full concepts

---

## 1.6 `@` — Temporal Scheduling (Step-Based Control)

**Syntax:** `prompt @start-end` or `prompt @start-end%`

**What it does:**
Controls WHEN during the denoising process a prompt is active. Early steps define composition/structure, middle steps add details, late steps refine. This lets you use different prompts for different phases.

**How it works technically:**
1. Denoising has N total steps (e.g., 20)
2. `@0-10` means "use this prompt for steps 0-10"
3. `@50-100%` means "use this prompt for the last half"
4. Multiple scheduled prompts combine to guide different phases

**Examples:**
```
cat @0-50% airplane @50-100%
→ First half: guided by "cat" (defines structure)
→ Second half: guided by "airplane" (adds airplane details)
→ Result: Cat-shaped airplane? Airplane-textured cat?

detailed @0-30% abstract @30-70% refined @70-100%
→ Three-phase generation

composition:forest @0-20% subject:wolf @20-60% style:oil @60-100%
→ Layered control: composition, then subject, then style
```

**Use cases:**
- Controlling structure vs. details separately
- Progressive style application
- Complex multi-phase generation
- Precise artistic control

**Why it matters:**
Early denoising steps = broad structure, layout, composition
Late denoising steps = fine details, textures, refinement
This gives you control over WHAT gets influenced WHEN.

---

## 1.7 `#` — Seed Control (Deterministic Variation)

**Syntax:** `prompt #seed` or `prompt #seed1,seed2`

**What it does:**
Pins the random seed for reproducible results. The same prompt with the same seed always produces the same image. You can also reference multiple seeds for operations that need them.

**How it works technically:**
1. Sets the random number generator seed
2. All "random" operations become deterministic
3. Same seed + same prompt = identical result

**Examples:**
```
cat #123
→ Always produces the same cat image

cat #123 % airplane #456 : 10
→ Interpolate between specific cat and specific airplane

landscape #42
→ Reproducible landscape

"my prompt" #save:favorite
→ Save seed with a name for later reference
```

**Use cases:**
- Reproducing good results
- Consistent character/style across images
- Comparing variations with controlled changes
- Sharing exact generations

**Variations:**
- `#?` — Explicit random seed
- `#save:name` — Named seed storage
- `#load:name` — Recall saved seed

---

## 1.8 `?` — Variation (Noise Injection)

**Syntax:** `prompt ?` or `prompt ? amount`

**What it does:**
Adds controlled randomness/variation to the latent representation. Each generation will be slightly different, even with the same seed. It's like "wiggling" the concept in latent space.

**How it works technically:**
1. Encode `prompt` → vector A
2. Add noise: `V = A + random_noise * amount`
3. Generate from noisy vector V

**Examples:**
```
cat ?
→ Cat with random small variations each time

cat ? 0.3
→ 30% variation (noticeable but recognizable)

cat ? 0.8
→ 80% variation (wild departures from "cat")

portrait ? 0.1
→ Subtle variations for variety
```

**Use cases:**
- Generating diverse options
- Exploring "nearby" concepts
- Breaking repetition
- Creative accidents

**Comparison to `??`:**
- `?` = small noise injection
- `??` = active diversity exploration (see section 2.3)

---

## 1.9 `!` — Negation (Explicit NOT)

**Syntax:** `!concept` or `prompt !unwanted`

**What it does:**
Explicitly negates a concept, pushing the result away from it in latent space. Stronger and more precise than typical negative prompts.

**How it works technically:**
1. Encode `unwanted` → vector N
2. Use -N as negative guidance during generation
3. Result actively avoids the concept

**Examples:**
```
!realistic
→ Explicitly not realistic (tends toward artistic/stylized)

photo of cat !cartoon
→ Cat photo that avoids cartoon qualities

landscape !urban
→ Landscape avoiding any urban elements

portrait !smile
→ Portrait without smiling (for serious mood)
```

**Use cases:**
- Strong negative guidance
- Avoiding specific styles/elements
- "Anything but X" queries
- Cleaning up unwanted tendencies

**Notes:**
- More forceful than typical negative prompts
- Can be combined: `!blur !artifacts !watermark`

---

## 1.10 `~` — Smooth Transition (Eased Interpolation)

**Syntax:** `prompt_a ~ prompt_b` or `prompt_a ~curve prompt_b`

**What it does:**
Like `%` interpolation but with easing curves. Instead of linear interpolation, it accelerates/decelerates the transition for more natural or dramatic effects.

**How it works technically:**
1. Same as `%` but applies easing function to interpolation
2. `~ease` = slow start and end, fast middle
3. `~linear` = constant speed (same as `%`)
4. `~step` = sudden jump at midpoint

**Examples:**
```
cat ~ airplane : 10
→ Smooth eased transition (default ease curve)

cat ~linear airplane : 10
→ Linear (same as %)

cat ~step airplane : 10
→ Sudden switch in the middle

sad ~ease happy : 20
→ Emotional transition that lingers at extremes
```

**Available curves:**
- `~ease` — Slow-fast-slow (default)
- `~ease-in` — Slow start, fast end
- `~ease-out` — Fast start, slow end
- `~linear` — Constant rate
- `~step` — Hard switch at midpoint
- `~bounce` — Overshoot effect

**Use cases:**
- Cinematic transitions
- Natural-feeling morphs
- Dramatic reveals
- Animation keyframes

---

## 1.11 `X` — Breeding (Genetic Crossover)

**Syntax:** `prompt_a X prompt_b` or `#seed1 X #seed2`

**What it does:**
Combines two concepts or seeds using genetic algorithm-inspired crossover. Instead of simple averaging, it mixes "genes" (latent dimensions) from both parents to create unique offspring.

**How it works technically:**
1. Encode both prompts → vectors A and B
2. For each dimension, randomly choose from A or B
3. Result is a "child" with genes from both parents
4. Multiple offspring possible with different crossover patterns

**Examples:**
```
cat X airplane
→ Genetic mix: some features from cat, some from airplane
→ Different from cat + airplane (blend)

#123 X #456
→ Breed two seeds: combine their latent genetics

wolf X eagle
→ Mythical creature breeding

realistic X anime
→ Style breeding
```

**Use cases:**
- Creating unique hybrids
- Evolutionary exploration
- Unexpected combinations
- "What if these had a baby?"

**Comparison to `+`:**
- `+` = smooth blend of everything
- `X` = genetic mix of specific features

**Variations:**
- `a X b : 0.7` — 70% chance to pick from A for each gene
- `a X b X c` — Three-parent breeding

---

# 2. Multi-Character Operators

## 2.1 `::` — Style Transfer

**Syntax:** `content :: style`

**What it does:**
Applies the style/aesthetic of one concept to the content of another. It separates "what" from "how it looks" and combines them.

**How it works technically:**
1. Extract content features from left side
2. Extract style features from right side
3. Combine: content structure + style appearance
4. Generate result

**Examples:**
```
cat :: van gogh
→ A cat rendered in Van Gogh's style

photo of city :: cyberpunk
→ City photo with cyberpunk aesthetic

portrait :: anime
→ Portrait in anime style

landscape :: watercolor
→ Landscape as watercolor painting

my subject :: lora:style_v1:0.8
→ Subject with LoRA-defined style
```

**Use cases:**
- Artistic style application
- Consistent style across subjects
- Genre transformation
- "What would X look like as Y?"

**Notes:**
- Different from `+` which blends content too
- Preserves subject, changes rendering
- Can chain: `cat :: anime :: dark`

---

## 2.2 `->` — Direction Vector (Latent Push)

**Syntax:** `prompt -> direction` or `prompt <- direction`

**What it does:**
Pushes the result toward (or away from) a concept direction in latent space. Think of it as navigating with a compass - you're saying "go more in THIS direction."

**How it works technically:**
1. Encode `prompt` → vector A
2. Compute direction vector for `direction`
3. Push: `V = A + direction_vector * strength`
4. Generate from pushed vector

**Examples:**
```
face -> happy
→ Face pushed toward happiness

cat -> fluffy
→ Cat pushed toward fluffiness

portrait <- old
→ Portrait pushed AWAY from old (toward young)

landscape -> dramatic
→ Landscape with more drama

character -> detailed
→ More detailed version
```

**Use cases:**
- Fine-tuning specific qualities
- Artistic direction
- "More of this quality"
- Navigating concept space

**Pre-computed directions:**
Some directions could be pre-computed for common adjustments:
- `->age` (older/younger)
- `->detail` (more/less detailed)
- `->happy` (emotional)
- `->realistic` (realism level)

---

## 2.3 `??` — Exploration Mode (Diversity Generation)

**Syntax:** `prompt ?? count` or `prompt ?? count,diversity`

**What it does:**
Generates multiple diverse variations by actively exploring the space around a concept. Unlike `?` (simple noise), this uses algorithms to maximize diversity and coverage.

**How it works technically:**
1. Encode `prompt` → center vector A
2. Generate N diverse directions from A
3. Actively maximize distance between samples
4. Generate image from each diverse position

**Examples:**
```
cat ?? 10
→ 10 maximally diverse cat variations

portrait ?? 5,high
→ 5 portraits with high diversity

logo concept ?? 20
→ 20 diverse logo explorations

character design ?? 8
→ 8 different character interpretations
```

**Use cases:**
- Brainstorming/ideation
- Exploring design space
- Finding unexpected interpretations
- Client presentations

**Diversity levels:**
- `low` — Subtle variations
- `medium` — Noticeable differences (default)
- `high` — Wild departures
- `extreme` — Maximum diversity

---

## 2.4 `@@` — Grid Exploration (2D Latent Map)

**Syntax:** `a @@ b` or `a @@ b : NxM`

**What it does:**
Creates a 2D grid of images by interpolating between concepts on two axes. This maps out a region of latent space visually.

**How it works technically:**
1. Define 4 corners (or 2 axes)
2. Interpolate across both X and Y axes
3. Generate image at each grid point
4. Output as grid image or individual files

**Examples:**
```
cat @@ dog : 5x5
→ 5x5 grid from cat to dog (single axis, both ends)

cat @@ dog x realistic @@ cartoon : 4x4
→ 4x4 grid with:
  - X axis: cat → dog
  - Y axis: realistic → cartoon
  - Corners: realistic cat, cartoon cat, realistic dog, cartoon dog

happy @@ sad x detailed @@ simple : 3x3
→ 9 images mapping emotion vs detail level
```

**Use cases:**
- Visualizing latent space regions
- Parameter exploration
- Understanding model behavior
- Creating style guides

**Output:**
- Single grid image
- Individual images with coordinates
- Interactive explorer (future)

---

## 2.5 `!!` — Chaos/Glitch Injection

**Syntax:** `prompt !!` or `prompt !! amount`

**What it does:**
Injects controlled chaos or glitch artifacts into the generation. Unlike `?` (smooth noise), this creates sudden breaks, artifacts, and unexpected disruptions.

**How it works technically:**
1. During generation, randomly corrupt parts of the latent
2. Introduce discontinuities
3. Partially scramble guidance
4. Create "broken" but artistic effects

**Examples:**
```
portrait !!
→ Glitchy portrait with artifacts

landscape !! 0.3
→ 30% chaos injection

photo !! 0.1
→ Subtle glitch aesthetic

a !! b
→ Glitchy transition between concepts
```

**Use cases:**
- Glitch art aesthetic
- Datamosh effects
- Experimental visuals
- Breaking conventional outputs

**Levels:**
- `0.1` — Subtle artifacts
- `0.3` — Noticeable glitches
- `0.5` — Heavy corruption
- `0.8+` — Maximum chaos

---

## 2.6 `=>` — Semantic Gradient

**Syntax:** `concept_a => concept_b : steps`

**What it does:**
Creates a gradient along a semantic dimension. Different from interpolation (`%`) in that it follows the conceptual meaning rather than the direct latent path.

**How it works technically:**
1. Identify the semantic dimension between A and B
2. Sample along that dimension (not direct line)
3. Follow conceptual meaning
4. Generate at each sample point

**Examples:**
```
small => big : 10
→ Size progression from small to big

simple => complex : 8
→ Complexity gradient

calm => chaotic : 12
→ Energy level progression

minimalist => ornate : 6
→ Style detail progression
```

**Use cases:**
- Exploring semantic dimensions
- Creating progressions
- Understanding concept relationships
- Controlled attribute manipulation

**Comparison to `%`:**
- `%` = direct latent line (shortest path)
- `=>` = semantic path (meaningful progression)

---

# 3. Function-Style Operators

## 3.1 `walk(a, b, steps)` — Latent Walk

**Syntax:** `walk(prompt_a, prompt_b, steps)`

**What it does:**
Explicit function for latent space walk between two points. Functionally similar to `%` but with clearer syntax for complex operations.

**Examples:**
```
walk(cat, airplane, 10)
→ Same as "cat % airplane : 10"

walk(happy, sad, 20, ease)
→ Eased walk with curve

walk(a, b, c, d, 30)
→ Multi-point walk through 4 concepts
```

**Use cases:**
- Complex walks
- When clarity is preferred over brevity
- Chaining with other functions

---

## 3.2 `orbit(center, count, radius)` — Orbital Variations

**Syntax:** `orbit(prompt, count)` or `orbit(prompt, count, radius)`

**What it does:**
Generates variations that "orbit" around a central concept. All outputs are equidistant from the center, exploring the "surface" of a sphere in latent space.

**How it works technically:**
1. Encode `prompt` → center vector
2. Generate N points on sphere surface around center
3. Radius controls how far from center
4. Generate image from each orbit point

**Examples:**
```
orbit(cat, 10)
→ 10 cat variations arranged in orbit

orbit(portrait, 8, 0.3)
→ 8 portraits at 0.3 radius

orbit(logo, 20, 0.5)
→ 20 logo variations for exploration
```

**Use cases:**
- Exploring concept boundaries
- Systematic variation generation
- Finding the edges of a concept
- Diverse but related outputs

---

## 3.3 `mutate(prompt, rate)` — Genetic Mutation

**Syntax:** `mutate(prompt, mutation_rate)`

**What it does:**
Applies random mutations to the latent representation, like genetic mutations. Higher rates = more dramatic changes.

**How it works technically:**
1. Encode `prompt` → vector A
2. Randomly modify portions of A
3. Mutation rate controls percentage changed
4. Generate from mutated vector

**Examples:**
```
mutate(cat, 0.1)
→ Cat with 10% mutation (subtle)

mutate(character, 0.3)
→ 30% mutation (noticeable changes)

mutate(design, 0.5)
→ 50% mutation (significant departure)
```

**Use cases:**
- Evolution-style exploration
- Creating variants
- "What if this mutated?"
- Unexpected discoveries

---

## 3.4 `blend(a, b, ratio)` — Explicit Blend

**Syntax:** `blend(prompt_a, prompt_b, ratio)`

**What it does:**
Explicit function for blending. Same as `+` operator but clearer for complex expressions.

**Examples:**
```
blend(cat, dog, 0.5)
→ Same as "cat + dog : 0.5"

blend(realistic, anime, 0.3)
→ 30% realistic, 70% anime

blend(a, b, 0.5) :: style
→ Blend then apply style
```

---

## 3.5 `distance(a, b)` — Latent Distance

**Syntax:** `distance(prompt_a, prompt_b)`

**What it does:**
Calculates and displays the distance between two concepts in latent space. Useful for understanding how "far apart" concepts are.

**Output:**
- Numerical distance
- Similarity percentage
- Visualization of the difference

**Examples:**
```
distance(cat, dog)
→ "Distance: 0.42, Similarity: 58%"

distance(photo, realistic)
→ "Distance: 0.12, Similarity: 88%"

distance(happy, sad)
→ "Distance: 0.67, Similarity: 33%"
```

**Use cases:**
- Understanding concept relationships
- Debugging prompts
- Choosing interpolation steps
- Learning model behavior

---

# 4. Advanced Concepts

## 4.1 Latent Arithmetic

**Syntax:** `king - man + woman` (Word2Vec style)

**What it does:**
Applies vector arithmetic to concepts, enabling analogies and transformations. Famous example: "king - man + woman = queen"

**How it works:**
1. Encode each concept
2. Apply arithmetic operations
3. Result vector represents transformed concept
4. Generate from result

**Examples:**
```
king - man + woman
→ Queen-like concept

cat + (airplane - vehicle)
→ Cat with "flying" quality but not "vehicle-ness"

portrait - serious + playful
→ Playful portrait

winter - cold + warm
→ "Winter" but warm feeling
```

**Use cases:**
- Concept analogies
- Precise transformations
- Understanding relationships
- Creative concept engineering

---

## 4.2 Phase-Based Prompts

**Syntax:** `[structure: X] [detail: Y] [style: Z]`

**What it does:**
Different prompts for different generation phases. Structure prompts guide early steps, detail prompts guide middle, style prompts guide late steps.

**Examples:**
```
[structure: a forest scene] [detail: tall pine trees] [style: oil painting]

[composition: portrait centered] [subject: old man] [finish: high contrast]

[layout: city skyline] [elements: skyscrapers] [mood: noir]
```

**Use cases:**
- Maximum control over generation
- Separating concerns
- Professional workflow
- Precise artistic direction

---

## 4.3 Latent Bookmarks

**Syntax:** `#save:name` / `#load:name`

**What it does:**
Save specific latent positions or seeds with names for later recall. Build a library of "favorite" positions.

**Examples:**
```
cat #123 #save:fluffy_cat
→ Save this specific generation

#load:fluffy_cat + airplane
→ Load saved position and combine

#compare:v1,v2,v3
→ Compare saved positions
```

**Use cases:**
- Building asset libraries
- Consistent characters
- Reproducible results
- Sharing specific generations

---

## 4.4 Animation Syntax

**Syntax:** `a t=0 b t=1 : frames` or `loop: a | b : frames`

**What it does:**
Temporal generation for creating animations or video frames.

**Examples:**
```
cat t=0 airplane t=1 : 24
→ 24-frame animation morphing cat to airplane

loop: cat | dog : 30
→ 30-frame looping animation

bounce: happy % sad % happy : 60
→ 60-frame bounce animation
```

**Use cases:**
- Morph animations
- Concept exploration videos
- Looping GIFs
- Storyboarding

---

## 4.5 Conditional/Ternary

**Syntax:** `condition ? true_prompt : false_prompt`

**What it does:**
Conditional prompt selection based on some evaluation.

**Examples:**
```
random > 0.5 ? cat : dog
→ Randomly choose cat or dog

detailed ? photo : sketch
→ If "detailed" is strong, use photo style

complex ? multi-element : minimal
→ Complexity-based selection
```

**Use cases:**
- Dynamic prompt selection
- Randomized generation
- Adaptive prompting
- Complex logic

---

## 4.6 Variables & Macros

**Syntax:** `$name = value` / `#define NAME = value`

**What it does:**
Define reusable prompt components for cleaner, more maintainable prompts.

**Examples:**
```
$style = cyberpunk neon; a $style cat, a $style dog

#define QUALITY = masterpiece, best quality, detailed
a cat, #QUALITY

$base = __animal__ in __place__; $base > enhance
```

**Use cases:**
- Reusable components
- Consistent styling
- Complex prompt management
- Template systems

---

## Summary Comparison Table

| Operator | Category | Key Difference | Best For |
|----------|----------|----------------|----------|
| `%` | Interpolation | Direct latent walk | Morphs, exploration |
| `\|` | Temporal | Alternating guidance | Hybrid aesthetics |
| `+` | Blend | Simultaneous mix | Precise blending |
| `-` | Subtract | Concept removal | Avoiding elements |
| `*` | Emphasis | Amplification | Exaggeration |
| `@` | Schedule | Step-based timing | Phase control |
| `#` | Seed | Reproducibility | Consistency |
| `?` | Noise | Random variation | Subtle variety |
| `!` | Negate | Explicit NOT | Strong avoidance |
| `~` | Eased | Curved transition | Natural morphs |
| `X` | Breed | Genetic crossover | Unique hybrids |
| `::` | Style | Content/style split | Style transfer |
| `->` | Direction | Latent navigation | Fine-tuning |
| `??` | Explore | Diversity maximization | Ideation |
| `@@` | Grid | 2D mapping | Space visualization |
| `!!` | Chaos | Glitch injection | Experimental art |
| `=>` | Semantic | Meaningful gradient | Attribute control |

---

## Implementation Effort Matrix (HuggingFace Stack)

Based on z-Explorer's tech stack: **diffusers**, **transformers**, **peft**

### Effort Legend

| Level | Description | Typical Time |
|-------|-------------|--------------|
| 🟢 **Easy** | Uses existing APIs, minimal code | 1-2 hours |
| 🟡 **Medium** | Custom callbacks, some research | 4-8 hours |
| 🟠 **Hard** | Deeper integration, experimentation | 1-2 days |
| 🔴 **Very Hard** | Research required, complex systems | 3-5 days |

---

### Implementation Matrix by Operator

| Operator | Effort | Primary Library | Implementation Approach | Key APIs/Techniques |
|----------|--------|-----------------|------------------------|---------------------|
| **Core Single-Character Operators** |||||
| `#` Seed | 🟢 Easy | diffusers | Pass `generator` to pipeline | `torch.Generator(device).manual_seed(seed)` |
| `!` Negate | 🟢 Easy | diffusers | Built-in negative prompts | `negative_prompt` parameter |
| `*` Emphasis | 🟢 Easy | transformers | Scale embedding vectors | `prompt_embeds * multiplier` |
| `+` Blend | 🟢 Easy | transformers | Vector addition on embeddings | `embeds_a * ratio + embeds_b * (1-ratio)` |
| `-` Subtract | 🟢 Easy | transformers | Vector subtraction | `embeds_a - embeds_b * strength` |
| `?` Variation | 🟢 Easy | torch | Add Gaussian noise to embeddings | `embeds + torch.randn_like(embeds) * amount` |
| `%` Interpolation | 🟡 Medium | transformers | Loop with interpolated embeddings | `torch.lerp(embeds_a, embeds_b, t)` |
| `~` Smooth | 🟡 Medium | transformers | Interpolation + easing curves | Apply `ease()` function to interpolation t |
| `@` Schedule | 🟡 Medium | diffusers | Step callback to swap prompts | `callback_on_step_end`, check `step_index` |
| `\|` Alternate | 🟡 Medium | diffusers | Step callback to alternate | `callback_on_step_end`, `step % 2` swap |
| `X` Breed | 🟠 Hard | transformers | Dimension-wise crossover | Random mask: `where(mask, embeds_a, embeds_b)` |
| **Multi-Character Operators** |||||
| `::` Style | 🟠 Hard | diffusers+peft | IP-Adapter or style injection | `ip_adapter`, LoRA, or custom conditioning |
| `->` Direction | 🟠 Hard | transformers | Pre-compute direction vectors | Encode concept pairs, compute difference vectors |
| `??` Explore | 🟠 Hard | torch | Diversity sampling algorithms | Farthest point sampling on embedding sphere |
| `@@` Grid | 🟡 Medium | transformers | Nested interpolation loops | 2D grid of `torch.lerp` calls |
| `!!` Chaos | 🟡 Medium | diffusers | Inject noise in callback | Corrupt latents mid-denoising |
| `=>` Semantic | 🟠 Hard | transformers | Semantic direction discovery | May need classifier or direction learning |
| **Function-Style Operators** |||||
| `walk()` | 🟡 Medium | transformers | Same as `%` with cleaner API | Wrapper around interpolation |
| `orbit()` | 🟠 Hard | torch | Spherical sampling | Uniform points on hypersphere surface |
| `mutate()` | 🟡 Medium | torch | Random dimension mutation | Mask-based noise injection |
| `blend()` | 🟢 Easy | transformers | Same as `+` with cleaner API | Wrapper around blend |
| `distance()` | 🟢 Easy | torch | Cosine/L2 distance | `F.cosine_similarity(a, b)` |
| **Advanced Concepts** |||||
| Latent Arithmetic | 🟠 Hard | transformers | Vector arithmetic on embeddings | May not transfer perfectly from word2vec |
| Phase-Based | 🟠 Hard | diffusers | Multi-phase callback switching | Complex `callback_on_step_end` state machine |
| Bookmarks | 🟡 Medium | custom | Storage/retrieval system | JSON/pickle for seed + embedding pairs |
| Animation | 🔴 Very Hard | diffusers | Frame-by-frame generation | Video pipeline, frame interpolation |
| Conditional | 🟡 Medium | python | Parsing + logic evaluation | Custom expression parser |
| Variables | 🟡 Medium | python | Template substitution | Regex + string replacement |

---

### Implementation by Effort Level

#### 🟢 Easy (1-2 hours each) — Start Here!

| Operator | What You Need | Code Snippet |
|----------|---------------|--------------|
| `#` Seed | Pass seed to generator | `generator = torch.Generator("cuda").manual_seed(seed)` |
| `!` Negate | Use negative_prompt | `pipe(prompt, negative_prompt=negated)` |
| `*` Emphasis | Scale embeddings | `scaled = text_encoder(prompt) * multiplier` |
| `+` Blend | Weighted average | `mixed = emb_a * r + emb_b * (1-r)` |
| `-` Subtract | Vector subtraction | `result = emb_a - emb_b * strength` |
| `?` Variation | Add noise | `varied = emb + torch.randn_like(emb) * amount` |
| `distance()` | Cosine similarity | `sim = F.cosine_similarity(a, b)` |

#### 🟡 Medium (4-8 hours each) — Callbacks & Loops

| Operator | What You Need | Diffusers Feature |
|----------|---------------|-------------------|
| `%` Interpolation | Loop over interpolation values | Multiple `pipe()` calls with `torch.lerp` |
| `~` Smooth | Same as `%` + easing | Apply easing before `torch.lerp` |
| `@` Schedule | Step callback | `callback_on_step_end(pipe, step, timestep, callback_kwargs)` |
| `\|` Alternate | Step callback + swap | Swap `prompt_embeds` in callback |
| `@@` Grid | Nested loops | 2D array of pipe calls |
| `!!` Chaos | Latent corruption | Modify `latents` in callback |
| `mutate()` | Masked noise | Random mask + noise |
| Bookmarks | File storage | Save/load embeddings + seeds |

**Key diffusers pattern for `@` and `|`:**
```python
def callback(pipe, step, timestep, callback_kwargs):
    if step < threshold:
        callback_kwargs["prompt_embeds"] = embeds_a
    else:
        callback_kwargs["prompt_embeds"] = embeds_b
    return callback_kwargs

pipe(..., callback_on_step_end=callback)
```

#### 🟠 Hard (1-2 days each) — Research Required

| Operator | Challenge | Possible Approach |
|----------|-----------|-------------------|
| `X` Breed | Meaningful dimension selection | Random crossover first, then refine |
| `::` Style | Content/style separation | IP-Adapter, reference-only, or custom CLIP manipulation |
| `->` Direction | Pre-computing useful directions | Train or extract from concept pairs |
| `??` Explore | Maximizing diversity | Farthest point sampling, k-means on hypersphere |
| `=>` Semantic | Finding semantic axes | Concept pair subtraction, classifier gradients |
| `orbit()` | Uniform hypersphere sampling | Gaussian normalization technique |
| Latent Arithmetic | Doesn't always transfer cleanly | Experiment with different encoding methods |
| Phase-Based | Complex state management | State machine in callback |

#### 🔴 Very Hard (3-5 days+) — Major Feature

| Operator | Challenge | Notes |
|----------|-----------|-------|
| Animation Syntax | Video pipeline, frame coherence | Consider AnimateDiff or frame-by-frame with consistency |

---

### Library-Specific Notes

#### diffusers
- **Callbacks**: `callback_on_step_end` is your main hook for step-level control
- **Prompt Embeds**: Pre-encode with `pipe.encode_prompt()`, then pass `prompt_embeds`
- **Latent Access**: Callbacks receive `latents` in `callback_kwargs`
- **CFG Guidance**: Remember `do_classifier_free_guidance` affects embedding batch size

#### transformers
- **Text Encoding**: `CLIPTextModel` or `T5EncoderModel` for embeddings
- **Token Attention**: Can weight specific tokens via attention masks
- **Embedding Shape**: Usually `(batch, seq_len, hidden_dim)`

#### peft
- **LoRA Loading**: Already planned for z-Explorer
- **Style Transfer**: Could use LoRA for learned styles
- **Direction Vectors**: Could train LoRA-style adapters for directions

---

### Recommended Implementation Order

Based on effort vs. impact:

```
Week 1: Quick Wins (🟢 Easy)
├── #  Seed Control
├── +  Blend
├── -  Subtract
├── *  Emphasis
├── !  Negation
└── ?  Variation

Week 2: Core Power (🟡 Medium)
├── %  Interpolation
├── |  Alternating
├── @  Temporal Schedule
└── ~  Smooth Transition

Week 3: Advanced Features (🟠 Hard)
├── @@  Grid Exploration
├── X   Breeding
├── ::  Style Transfer
└── ??  Exploration Mode

Future: Research Projects (🔴 Very Hard)
├── ->  Direction Vectors
├── =>  Semantic Gradient
└── Animation Syntax
```

---

## Implementation Priority Recommendation

**Phase 1 (Core MVP):**
1. `%` — Latent Interpolation
2. `|` — Alternating Prompt
3. `+` — Latent Blend
4. `@` — Temporal Scheduling
5. `#` — Seed Control

**Phase 2 (Power Features):**
6. `-` — Subtraction
7. `~` — Smooth Transition
8. `??` — Exploration Mode
9. `::` — Style Transfer
10. `X` — Breeding

**Phase 3 (Advanced):**
11. `@@` — Grid Exploration
12. `->` — Direction Vectors
13. `!!` — Chaos Mode
14. `=>` — Semantic Gradient
15. Latent Arithmetic

**Phase 4 (Future):**
16. Animation Syntax
17. Latent Bookmarks
18. Variables/Macros
19. Phase-Based Prompts
20. Conditional Logic

---

*End of Prompt Operators Reference Brief*
