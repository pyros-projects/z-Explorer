"""Standalone local CLI for pyros-cli.

This provides a fully offline image generation experience using:
- Z-Image-Turbo for image generation
- Qwen3-4B for prompt enhancement and variable generation

No internet, ComfyUI, or cloud APIs required!
"""

import os
import random
import re
import sys
from pathlib import Path
from importlib.metadata import version, PackageNotFoundError

# Version from pyproject.toml (via package metadata)
try:
    __version__ = version("z-explorer")
except PackageNotFoundError:
    __version__ = "dev"  # Running from source without install


def get_changelog_path() -> Path:
    """Get the path to the CHANGELOG.md file."""
    # Try multiple locations
    possible_paths = [
        Path(__file__).parent.parent.parent.parent / "CHANGELOG.md",  # From src/z_explorer/
        Path.cwd() / "CHANGELOG.md",  # Current directory
        Path(__file__).parent / "CHANGELOG.md",  # Same directory as cli.py
    ]
    for p in possible_paths:
        if p.exists():
            return p
    return None

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from art import text2art
import questionary
from prompt_toolkit.completion import Completer, Completion

console = Console()

# Load environment variables
load_dotenv()


# Custom completer for prompt variables and commands
class PromptCompleter(Completer):
    """Autocomplete for prompt variables (__var__) and commands (/cmd)."""
    
    def __init__(self, choices):
        self.choices = choices
        # Extract commands without the leading slash for better matching
        self.commands = [cmd[1:] if cmd.startswith('/') else cmd for cmd in choices if cmd.startswith('/')]
        # Keep prompt variables as they are
        self.vars = [var for var in choices if not var.startswith('/')]
    
    def get_completions(self, document, complete_event):
        text_before_cursor = document.text_before_cursor
        cursor_position = len(text_before_cursor)
        
        # Find commands - they must start with /
        if '/' in text_before_cursor:
            last_slash_pos = text_before_cursor.rfind('/')
            if cursor_position > last_slash_pos:
                current_word = text_before_cursor[last_slash_pos+1:].strip()
                for command in self.commands:
                    if command.startswith(current_word):
                        yield Completion(
                            command, 
                            start_position=-len(current_word),
                            display=f"/{command}"
                        )
        
        # Find prompt variables - looking for partial "__var" matches
        if '__' in text_before_cursor:
            last_var_start = text_before_cursor.rfind('__')
            if cursor_position > last_var_start and text_before_cursor.count('__', last_var_start) == 1:
                current_var = text_before_cursor[last_var_start:]
                
                if ':' not in current_var:  # Not typing an index
                    for var in self.vars:
                        if var.startswith(current_var):
                            completion_text = var[len(current_var):]
                            yield Completion(
                                completion_text, 
                                start_position=0,
                                display=var
                            )


def get_autocomplete_suggestions(prompt_vars: dict) -> list:
    """Get autocomplete suggestions for commands and prompt variables."""
    # Commands
    commands = ["/help", "/vars", "/enhance", "/seed", "/size", "/gpu", "/unload", "/version", "/changelog", "/quit", "/q"]

    # Prompt variables
    var_suggestions = list(prompt_vars.keys())

    return commands + var_suggestions


def parse_batch_params(user_input: str) -> tuple[str, dict]:
    """Parse batch parameters from prompt.
    
    Syntax: prompt text : x10,h832,w1216
    
    Parameters (all optional, separated by comma):
        x<N>  - Generate N images (default: 1)
        h<N>  - Height in pixels (default: 1024)
        w<N>  - Width in pixels (default: 1024)
    
    Args:
        user_input: The full user input string
        
    Returns:
        Tuple of (prompt without params, params dict)
    """
    params = {
        "count": 1,
        "height": 1024,
        "width": 1024,
    }
    
    # Check if there are parameters (: at the end, not part of > enhancement)
    if ":" not in user_input:
        return user_input, params
    
    # Split by last colon that's not inside the enhancement part
    # Handle case: "prompt > enhance : x10" vs "prompt : x10"
    parts = user_input.rsplit(":", 1)
    if len(parts) != 2:
        return user_input, params
    
    prompt_part = parts[0].strip()
    param_part = parts[1].strip()
    
    # If param_part doesn't look like parameters (should contain x, h, or w followed by numbers)
    if not any(p.strip().startswith(('x', 'h', 'w')) and any(c.isdigit() for c in p) 
               for p in param_part.split(',')):
        return user_input, params
    
    # Parse individual parameters
    for param in param_part.split(','):
        param = param.strip().lower()
        if not param:
            continue
            
        if param.startswith('x') and param[1:].isdigit():
            params["count"] = int(param[1:])
        elif param.startswith('h') and param[1:].isdigit():
            params["height"] = int(param[1:])
        elif param.startswith('w') and param[1:].isdigit():
            params["width"] = int(param[1:])
    
    return prompt_part, params


