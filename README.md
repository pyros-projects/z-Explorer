<p align="center">
  <img alt="Z-Explorer" src="docs/assets/github-banner.jpg" width="800">
</p>

<h1 align="center">⚡ Z-Explorer</h1>

<p align="center">
  <strong>Local AI Image Generation</strong><br>
  <em>Type a prompt. Get art. No cloud required. No spaghetti needed.</em>
</p>

<p align="center">
  <a href="#the-problem">The Problem</a> •
  <a href="#tutorial-your-first-10-minutes">Tutorial</a> •
  <a href="#installation">Installation</a> •
  <a href="#commands">Commands</a>
</p>

---

## The Problem

You wanted to make AI art. Instead you got:

- 47 browser tabs of documentation
- A node graph that looks like mom's spaghetti had a baby with a circuit board
- "CUDA out of memory" every 5 minutes
- Settings panels with 200 sliders you don't understand
- That one workflow that worked yesterday but doesn't today

**You're spending more time fighting the tool than creating.**

That's insane.

---

## Tutorial: Your First 10 Minutes

Z-Explorer strips away everything between you and your art. Let's prove it.

---

### Step 0: Install

**One command to install:**

```bash
# Linux
curl -fsSL https://raw.githubusercontent.com/pyros-projects/z-Explorer/main/install.sh | bash

# Windows (PowerShell)
irm https://raw.githubusercontent.com/pyros-projects/z-Explorer/main/install.ps1 | iex
```

**After a bit your browser should open**

Click **"Download"** when prompted. Grab a coffee while ~10GB of models download. ☕

<p align="center">
  <img alt="Z-Explorer" src="docs/assets/download-progress-live.png" width="400">
</p>

Once complete — you're ready to create!

