#!/usr/bin/env python3
"""Vibe check for generate_prompt_variable_values with model comparison.

Run with:
    # Single model (uses current LLM_REPO from env)
    uv run python tests/scripts/generate_prompt_variable_values.py

    # Compare two models side-by-side
    uv run python tests/scripts/generate_prompt_variable_values.py --compare \
        "unsloth/Qwen3-4B-Instruct-2507-bnb-4bit" \
        "mistralai/Ministral-3-3B-Instruct-2512"

    # Single specific model
    uv run python tests/scripts/generate_prompt_variable_values.py --model "mistralai/Ministral-3-3B-Instruct-2512"
"""

import argparse
import os

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# Test cases: (variable_name, context_prompt)
TEST_CASES = [
    # Simple values - should return short, single words or brief phrases
    (
        "cat_breed",
        "a __cat_breed__ sitting on a windowsill",
    ),
    (
        "color",
        "a __color__ sports car",
    ),
    (
        "art_style",
        "portrait of a woman, __art_style__",
    ),
    # Detailed descriptions - should return full sentences/paragraphs
    (
        "detailed_scene",
        "",
    ),
    (
        "50_word_fantasy_landscape",
        "",
    ),
    (
        "dramatic_lighting_scene_with_a_cat",
        "",
    ),
    # User's example - very explicit instructions in the name
    (
        "very_detailed_at_least_50_words_scene",
        "",
    ),
    # Edge cases - testing specific constraints
    (
        "short_3_word_mood",
        "a person feeling __short_3_word_mood__",
    ),
    (
        "famous_inventor",
        "portrait of __famous_inventor__",
    ),
]


def run_single_model(model_repo: str | None = None):
    """Run tests with a single model."""
    from z_explorer.llm_provider import generate_prompt_variable_values, unload_model

    model_name = model_repo or os.environ.get("LLM_REPO", "default")
    console.print(
        f"\n[bold cyan]🧪 Vibe Check: generate_prompt_variable_values[/bold cyan]"
    )
    console.print(f"[dim]Model: {model_name}[/dim]\n")

    if model_repo:
        os.environ["LLM_MODE"] = "hf_download"
        os.environ["LLM_REPO"] = model_repo
        unload_model()  # Force reload with new model

    for var_name, context in TEST_CASES:
        console.print(f"\n[bold yellow]━━━ __{var_name}__ ━━━[/bold yellow]")
        if context:
            console.print(f"[dim]Context: {context}[/dim]")

        console.print("[dim]Generating...[/dim]")

        try:
            values = generate_prompt_variable_values(
                variable_name=var_name,
                context_prompt=context or f"__{var_name}__",
                count=5,
            )

            console.print(f"[green]✓ Got {len(values)} values:[/green]\n")

            for i, val in enumerate(values, 1):
                word_count = len(val.split())
                console.print(f"  {i}. [dim]({word_count} words)[/dim] {val}")

        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")

        console.print()

    console.print("[bold green]Done![/bold green]\n")


def generate_all_for_model(
    model_repo: str, progress: Progress, task_id
) -> dict[str, list[str]]:
    """Generate all test case values for a single model."""
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

    for i, (var_name, context) in enumerate(TEST_CASES):
        progress.update(task_id, description=f"__{var_name}__")

        try:
            values = llm_provider.generate_prompt_variable_values(
                variable_name=var_name,
                context_prompt=context or f"__{var_name}__",
                count=3,
            )
            results[var_name] = values
        except Exception as e:
            results[var_name] = [f"Error: {e}"]

        progress.update(task_id, completed=i + 1)

    return results


def run_comparison(model_a: str, model_b: str):
    """Run tests comparing two models side-by-side."""
    console.print(
        f"\n[bold cyan]🧪 Model Comparison: generate_prompt_variable_values[/bold cyan]"
    )
    console.print(f"[blue]Model A:[/blue] {model_a}")
    console.print(f"[magenta]Model B:[/magenta] {model_b}\n")

    total_tests = len(TEST_CASES)

    # Phase 1: Generate all values for Model A
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

    # Phase 2: Generate all values for Model B
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

    for var_name, context in TEST_CASES:
        # Header for this test case
        console.print(f"\n[bold yellow]{'━' * 80}[/bold yellow]")
        console.print(f"[bold yellow]  __{var_name}__[/bold yellow]")
        if context:
            console.print(f"[dim]  Context: {context}[/dim]")
        console.print(f"[bold yellow]{'━' * 80}[/bold yellow]\n")

        values_a = results_a.get(var_name, ["No results"])
        values_b = results_b.get(var_name, ["No results"])

        # Display Model A results
        console.print(
            Panel.fit(
                "\n".join([f"[dim]({len(v.split())}w)[/dim] {v}" for v in values_a]),
                title=f"[blue]{model_a_short}[/blue]",
                border_style="blue",
            )
        )

        console.print()  # Spacing

        # Display Model B results
        console.print(
            Panel.fit(
                "\n".join([f"[dim]({len(v.split())}w)[/dim] {v}" for v in values_b]),
                title=f"[magenta]{model_b_short}[/magenta]",
                border_style="magenta",
            )
        )

        console.print()

    console.print("[bold green]" + "=" * 80 + "[/bold green]")
    console.print("[bold green]                       COMPARISON COMPLETE[/bold green]")
    console.print("[bold green]" + "=" * 80 + "[/bold green]\n")


def main():
    parser = argparse.ArgumentParser(
        description="Vibe check for generate_prompt_variable_values with optional model comparison"
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