def print_banner():
    """Display the local mode banner."""
    console.clear()
    banner = text2art("Pyro's z-explorer", font="tarty4")
    console.print(banner, style="magenta")
    console.print(f"[dim]v{__version__} • Fully offline image generation with Z-Image-Turbo + Qwen3-4B[/dim]")
    console.line()


def print_gpu_status():
    """Print GPU memory status."""
    from z_explorer.image_generator import get_gpu_memory_info
    
    info = get_gpu_memory_info()
    if "error" not in info:
        console.print(
            f"[dim]GPU: {info['free_gb']:.1f}GB free / {info['total_gb']:.1f}GB total[/dim]"
        )
    else:
        console.print("[yellow]⚠ No GPU detected - generation will be slow[/yellow]")


def load_prompt_vars() -> dict:
    """Load prompt variables from library."""
    from z_explorer.models.prompt_vars import load_prompt_vars as _load
    return _load()


def substitute_vars_local(prompt: str, prompt_vars: dict) -> str:
    """Substitute prompt variables, generating missing ones locally.
    
    Args:
        prompt: The user's prompt with __variables__
        prompt_vars: Existing prompt variables dict
        
    Returns:
        Prompt with all variables substituted
    """
    from z_explorer.llm_provider import generate_prompt_variable_values
    from z_explorer.models.prompt_vars import save_prompt_var
    
    # Pattern to find __variable__ in the prompt
    pattern = r'(__[a-zA-Z0-9_\-/]+__)'
    
    substituted = prompt
    matches = re.findall(pattern, substituted)
    
    for match in matches:
        var_name = match  # e.g., __cat_breed__
        
        if var_name in prompt_vars:
            # Use existing variable
            var = prompt_vars[var_name]
            if var.values:
                replacement = random.choice(var.values)
                substituted = substituted.replace(var_name, replacement, 1)
                console.print(f"[dim]Substituted {var_name} → {replacement}[/dim]")
        else:
            # Generate new variable using local LLM
            raw_name = var_name.strip("_")
            console.print(f"\n[cyan]🤖 Generating values for missing variable: {var_name}[/cyan]")
            
            values = generate_prompt_variable_values(raw_name, prompt)
            
            if values:
                # Save for future use
                file_path = save_prompt_var(
                    variable_name=raw_name,
                    description=f"Auto-generated values for {raw_name}",
                    values=values
                )
                console.print(f"[green]✓ Generated {len(values)} values, saved to {file_path}[/green]")
                
                # Use one of the generated values
                replacement = random.choice(values)
                substituted = substituted.replace(var_name, replacement, 1)
                console.print(f"[dim]Substituted {var_name} → {replacement}[/dim]")
            else:
                console.print(f"[yellow]⚠ Could not generate values for {var_name}[/yellow]")
    
    return substituted


def enhance_prompt_local(prompt: str) -> str:
    """Enhance a prompt using the local LLM."""
    from z_explorer.llm_provider import enhance_prompt
    
    console.print("\n[cyan]🤖 Enhancing prompt with local LLM...[/cyan]")
    enhanced = enhance_prompt(prompt)
    console.print(f"[green]✓ Enhanced prompt ready[/green]")
    return enhanced


def generate_image_local(
    prompt: str, 
    seed: int = None,
    width: int = 1024,
    height: int = 1024
) -> tuple:
    """Generate an image using Z-Image-Turbo."""
    from z_explorer.image_generator import generate_image_with_preview
    
    console.print(f"[magenta]🎨 Generating {width}x{height} image...[/magenta]")
    return generate_image_with_preview(prompt, width=width, height=height, seed=seed)


