#!/usr/bin/env python3
"""Vibe check for generate_prompt_variable_values.

Run with: uv run python tests/scripts/generate_prompt_variable_values.py
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# Test cases: (variable_name, context_prompt, expected_description)
TEST_CASES = [
    # Simple values - should return short, single words or brief phrases
    (
        "cat_breed",
        "a __cat_breed__ sitting on a windowsill",
        # Perfect output: ["Persian", "Siamese", "Maine Coon", "Bengal", "Ragdoll"]
    ),
    (
        "color",
        "a __color__ sports car",
        # Perfect output: ["crimson", "midnight blue", "silver", "forest green", "golden"]
    ),
    (
        "art_style",
        "portrait of a woman, __art_style__",
        # Perfect output: ["impressionist", "art nouveau", "cyberpunk", "watercolor", "baroque"]
    ),
    
    # Detailed descriptions - should return full sentences/paragraphs
    (
        "detailed_scene",
        "",
        # Perfect output: [
        #   "A misty forest at dawn with rays of golden light piercing through ancient oak trees",
        #   "An abandoned Victorian mansion overtaken by ivy, moonlight casting long shadows",
        #   "A bustling Tokyo street corner at night, neon signs reflecting off rain-slicked pavement",
        # ]
    ),
    (
        "50_word_fantasy_landscape",
        "",
        # Perfect output: Each value should be ~50 words describing a fantasy landscape
        # Example: "A crystalline mountain range stretches toward twin moons, its peaks 
        #          glowing with ancient runes. Below, a river of liquid starlight winds 
        #          through floating islands covered in bioluminescent flora. Dragons soar 
        #          between the peaks while tiny villages cling to cliff faces, their 
        #          lanterns twinkling like earthbound stars."
    ),
    (
        "dramatic_lighting_scene_with_a_cat",
        "",
        # Perfect output: Full scenes featuring a cat with dramatic lighting
        # Example: "A sleek black cat perched on a marble pedestal, a single shaft of 
        #          golden light from a high window illuminating its emerald eyes while 
        #          the rest of the room fades into deep shadow"
    ),
    
    # User's example - very explicit instructions in the name
    (
        "very_detailed_at_least_50_words_scene",
        "",
        # Perfect output: Each value should be 50+ words of rich scene description
        # The LLM should interpret "very_detailed" and "at_least_50_words" literally
    ),
    
    # Edge cases - testing specific constraints
    (
        "short_3_word_mood",
        "a person feeling __short_3_word_mood__",
        # Perfect output: ["quietly content today", "lost in thought", "radiantly alive now", 
        #                  "peacefully at ease", "wildly, deeply happy"]
        # Each should be EXACTLY 3 words
    ),
    (
        "famous_inventor",
        "portrait of __famous_inventor__",
        # Perfect output: ["Nikola Tesla", "Ada Lovelace", "Leonardo da Vinci", 
        #                  "Marie Curie", "Thomas Edison"]
    ),
]


def main():
    from z_explorer.llm_provider import generate_prompt_variable_values
    
    console.print("\n[bold cyan]🧪 Vibe Check: generate_prompt_variable_values[/bold cyan]\n")
    
    for var_name, context in TEST_CASES:
        console.print(f"\n[bold yellow]━━━ __{var_name}__ ━━━[/bold yellow]")
        if context:
            console.print(f"[dim]Context: {context}[/dim]")
        
        console.print("[dim]Generating...[/dim]")
        
        try:
            values = generate_prompt_variable_values(
                variable_name=var_name,
                context_prompt=context or f"__{var_name}__",
                count=5,  # Just 5 for quick vibe check
            )
            
            console.print(f"[green]✓ Got {len(values)} values:[/green]\n")
            
            for i, val in enumerate(values, 1):
                word_count = len(val.split())
                console.print(f"  {i}. [dim]({word_count} words)[/dim] {val}")
                
        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
        
        console.print()
    
    console.print("[bold green]Done![/bold green]\n")


if __name__ == "__main__":
    main()

