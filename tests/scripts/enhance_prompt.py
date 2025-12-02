#!/usr/bin/env python3
"""Vibe check for enhance_prompt with model comparison.

Tests that prompt enhancement respects user intent - especially for
"low quality" or stylized requests that shouldn't get upgraded to
"ultra HD masterpiece" aesthetics.

Run with:
    # Single model (uses current LLM_REPO from env)
    uv run python tests/scripts/enhance_prompt.py

    # Compare two models side-by-side
    uv run python tests/scripts/enhance_prompt.py --compare \
        "unsloth/Qwen3-4B-Instruct-2507-bnb-4bit" \
        "mistralai/Ministral-3-3B-Instruct-2512"

    # Single specific model
    uv run python tests/scripts/enhance_prompt.py --model "mistralai/Ministral-3-3B-Instruct-2512"
"""

import argparse
import os

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# Test cases: (user_prompt, instruction, expected_behavior)
# expected_behavior is just a note for the human reviewer
TEST_CASES = [
    # === INTENT: LOW QUALITY / DEGRADED ===
    (
        "a cat sitting on a couch",
        "bad quality, blurry amateur photo",
        "Should enhance for blur, noise, amateur framing - NOT add 'ultra HD'",
    ),
    (
        "a forest landscape",
        "VHS recording from the 90s, scan lines, tracking artifacts",
        "Should enhance for analog video imperfections",
    ),
    (
        "portrait of a woman",
        "polaroid instant photo, washed out colors, light leak",
        "Should enhance for film artifacts and instant photo aesthetics",
    ),
    (
        "city street at night",
        "security camera footage, low resolution, grainy",
        "Should enhance for surveillance camera look",
    ),
    # === INTENT: SPECIFIC ARTISTIC STYLES ===
    (
        "a dragon",
        "children's crayon drawing, messy, colorful",
        "Should enhance for child-like art style, not professional illustration",
    ),
    (
        "a house",
        "quick pencil sketch, rough lines, unfinished",
        "Should enhance for sketchy, loose quality",
    ),
    (
        "a sunset",
        "glitch art, corrupted data, pixel sorting",
        "Should enhance for digital corruption aesthetics",
    ),
    # === INTENT: HIGH QUALITY (control group) ===
    (
        "a cat sitting on a couch",
        "professional studio photography, sharp focus, perfect lighting",
        "Should enhance for professional quality - quality modifiers OK here",
    ),
    (
        "a forest landscape",
        "masterpiece oil painting, museum quality, fine art",
        "Should enhance for fine art quality",
    ),
    (
        "portrait of a woman",
        "8K ultra HD, hyper realistic, octane render",
        "Should enhance for maximum technical quality",
    ),
    # === INTENT: NEUTRAL (no instruction) ===
    (
        "a cat sitting on a couch",
        "",
        "No instruction - should default to professional aesthetics",
    ),
    (
        "cyberpunk city at night with neon lights",
        "",
        "No instruction - should enhance with appropriate genre details",
    ),
    (
        "portrait of an elderly man",
        "",
        "No instruction - should add tasteful professional enhancements",
    ),
]


def run_single_model(model_repo: str | None = None):
    """Run tests with a single model."""
    from z_explorer.llm_provider import enhance_prompt, unload_model

    model_name = model_repo or os.environ.get("LLM_REPO", "default")
    console.print(f"\n[bold cyan]🧪 Vibe Check: enhance_prompt[/bold cyan]")
    console.print(f"[dim]Model: {model_name}[/dim]\n")

    if model_repo:
        os.environ["LLM_MODE"] = "hf_download"
        os.environ["LLM_REPO"] = model_repo
        unload_model()  # Force reload with new model

    for user_prompt, instruction, expected in TEST_CASES:
        console.print(f"\n[bold yellow]{'━' * 80}[/bold yellow]")
        console.print(f"[bold]Prompt:[/bold] {user_prompt}")
        if instruction:
            console.print(f"[bold]Instruction:[/bold] {instruction}")
        else:
            console.print("[dim]Instruction: (none)[/dim]")
        console.print(f"[dim italic]Expected: {expected}[/dim italic]")
        console.print(f"[bold yellow]{'━' * 80}[/bold yellow]")

        console.print("[dim]Generating...[/dim]")

        try:
            enhanced = enhance_prompt(user_prompt, instruction)
            word_count = len(enhanced.split())

            console.print(f"\n[green]✓ Enhanced ({word_count} words):[/green]")
            console.print(Panel(enhanced, border_style="green", padding=(0, 2)))

            # Quick automated checks (just warnings, not failures)
            enhanced_lower = enhanced.lower()

            # Check for quality modifier contamination in low-quality requests
            if instruction and any(
                term in instruction.lower()
                for term in [
                    "bad quality",
                    "amateur",
                    "blurry",
                    "low resolution",
                    "vhs",
                    "grainy",
                ]
            ):
                quality_terms = [
                    "ultra hd",
                    "8k",
                    "4k",
                    "masterpiece",
                    "highly detailed",
                    "professional quality",
                ]
                found_terms = [t for t in quality_terms if t in enhanced_lower]
                if found_terms:
                    console.print(
                        f"[yellow]⚠ Warning: Found quality modifiers in low-quality request: {found_terms}[/yellow]"
                    )

        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")

        console.print()

    console.print("[bold green]Done![/bold green]\n")