def display_image_preview(image_path: str):
    """Display image preview in terminal if supported."""
    try:
        from z_explorer.services.preview import display_terminal_preview
        import asyncio
        
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        asyncio.run(display_terminal_preview(image_bytes))
    except Exception as e:
        console.print(f"[dim]Preview not available: {e}[/dim]")


def show_help():
    """Show help information."""
    table = Table(title="Commands", show_header=True, header_style="bold cyan")
    table.add_column("Command", style="green")
    table.add_column("Description")

    table.add_row("/help", "Show this help")
    table.add_row("/vars", "List available prompt variables")
    table.add_row("/enhance <prompt>", "Enhance a prompt without generating")
    table.add_row("/seed <number>", "Set seed for next generation")
    table.add_row("/size <WxH>", "Set output size (e.g., 1024x1024)")
    table.add_row("/gpu", "Show GPU memory status")
    table.add_row("/unload", "Unload models to free GPU memory")
    table.add_row("/version", "Show version information")
    table.add_row("/changelog", "Show changelog")
    table.add_row("/quit or /q", "Exit")

    console.print(table)
    console.print("\n[dim]Tips:[/dim]")
    console.print("[dim]• Use __variable__ syntax for random substitution (e.g., __animal__)[/dim]")
    console.print("[dim]• Missing variables are auto-generated by the local LLM[/dim]")
    console.print("[dim]• Add '>' to enhance prompt (e.g., 'a cat > make it magical')[/dim]")
    console.print("[dim]• Add batch params with ':' (e.g., 'prompt : x10,h832,w1216')[/dim]")
    console.print("[dim]  x<N>=count, h<N>=height, w<N>=width (all optional)[/dim]")