> **Requirements:** Linux or Windows, NVIDIA GPU (GTX 1080 Ti or newer) with 10GB+ VRAM, [uv](https://docs.astral.sh/uv/) package manager, **[Node.js](https://nodejs.org/)**, and Unicode support in terminal (like Windows Terminal or almost any Linux terminal).
> See [Installation](#installation) for Docker, manual setup, and advanced options.

---

### Step 1: Your First Image

Type a prompt. Any prompt. Natural language, just like talking to a person:

```
>>> a cute fox in a magical forest
```

Hit enter. Watch the magic happen.

<p align="center">
  <img alt="Z-Explorer" src="docs/assets/01_cute_fox.png" width="800">
</p>

That's it. No nodes. No tabs. No sliders. Just your idea, rendered.

Your image appears in the gallery above. Hover over it to see the prompt. Click to view full size.

---

### Step 2: Add Some Randomness

Let's make things interesting. **Variables** let you randomize parts of your prompt:

```
>>> a __animal__ in a magical forest
```

<p align="center">
  <img alt="Z-Explorer" src="docs/assets/02_animal.png" width="800">
</p>

Each time you run this, Z-Explorer picks a random animal from its library. Run it 5 times, get 5 different creatures.

<p align="center">
  <img alt="Z-Explorer" src="docs/assets/03_animal.png" width="800">
</p>

---

### Step 3: More on Variables

You may ask where it knows what variables are available.

Here's where it gets magical. **They get generated on the fly:**

```
>>> a cute __mythical_creature__ in a magical forest
```

<p align="center">
  <img alt="Z-Explorer" src="docs/assets/04_mythical_creature.png" width="800">
</p>


Z-Explorer's local LLM generates it on the fly:

```
✨ Generated __mythical_creature__ with 20 values
   → Phoenix, Dragon, Unicorn, Griffin, Kitsune...
```

Saved to your library forever. Use `__mythical_creature__` anytime.

No more googling "list of mythical creatures". Just ask, and it appears.

**Pro tip:** Type `/vars` to see all available variables.

<p align="center">
  <img alt="Z-Explorer" src="docs/assets/05_mythical_creature.png" width="800">
</p>

**Pro tip:** Combine as many variables as you want, and remember: The name of the variable steers its content!

<p align="center">
  <img alt="Z-Explorer" src="docs/assets/14_multi_var.png" width="800">
</p>

---

### Step 4: Enhance Your Prompts

Your prompt: `a cute fox`

What the AI actually needs for stunning results: `A cute fox with fluffy orange fur and bright amber eyes, sitting in an enchanted forest clearing, soft dappled sunlight filtering through ancient oak trees, magical fireflies floating in the air, Studio Ghibli inspired, warm color palette, highly detailed fur texture`

The `>` operator bridges that gap:

```
>>> a cute fox > studio ghibli, 2d, anime
```

<p align="center">
  <img alt="Z-Explorer" src="docs/assets/06_enhance.png" width="800">
</p>


The local LLM expands your idea into a rich, detailed prompt. Same intent, 10x better output.

Think of the `>` operator as magical 'turns into' operator which makes exploring your ideas even more fun!

<p align="center">
  <img alt="Z-Explorer" src="docs/assets/07_enhance.png" width="800">
</p>


---

### Step 5: Generate Variations

Found a prompt you like? Generate multiple variations at once:

```
>>> a __mythical_creature__ in a magical forest : x5
```

<p align="center">
  <img alt="Z-Explorer" src="docs/assets/08_multi.png" width="800">
</p>

5 images, 5 different creatures, 5 different seeds. Find the diamond in the rough.

---

### Step 6: Custom Sizes

Need a specific aspect ratio? Add size parameters:

```
>>> epic fantasy landscape : w1216,h832
```

<p align="center">
  <img alt="Z-Explorer" src="docs/assets/09_widescreen.png" width="800">
</p>


Or combine everything:

```
>>> a __mythical_creature__ in a magical forest > cinematic and epic : x3,w1216,h832
```

<p align="center">
  <img alt="Z-Explorer" src="docs/assets/10.png" width="800">
</p>

3 widescreen cinematic images with random creatures and enhanced prompts. One command.

<p align="center">
  <img alt="Z-Explorer" src="docs/assets/11.png" width="800">
</p>

---

### Step 7: Customize Your Workspace

Type `/settings` to open the settings dialog:

```
>>> /settings
```

<p align="center">
  <img alt="Z-Explorer" src="docs/assets/12_settings.png" width="800">
</p>

**Gallery Tab** — Choose how your images display:
- **Flex Row** — Images flow naturally (default)
- **Masonry** — Pinterest-style columns
- **Grid** — Uniform squares or auto-fit


**Thumbnail Size** — See more detail or fit more images:
- Small, Medium, Large, XL, or custom (80-500px)

---

### Step 8: Explore Your Gallery

Your gallery grows with every generation. Use the layout options to find what works for you:

<p align="center">
  <img alt="Z-Explorer" src="docs/assets/13_layout.png" width="800">
</p>

**Hover** over any image to see its prompt. **Click** to view full size.

Every image is saved to your `output/` folder with its prompt embedded in the metadata.

---

### What's Next?

You've learned the basics. Here's what else you can do:

| Command | What it does |
|---------|--------------|
| `/seed 12345` | Set a specific seed for reproducibility |
| `/size 1024x1024` | Set default dimensions |
| `/gpu` | Check GPU memory status |
| `/unload` | Free up GPU memory |

**Create your own variables:**

```
# library/mood.md
ethereal
cyberpunk
cottagecore
dark fantasy
solarpunk
```

Now use `__mood__` in any prompt. Your vocabulary, your art.

---

### The Philosophy

Everything runs locally. No cloud. No API keys. No monthly fees. No data leaving your machine.

Your GPU, your art, your privacy.

---

## Two Ways to Create

### 🌐 Web UI (Default)

Launch Z-Explorer and get a beautiful web-based UI:

- **Masonry gallery** of all your generations
- **Fake CLI** for that terminal aesthetic (with autocomplete!)
- **Live preview** — images appear the moment they're done
- **Prompt saved** with every image

```bash
uv run z-explorer
```

### ⌨️ CLI Mode (For Purists)

Prefer a pure terminal experience?
Terminal with good graphical abilities preferred (Kitty or Alacritty)

```bash
uv run z-explorer --cli
```

Same power, different vibe. Perfect for SSH sessions or terminal lovers.

---

## Installation

### Prerequisites

- **Linux or Windows** (macOS not supported — requires NVIDIA CUDA)
- **NVIDIA GPU** with CUDA support (12GB+ VRAM recommended)
- **[uv](https://docs.astral.sh/uv/)** — fast Python package manager
- **[Node.js](https://nodejs.org/)** 18+ — for building the web UI

**Install uv:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # Linux
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows
```

**Install Node.js:**
```bash
# Linux (Ubuntu/Debian)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Linux (Fedora/RHEL)
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
sudo dnf install -y nodejs

# Windows - download installer from https://nodejs.org/
# Or use winget:
winget install OpenJS.NodeJS.LTS
```

### Quick Install

```bash
git clone https://github.com/pyros-projects/z-Explorer.git
cd z-Explorer
uv run z-explorer --quick-setup
```

That's it. `uv sync` handles all dependencies including bleeding-edge versions from Git.

### One-Liner Install

**Linux:**
```bash
curl -fsSL https://raw.githubusercontent.com/pyros-projects/z-Explorer/main/install.sh | bash
```

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/pyros-projects/z-Explorer/main/install.ps1 | iex
```

> ⚠️ **macOS is not supported** — requires NVIDIA CUDA (bitsandbytes dependency)

### Docker

**Pre-built image:**
```bash
docker run --gpus all -p 8345:8345 -v ./output:/app/output ghcr.io/pyros-projects/z-explorer:latest
```

**Or build locally:**
```bash
git clone https://github.com/pyros-projects/z-Explorer.git
cd z-Explorer
docker build -t z-explorer .
docker run --gpus all -p 8345:8345 -v ./output:/app/output z-explorer
```

Then open http://localhost:8345

### First-Time Setup

On first launch, Z-Explorer guides you through model configuration:

```
? Choose a setup option:
> Quick Start (Recommended for beginners)
  Custom Setup
  Full Quality
```

**Pick "Quick Start"** — it downloads optimized models that work great on 12GB GPUs:
- Image model: ~6GB download, ~12GB VRAM
- LLM: ~4GB download, fast inference

The wizard downloads everything automatically. Grab a coffee ☕

### Other Options

- **Custom Setup** — Mix and match model sources (local files, HuggingFace, quantized)
- **Full Quality** — Maximum quality for 24GB+ GPUs (~15GB download)

For advanced configuration, see [docs/CONFIGURATION.md](docs/CONFIGURATION.md) or copy `env.example` to `.env`.

### Reconfigure Anytime

```bash
uv run z-explorer --setup        # Re-run setup wizard (interactive)
uv run z-explorer --quick-setup  # Auto-configure with defaults (non-interactive)
uv run z-explorer --show-config  # Check current configuration
```

### Updating

```bash
git pull
uv sync
```

---

## Commands

| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/vars` | List available prompt variables |
| `/enhance <prompt>` | Preview enhanced prompt |
| `/seed <number>` | Set seed for reproducibility |
| `/size <WxH>` | Set output dimensions (e.g., 1920x1080) |
| `/gpu` | Check GPU memory status |
| `/unload` | Free GPU memory |
| `/settings` | Open settings dialog |
| `/quit` | Exit |

**Prompt Syntax:**

```
__variable__        Random value from variable
__variable:5__      Specific index (5th value)
prompt > instruction   Enhance prompt with instruction
prompt : x10,w1920    Batch with parameters
```

---

## What's Under the Hood

- **Z-Image-Turbo** — Lightning-fast image generation
- **Qwen3-4B** — Local LLM for enhancement and variable generation
- **FastAPI** — Backend API server
- **Svelte** — Beautiful web UI

Everything runs locally. No internet required after initial setup.

---

## Roadmap

- **LoRA Support** — Load and apply LoRA weights for fine-tuned styles, characters, and concepts
- **Variable Management** — Create, edit, and organize your prompt variables through the UI
- **Gallery Management** — Multiple folders, favorites, tags, search, and filtering to organize thousands of generations
- **More Prompt Magic** — Latent space exploration, prompt interpolation, and support for external LLM services (OpenAI, Anthropic, Ollama)

---

<p align="center">
  <em>Inspired by</em><br>
  <strong>https://github.com/lllyasviel/Fooocus</strong>
</p>

---

## License

MIT — Go forth and create.