def generate_all_for_model(
    model_repo: str, progress: Progress, task_id
) -> dict[tuple[str, str], str]:
    """Generate all test case enhancements for a single model."""
    import logging
    import warnings

    # Suppress ALL noisy output during model loading
    logging.getLogger("transformers").setLevel(logging.ERROR)
    logging.getLogger("accelerate").setLevel(logging.ERROR)
    warnings.filterwarnings("ignore")

    # Disable tqdm progress bars
    os.environ["TQDM_DISABLE"] = "1"
    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

    from z_explorer import llm_provider

    # Unload and set new model
    llm_provider.unload_model()
    os.environ["LLM_MODE"] = "hf_download"
    os.environ["LLM_REPO"] = model_repo

    results = {}

    for i, (user_prompt, instruction, _expected) in enumerate(TEST_CASES):
        short_desc = f"{user_prompt[:30]}..." if len(user_prompt) > 30 else user_prompt
        progress.update(task_id, description=short_desc)

        try:
            enhanced = llm_provider.enhance_prompt(user_prompt, instruction)
            results[(user_prompt, instruction)] = enhanced
        except Exception as e:
            results[(user_prompt, instruction)] = f"Error: {e}"

        progress.update(task_id, completed=i + 1)

    return results


def run_comparison(model_a: str, model_b: str):
    """Run tests comparing two models side-by-side."""
    console.print(f"\n[bold cyan]🧪 Model Comparison: enhance_prompt[/bold cyan]")
    console.print(f"[blue]Model A:[/blue] {model_a}")
    console.print(f"[magenta]Model B:[/magenta] {model_b}\n")

    total_tests = len(TEST_CASES)

    # Phase 1: Generate all enhancements for Model A
    console.print("[bold blue]Phase 1: Generating with Model A...[/bold blue]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TextColumn("[progress.percentage]{task.completed}/{task.total}"),
        console=console,
    ) as progress:
        task_a = progress.add_task(
            f"[blue]{model_a.split('/')[-1]}[/blue]", total=total_tests
        )
        results_a = generate_all_for_model(model_a, progress, task_a)

    console.print("[green]✓ Model A complete[/green]\n")

    # Phase 2: Generate all enhancements for Model B
    console.print("[bold magenta]Phase 2: Generating with Model B...[/bold magenta]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TextColumn("[progress.percentage]{task.completed}/{task.total}"),
        console=console,
    ) as progress:
        task_b = progress.add_task(
            f"[magenta]{model_b.split('/')[-1]}[/magenta]", total=total_tests
        )
        results_b = generate_all_for_model(model_b, progress, task_b)

    console.print("[green]✓ Model B complete[/green]\n")

    # Phase 3: Display comparison report
    console.print("[bold yellow]" + "=" * 80 + "[/bold yellow]")
    console.print(
        "[bold yellow]                         COMPARISON REPORT[/bold yellow]"
    )
    console.print("[bold yellow]" + "=" * 80 + "[/bold yellow]\n")

    model_a_short = model_a.split("/")[-1]
    model_b_short = model_b.split("/")[-1]

    for user_prompt, instruction, expected in TEST_CASES:
        # Header for this test case
        console.print(f"\n[bold yellow]{'━' * 80}[/bold yellow]")
        console.print(f"[bold]Prompt:[/bold] {user_prompt}")
        if instruction:
            console.print(f"[bold]Instruction:[/bold] {instruction}")
        else:
            console.print("[dim]Instruction: (none)[/dim]")
        console.print(f"[dim italic]Expected: {expected}[/dim italic]")
        console.print(f"[bold yellow]{'━' * 80}[/bold yellow]\n")

        enhanced_a = results_a.get((user_prompt, instruction), "No result")
        enhanced_b = results_b.get((user_prompt, instruction), "No result")

        # Display Model A results
        console.print(
            Panel(
                enhanced_a,
                title=f"[blue]{model_a_short}[/blue] ({len(enhanced_a.split())}w)",
                border_style="blue",
            )
        )

        console.print()  # Spacing

        # Display Model B results
        console.print(
            Panel(
                enhanced_b,
                title=f"[magenta]{model_b_short}[/magenta] ({len(enhanced_b.split())}w)",
                border_style="magenta",
            )
        )

        console.print()

    console.print("[bold green]" + "=" * 80 + "[/bold green]")
    console.print("[bold green]                       COMPARISON COMPLETE[/bold green]")
    console.print("[bold green]" + "=" * 80 + "[/bold green]\n")


def main():
    parser = argparse.ArgumentParser(
        description="Vibe check for enhance_prompt with optional model comparison"
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        help="Single model to test (e.g., 'mistralai/Ministral-3-3B-Instruct-2512')",
    )
    parser.add_argument(
        "--compare",
        "-c",
        nargs=2,
        metavar=("MODEL_A", "MODEL_B"),
        help="Compare two models side-by-side",
    )

    args = parser.parse_args()

    if args.compare:
        run_comparison(args.compare[0], args.compare[1])
    else:
        run_single_model(args.model)


if __name__ == "__main__":
    main()