def interactive_loop():
    """Main interactive loop with autocomplete support."""
    prompt_vars = load_prompt_vars()
    current_seed = None
    current_size = (1024, 1024)
    last_prompt = ""  # Keep track of last prompt for persistence
    
    show_help()
    console.line()
    
    # Build autocomplete suggestions
    autocomplete_suggestions = get_autocomplete_suggestions(prompt_vars)
    completer = PromptCompleter(autocomplete_suggestions)
    
    while True:
        try:
            # Use questionary with autocomplete and default to last prompt
            user_input = questionary.text(
                ">>> ",
                default=last_prompt,
                completer=completer,
            ).ask()
            
            if user_input is None:  # User pressed Ctrl+C
                continue
                
            user_input = user_input.strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.startswith("/"):
                cmd_parts = user_input.split(" ", 1)
                cmd = cmd_parts[0].lower()
                args = cmd_parts[1] if len(cmd_parts) > 1 else ""
                
                if cmd in ["/quit", "/q", "/exit"]:
                    console.print("[dim]Goodbye![/dim]")
                    break
                    
                elif cmd == "/help":
                    show_help()
                    
                elif cmd == "/vars":
                    if prompt_vars:
                        table = Table(title="Prompt Variables")
                        table.add_column("Variable", style="cyan")
                        table.add_column("Values", style="dim")
                        for var_id, var in prompt_vars.items():
                            preview = ", ".join(var.values[:5])
                            if len(var.values) > 5:
                                preview += f"... (+{len(var.values)-5} more)"
                            table.add_row(var_id, preview)
                        console.print(table)
                    else:
                        console.print("[yellow]No prompt variables found[/yellow]")
                    
                elif cmd == "/enhance":
                    if args:
                        enhanced = enhance_prompt_local(args)
                        console.print(Panel(enhanced, title="Enhanced Prompt", border_style="green"))
                    else:
                        console.print("[yellow]Usage: /enhance <prompt>[/yellow]")
                    
                elif cmd == "/seed":
                    if args:
                        try:
                            current_seed = int(args)
                            console.print(f"[green]Seed set to: {current_seed}[/green]")
                        except ValueError:
                            console.print("[red]Invalid seed (must be a number)[/red]")
                    else:
                        current_seed = None
                        console.print("[dim]Seed reset to random[/dim]")
                    
                elif cmd == "/size":
                    if args:
                        try:
                            w, h = args.lower().split("x")
                            current_size = (int(w), int(h))
                            console.print(f"[green]Size set to: {current_size[0]}x{current_size[1]}[/green]")
                        except:
                            console.print("[red]Invalid size format. Use: /size 1024x1024[/red]")
                    else:
                        console.print(f"[dim]Current size: {current_size[0]}x{current_size[1]}[/dim]")
                    
                elif cmd == "/gpu":
                    print_gpu_status()
                    
                elif cmd == "/unload":
                    from z_explorer.image_generator import unload_pipeline
                    from z_explorer.llm_provider import unload_model
                    unload_pipeline()
                    unload_model()
                    console.print("[green]✓ Models unloaded[/green]")
                    print_gpu_status()

                elif cmd == "/version":
                    console.print(f"[bold cyan]Z-Explorer[/bold cyan] v{__version__}")
                    console.print("[dim]AI Image Generation Without the UI Tax[/dim]")
                    console.print("[dim]https://github.com/pyros-projects/z-Explorer[/dim]")

                elif cmd == "/changelog":
                    changelog_path = get_changelog_path()
                    if changelog_path:
                        from rich.markdown import Markdown
                        changelog_content = changelog_path.read_text(encoding="utf-8")
                        md = Markdown(changelog_content)
                        console.print(md)
                    else:
                        console.print("[yellow]Changelog not found. Visit:[/yellow]")
                        console.print("[dim]https://github.com/pyros-projects/z-Explorer/blob/main/CHANGELOG.md[/dim]")

                else:
                    console.print(f"[red]Unknown command: {cmd}[/red]")
                    console.print("[dim]Type /help for available commands[/dim]")
                
                continue
            
            # Parse batch parameters (: x10,h832,w1216)
            prompt_input, batch_params = parse_batch_params(user_input)
            count = batch_params["count"]
            img_height = batch_params["height"]
            img_width = batch_params["width"]
            
            if count > 1 or img_height != 1024 or img_width != 1024:
                console.print(f"[dim]Batch: {count} image(s) @ {img_width}x{img_height}[/dim]")
            
            # === PHASE 1: Generate all prompts (LLM phase) ===
            console.print(f"\n[bold cyan]📝 Phase 1: Generating {count} prompt(s)...[/bold cyan]")
            
            generated_prompts = []
            for i in range(count):
                if count > 1:
                    console.print(f"[dim]Generating prompt {i+1}/{count}...[/dim]")
                
                # Check for enhancement instruction
                if ">" in prompt_input:
                    parts = prompt_input.split(">", 1)
                    base_prompt = parts[0].strip()
                    instruction = parts[1].strip() if len(parts) > 1 else ""
                    
                    # Substitute variables (each iteration gets fresh random values)
                    base_prompt = substitute_vars_local(base_prompt, prompt_vars)
                    
                    # Enhance
                    from z_explorer.llm_provider import enhance_prompt as _enhance
                    if count == 1:
                        console.print(f"[cyan]🤖 Enhancing with instruction: {instruction}[/cyan]")
                    
                    full_prompt = f"{base_prompt}\n\nEnhancement instruction: {instruction}" if instruction else base_prompt
                    prompt = _enhance(full_prompt, instruction)
                    
                    if count == 1:
                        console.print(Panel(prompt, title="Enhanced Prompt", border_style="cyan"))
                else:
                    # Just substitute variables
                    prompt = substitute_vars_local(prompt_input, prompt_vars)
                
                generated_prompts.append(prompt)
                
                # Reload prompt vars in case new ones were generated
                prompt_vars = load_prompt_vars()
            
            # Update completer with any new variables
            autocomplete_suggestions = get_autocomplete_suggestions(prompt_vars)
            completer = PromptCompleter(autocomplete_suggestions)
            
            # Unload LLM before image generation to free memory
            if count > 1:
                from z_explorer.llm_provider import unload_model
                console.print("[dim]Unloading LLM before image generation...[/dim]")
                unload_model()
            
            # === PHASE 2: Generate all images (Image model phase) ===
            console.print(f"\n[bold magenta]🎨 Phase 2: Generating {count} image(s)...[/bold magenta]")
            
            generated_paths = []
            for i, prompt in enumerate(generated_prompts):
                console.print(f"\n[cyan]Image {i+1}/{count}[/cyan]")
                console.print(Panel(prompt, title=f"Prompt {i+1}", border_style="green"))
                
                image, path = generate_image_local(
                    prompt, 
                    seed=current_seed,
                    width=img_width,
                    height=img_height
                )
                generated_paths.append(path)
                
                # Show preview for each image
                display_image_preview(path)
            
            # Keep the original prompt for next iteration
            last_prompt = user_input
            
            # Reset seed after use (unless user explicitly set it)
            if current_seed is not None:
                console.print(f"[dim]Used seed: {current_seed}[/dim]")
                current_seed = None
            
            # Summary
            if count > 1:
                console.print(f"\n[bold green]✓ Generated {count} images![/bold green]")
                for i, p in enumerate(generated_paths):
                    console.print(f"  [dim]{i+1}. {p}[/dim]")
            
            console.line()
            
        except KeyboardInterrupt:
            console.print("\n[dim]Interrupted. Type /quit to exit.[/dim]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")


DEFAULT_PORT = 8345


def _check_dependencies() -> bool:
    """Check if required packages are available."""
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
        import diffusers  # noqa: F401
        return True
    except ImportError:
        return False


def _wait_for_server(port: int, timeout: float = 5.0) -> bool:
    """Wait for server to be ready."""
    import time
    import httpx
    
    start = time.time()
    while time.time() - start < timeout:
        try:
            response = httpx.get(f"http://127.0.0.1:{port}/api/health", timeout=0.5)
            if response.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.1)
    return False


def _ensure_gui_built() -> bool:
    """Ensure the GUI is built, building it if necessary.

    Returns:
        True if GUI is ready, False if build failed
    """
    import subprocess

    # Check both possible locations for GUI
    module_dir = Path(__file__).parent
    gui_locations = [
        module_dir / "gui",  # Installed package location
        module_dir.parent.parent / "gui",  # Dev mode (legacy)
    ]

    for gui_dir in gui_locations:
        dist_dir = gui_dir / "dist"
        package_json = gui_dir / "package.json"

        # If dist exists, we're good
        if dist_dir.exists() and (dist_dir / "index.html").exists():
            return True

        # If package.json exists but no dist, we need to build
        if package_json.exists() and not dist_dir.exists():
            console.print(f"[yellow]GUI not built. Building from {gui_dir}...[/yellow]")

            try:
                # Check if node_modules exists, if not run npm install
                node_modules = gui_dir / "node_modules"
                if not node_modules.exists():
                    console.print("[dim]Installing npm dependencies...[/dim]")
                    result = subprocess.run(
                        ["npm", "install"],
                        cwd=str(gui_dir),
                        capture_output=True,
                        text=True,
                    )
                    if result.returncode != 0:
                        console.print(f"[red]npm install failed:[/red]\n{result.stderr}")
                        return False

                # Build the GUI
                console.print("[dim]Building GUI (npm run build)...[/dim]")
                result = subprocess.run(
                    ["npm", "run", "build"],
                    cwd=str(gui_dir),
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    console.print(f"[red]npm run build failed:[/red]\n{result.stderr}")
                    return False

                console.print("[green]✓ GUI built successfully[/green]")
                return True

            except FileNotFoundError:
                console.print("[red]npm not found. Please install Node.js to build the GUI.[/red]")
                return False
            except Exception as e:
                console.print(f"[red]Failed to build GUI: {e}[/red]")
                return False

    # No GUI source found - this is fine for published packages
    # The dist should be bundled in the wheel
    return True


def start_web_mode(port: int, host: str = "127.0.0.1"):
    """Start server and open browser.

    Args:
        port: Port for the API server
        host: Host to bind to (default: 127.0.0.1)
    """
    import threading
    import webbrowser
    import time

    # Ensure GUI is built (for dev mode)
    if not _ensure_gui_built():
        console.print("[yellow]Warning: GUI may not be available[/yellow]")

    from z_explorer.server import serve

    display_host = "localhost" if host == "127.0.0.1" else host
    console.print(f"[cyan]🚀 Starting Z-Explorer on http://{display_host}:{port}[/cyan]")

    if host == "0.0.0.0":
        console.print("[yellow]⚠ Server bound to all interfaces (0.0.0.0) - accessible from network[/yellow]")
    
    # Start server in background thread
    server_thread = threading.Thread(
        target=serve,
        kwargs={"host": host, "port": port},
        daemon=True,
    )
    server_thread.start()
    
    # Wait for server to be ready (always check localhost)
    console.print("[dim]Waiting for server...[/dim]")
    if not _wait_for_server(port):
        console.print("[red]❌ Server failed to start[/red]")
        return
    
    console.print("[green]✓ Server ready[/green]")
    console.print("[cyan]🌐 Opening in browser...[/cyan]")
    webbrowser.open(f"http://127.0.0.1:{port}")
    
    console.print("[dim]Press Ctrl+C to stop the server[/dim]")
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[dim]Shutting down...[/dim]")


def start_cli_mode():
    """Start the interactive CLI mode."""
    print_banner()
    print_gpu_status()
    console.line()
    
    # Check for required packages
    if not _check_dependencies():
        console.print(Panel(
            f"[red]Missing dependencies![/red]\n\n"
            f"Install with:\n"
            f"[cyan]uv sync[/cyan]\n\n"
            f"Required packages:\n"
            f"[dim]torch, transformers, diffusers[/dim]",
            title="Installation Required",
            border_style="red"
        ))
        sys.exit(1)
    
    console.print("[green]✓ All dependencies available[/green]")
    console.line()
    
    interactive_loop()


def main():
    """Main entry point for Z-Explorer.

    Modes:
        (default)   Web mode - starts server and opens browser
        --cli       CLI mode - interactive terminal (expert users)
        --setup     Run model configuration wizard
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Z-Explorer: Local AI Image Generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  z-explorer                Start web UI (default)
  z-explorer --cli          Start CLI mode (expert)
  z-explorer --setup        Configure model sources (interactive)
  z-explorer --quick-setup  Auto-configure with defaults (non-interactive, for Docker)
  z-explorer --show-config  Show current configuration
  z-explorer --port 9000    Use custom port
  z-explorer --host 0.0.0.0 Bind to all interfaces (network accessible)
        """,
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Start in CLI mode (expert users)",
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Run model configuration wizard",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Server port (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1, use 0.0.0.0 for network access)",
    )
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Show current model configuration and exit",
    )
    parser.add_argument(
        "--quick-setup",
        action="store_true",
        help="Non-interactive setup with Quick Start defaults (for Docker/scripts)",
    )

    args = parser.parse_args()

    # Show config and exit if requested
    if args.show_config:
        from z_explorer.model_config import print_config
        print_config()
        return

    # Non-interactive quick setup (for Docker, scripts, CI)
    if args.quick_setup:
        from z_explorer.model_config import save_config, LoadingMode, LLMMode, DEFAULT_LLM_REPO_QUANTIZED, is_configured
        if is_configured():
            console.print("[dim]Already configured, skipping quick-setup[/dim]")
        else:
            save_config(
                image_mode=LoadingMode.SDNQ,
                llm_mode=LLMMode.HF_DOWNLOAD,
                llm_repo=DEFAULT_LLM_REPO_QUANTIZED,
            )
            console.print("[green]✓ Quick Start configuration saved (SDNQ + quantized LLM, ~12GB VRAM)[/green]")
        # Continue to start the app (don't return)

    # Run setup wizard if requested
    if args.setup:
        from z_explorer.setup_wizard import run_wizard
        run_wizard()
        return

    # Check for first-run and trigger wizard if needed
    from z_explorer.model_config import is_configured
    if not is_configured():
        console.print("[yellow]No model configuration found![/yellow]")
        console.print("Run [cyan]z-explorer --setup[/cyan] to configure your models.\n")

        # Ask if they want to run setup now
        run_now = questionary.confirm(
            "Would you like to run the setup wizard now?",
            default=True,
        ).ask()

        if run_now:
            from z_explorer.setup_wizard import run_wizard
            if not run_wizard():
                return  # Wizard cancelled
            console.print()  # Blank line before starting
        else:
            # Use SDNQ as default (12GB VRAM friendly) instead of full HF_DOWNLOAD
            from z_explorer.model_config import save_config, LoadingMode, LLMMode, DEFAULT_LLM_REPO_QUANTIZED
            save_config(
                image_mode=LoadingMode.SDNQ,
                llm_mode=LLMMode.HF_DOWNLOAD,
                llm_repo=DEFAULT_LLM_REPO_QUANTIZED,
            )
            console.print("[dim]Using Quick Start defaults (SDNQ + quantized LLM, ~12GB VRAM)[/dim]\n")

    if args.cli:
        # Expert CLI mode
        start_cli_mode()
    else:
        # Default: Web mode (server + browser)
        start_web_mode(args.port, args.host)


if __name__ == "__main__":
    main()

