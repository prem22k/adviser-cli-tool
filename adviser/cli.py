"""CLI entrypoints for Adviser."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import typer
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from adviser import __version__
from adviser.config import settings
from adviser.config.profiles import Profile, ProfileManager
from adviser.config.snapshots import SnapshotManager
from adviser.digest.engine import main as digest_main
from adviser.digest.planner import estimate_plan
from adviser.ingestion.ingest import ingest as run_ingest
from adviser.llm.client import LLMClient
from adviser.llm.memory import ConversationMemory
from adviser.retrieval.retriever import HybridRetriever
from adviser.hardware import detect

console = Console()
PROMPT_STYLE = Style.from_dict({
    "prompt": "bold royalblue",
    "prefix": "bold cyan",
    "text": "white",
    "auto-suggest": "dim ansigray",
    "status-bar": "ansigray",
    "status-provider": "ansigray",
})

app = typer.Typer(help="Adviser CLI", invoke_without_command=True, no_args_is_help=False)
snapshot_app = typer.Typer(help="Backup and restore vector database snapshots.")
profile_app = typer.Typer(help="Manage Adviser profiles.")
sync_app = typer.Typer(help="Reserved for future sync workflows.")

app.add_typer(snapshot_app, name="snapshot")
app.add_typer(profile_app, name="profile")
app.add_typer(sync_app, name="sync")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    profile: str | None = typer.Option(None, "--profile", help="Profile to use for the chat session."),
    debug: bool = typer.Option(False, "--debug", help="Show retrieval debug panels."),
) -> None:
    if ctx.invoked_subcommand is None:
        run_chat(profile_name=profile, debug=debug)


@app.command("chat")
def chat_command(
    profile: str | None = typer.Option(None, "--profile", help="Profile to use for this session."),
    debug: bool = typer.Option(False, "--debug", help="Show retrieval debug panels."),
) -> None:
    run_chat(profile_name=profile, debug=debug)


@app.command("ingest")
def ingest_command(force: bool = typer.Option(False, "--force", "-f", help="Rebuild the adviser collection.")) -> None:
    _activate_runtime_profile(None)
    run_ingest(force_reload=force)


@app.command("mcp")
def mcp_command(
    profile: str | None = typer.Option(None, "--profile", help="Profile to load for the MCP server session.")
) -> None:
    """Launch the Model Context Protocol (MCP) server for IDE integration."""
    _activate_runtime_profile(profile)
    from adviser.mcp.server import start_server
    start_server(profile_name=profile)


@app.command("mcp-install")
def mcp_install_command(
    profile: str | None = typer.Option(None, "--profile", help="Profile to configure for the MCP server session.")
) -> None:
    """Automatically register this MCP server with your Cursor IDE and Claude Code."""
    import os
    import sys
    import json
    import shutil
    from pathlib import Path
    
    # 1. Resolve absolute path of adviser executable
    executable_path = shutil.which("adviser")
    if not executable_path:
        # Fallback to the current script's parent venv path
        executable_path = str(Path(sys.executable).parent / "adviser")
        if not Path(executable_path).exists():
            # Fallback to absolute file location of the python running cli.py
            executable_path = str(Path(sys.argv[0]).resolve())
            
    resolved_path = str(Path(executable_path).resolve())
    console.print(f"[cyan]Resolved adviser executable path:[/cyan] [bold]{resolved_path}[/bold]")
    
    # Build the MCP server configuration
    mcp_config = {
        "command": resolved_path,
        "args": ["mcp"] + (["--profile", profile] if profile else []),
        "env": {}
    }
    
    # Add any active API keys from the current environment to the MCP config env
    for key in ["OPENAI_API_KEY", "GEMINI_API_KEY", "GROQ_API_KEY"]:
        val = os.getenv(key)
        if val:
            mcp_config["env"][key] = val
            
    # Configure Cursor, Claude Desktop, Windsurf & Cline
    system = sys.platform
    config_options = {}

    # 1. Cursor Global
    cursor_global_paths = [Path.home() / ".cursor/mcp.json"]
    if system == "darwin":
        cursor_global_paths.append(Path.home() / "Library/Application Support/Cursor/User/globalStorage/cursor.chat.mcp/config.json")
    elif system == "win32":
        if os.getenv("APPDATA"):
            cursor_global_paths.append(Path(os.getenv("APPDATA")) / "Cursor/User/globalStorage/cursor.chat.mcp/config.json")
    else:
        cursor_global_paths.append(Path.home() / ".config/Cursor/User/globalStorage/cursor.chat.mcp/config.json")
        cursor_global_paths.append(Path.home() / ".config/cursor/User/globalStorage/cursor.chat.mcp/config.json")
    config_options["1"] = (cursor_global_paths, "Cursor (Global)")

    # 2. Cursor Project-Local
    config_options["2"] = ([Path(".cursor/mcp.json")], "Cursor (Project-Local)")

    # 3. Claude Desktop
    claude_paths = []
    if system == "darwin":
        claude_paths.append(Path.home() / "Library/Application Support/Claude/claude_desktop_config.json")
    elif system == "win32":
        if os.getenv("APPDATA"):
            claude_paths.append(Path(os.getenv("APPDATA")) / "Claude/claude_desktop_config.json")
    else:
        claude_paths.append(Path.home() / ".config/Claude/claude_desktop_config.json")
    config_options["3"] = (claude_paths, "Claude Desktop")

    # 4. Windsurf Global
    config_options["4"] = ([Path.home() / ".codeium/windsurf/mcp_config.json"], "Windsurf (Global)")

    # 5. Cline (VS Code Extension)
    cline_paths = []
    if system == "darwin":
        cline_paths.append(Path.home() / "Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json")
    elif system == "win32":
        if os.getenv("APPDATA"):
            cline_paths.append(Path(os.getenv("APPDATA")) / "Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json")
    else:
        cline_paths.append(Path.home() / ".config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json")
    config_options["5"] = (cline_paths, "Cline (VS Code Extension)")

    # Prompt user interactively using modern arrow-key TUI dialog if in interactive terminal
    selected_options = []
    if sys.stdin.isatty():
        from prompt_toolkit.shortcuts import checkboxlist_dialog
        
        selected_options = checkboxlist_dialog(
            title="Adviser MCP Auto-Installer",
            text=(
                "Use ARROW KEYS to navigate options.\n"
                "Press SPACE to select/deselect an IDE.\n"
                "Press TAB to switch focus to OK/Cancel buttons.\n"
                "Press ENTER to submit.\n\n"
                "Which IDEs/Clients do you want to configure Adviser MCP for?"
            ),
            values=[
                ("1", "Cursor (Global)"),
                ("2", "Cursor (Project-Local)"),
                ("3", "Claude Desktop"),
                ("4", "Windsurf (Global)"),
                ("5", "Cline (VS Code Extension)"),
                ("6", "All of the above")
            ]
        ).run()
        
        if not selected_options:
            console.print("[yellow]Installation cancelled by user.[/yellow]")
            return
            
        if "6" in selected_options:
            selected_options = ["1", "2", "3", "4", "5"]
    else:
        # Fallback for piped / non-interactive automated installs - configure all by default
        selected_options = ["1", "2", "3", "4", "5"]

    if not selected_options:
        console.print("[yellow]No IDEs selected. Exiting.[/yellow]")
        return

    ide_configured = False
    for opt in selected_options:
        paths, label = config_options[opt]
        for target_path in paths:
            try:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                data = {"mcpServers": {}}
                if target_path.exists():
                    try:
                        data = json.loads(target_path.read_text(encoding="utf-8"))
                    except Exception:
                        pass
                
                if "mcpServers" not in data:
                    data["mcpServers"] = {}
                
                # Apply Cline parameters if needed
                mcp_server_entry = dict(mcp_config)
                if label == "Cline (VS Code Extension)":
                    mcp_server_entry["disabled"] = False
                    mcp_server_entry["autoApprove"] = []
                    
                data["mcpServers"]["adviser-mcp"] = mcp_server_entry
                target_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
                console.print(f"[green]✓ Successfully registered with {label} at:[/green] [dim]{target_path}[/dim]")
                ide_configured = True
            except Exception as exc:
                console.print(f"[red]✖ Failed to configure {label} at {target_path}:[/red] {exc}")

    # Output Claude Code instructions
    console.print("\n[bold cyan]=== Claude Code MCP Integration ===[/bold cyan]")
    claude_cmd = f"claude mcp add adviser-mcp -- {resolved_path} mcp" + (f" --profile {profile}" if profile else "")
    console.print(f"To register with Claude Code, copy and run this command in your terminal:")
    console.print(f"\n  [bold green]{claude_cmd}[/bold green]\n")
    
    if ide_configured:
        console.print("[bold green]✔ MCP Server configured successfully for selected IDEs![/bold green]")
    else:
        console.print("[yellow]Automatic IDE configuration skipped. Please add the server manually in your settings.[/yellow]")


@app.command("digest")
def digest_command(plan: bool = typer.Option(False, "--plan", "-p", help="Estimate a digest plan only.")) -> None:
    profile = _activate_runtime_profile(None)
    providers = _selected_providers(profile)
    if plan:
        estimate_plan(providers=providers)
        return
    try:
        settings.validate()
    except (RuntimeError, FileNotFoundError) as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        console.print("Set your keys in `.env` or run `adviser init` to create a profile.")
        raise typer.Exit(code=1) from exc
    digest_main(providers=providers)


@app.command("init")
def init_command() -> None:
    console.print(Panel.fit("Adviser Setup Wizard", border_style="cyan", title="Setup"))
    hp = detect()
    gpu_desc = hp.gpu_name if hp.gpu_name else "not detected"
    console.print(
        Panel.fit(
            f"CPU cores: {hp.cpu_cores}\nRAM: {hp.ram_gb} GB\nGPU: {gpu_desc}\nHardware Tier: {hp.tier}",
            border_style="cyan",
            title="Hardware Profile",
        )
    )

    name = Prompt.ask("Profile name", default="default")
    default_data_path = str((Path.home() / "Documents" / "corpus").expanduser().resolve())
    data_path = Prompt.ask("Absolute path to your document folder", default=default_data_path)
    persona = Prompt.ask("Personal instructions", default=settings.ADVISER_PERSONA)
    enable_cloud = Confirm.ask("Enable cloud APIs (Groq/Gemini)?", default=True)
    enable_ollama = Confirm.ask("Enable Ollama (local)?", default=True)

    gemini_model = "gemini-3.5-flash"
    groq_model = "llama-3.3-70b-versatile"

    providers: list[str] = []
    if enable_cloud:
        for provider in ("gemini", "groq"):
            if provider not in providers:
                providers.append(provider)

        # Prompt for Gemini Model Selection
        console.print("\n[bold cyan]Choose your Google Gemini model:[/bold cyan]")
        console.print("1. [bold green]gemini-3.5-flash[/bold green] (Most intelligent Flash, sustained fast performance - Recommended default)")
        console.print("2. [bold white]gemini-3.1-pro-preview[/bold white] (Advanced reasoning and agentic problem solving)")
        console.print("3. [bold white]gemini-3.1-flash-lite[/bold white] (Frontier performance at a fraction of the cost)")
        gemini_choice = Prompt.ask("Select option [1/2/3]", default="1")
        if gemini_choice == "2":
            gemini_model = "gemini-3.1-pro-preview"
        elif gemini_choice == "3":
            gemini_model = "gemini-3.1-flash-lite"

        # Prompt for Groq Model Selection
        console.print("\n[bold cyan]Choose your Groq cloud model:[/bold cyan]")
        console.print("1. [bold green]llama-3.3-70b-versatile[/bold green] (Versatile flagship, balanced reasoning - Recommended default)")
        console.print("2. [bold white]llama-3.1-8b-instant[/bold white] (High speed, lightweight, token saving)")
        console.print("3. [bold white]openai/gpt-oss-120b[/bold white] (Flagship open-weights, advanced tool use & reasoning)")
        console.print("4. [bold white]openai/gpt-oss-20b[/bold white] (Ultra-fast 1000 t/s, budget-friendly)")
        groq_choice = Prompt.ask("Select option [1/2/3/4]", default="1")
        if groq_choice == "2":
            groq_model = "llama-3.1-8b-instant"
        elif groq_choice == "3":
            groq_model = "openai/gpt-oss-120b"
        elif groq_choice == "4":
            groq_model = "openai/gpt-oss-20b"

    if enable_ollama:
        providers.append("ollama")

        # Check if Ollama is installed
        ollama_installed = bool(shutil.which("ollama"))
        if not ollama_installed:
            console.print(
                Panel(
                    "[yellow]Warning: Ollama CLI is not detected on your system.[/yellow]\n\n"
                    "To install Ollama for local LLM support:\n"
                    "• Linux/macOS: [bold cyan]curl -fsSL https://ollama.com/install.sh | sh[/bold cyan]\n"
                    "• Windows/Other: Visit [bold cyan]https://ollama.com[/bold cyan] to download the installer.",
                    title="[bold yellow]Ollama Not Found[/bold yellow]",
                    border_style="yellow"
                )
            )

        # Recommend local models based on hardware auto-detection
        general_models = hp.recommended_llms.get("general", [])
        if general_models:
            recommended_model = general_models[-1]
            console.print(
                Panel(
                    f"Based on your [bold cyan]{hp.tier}[/bold cyan] hardware tier, we recommend running:\n"
                    f"👉 [bold green]ollama pull {recommended_model}[/bold green]\n\n"
                    f"To use this model with Adviser, configure it in your terminal before running the chat:\n"
                    f"[bold cyan]export OLLAMA_MODEL={recommended_model}[/bold cyan]\n\n"
                    f"Other models that fit your memory: {', '.join(general_models[:-1])}",
                    title="[bold green]Local LLM Recommendation[/bold green]",
                    border_style="green"
                )
            )

    db_path = str((Path.home() / ".local" / "share" / "adviser" / name / "chroma_db").expanduser())
    profile = ProfileManager.create(
        name=name,
        persona=persona,
        data_path=str(Path(data_path).expanduser()),
        db_path=db_path,
        providers=providers,
        gemini_model=gemini_model,
        groq_model=groq_model,
    )
    ProfileManager.set_active(profile.name)
    console.print(
        Panel.fit(
            "1. Run `adviser ingest` to parse documents.\n"
            "2. Run `adviser chat` to start the assistant!",
            title="Next Steps",
            border_style="cyan",
        )
    )


@snapshot_app.command("save")
def snapshot_save(path: Path = typer.Argument(..., help="Output .tar.gz path.")) -> None:
    _activate_runtime_profile(None)
    SnapshotManager.save(path)


@snapshot_app.command("load")
def snapshot_load(path: Path = typer.Argument(..., help="Input .tar.gz path.")) -> None:
    _activate_runtime_profile(None)
    SnapshotManager.load(path)


@profile_app.command("list")
def profile_list() -> None:
    active = ProfileManager.get_active()
    table = Table(title="Profiles", expand=False)
    table.add_column("Active", style="green")
    table.add_column("Name", style="cyan")
    table.add_column("Document Path", style="white")
    for name in ProfileManager.list_profiles():
        profile = ProfileManager.load(name)
        marker = "[green]*[/green]" if active and active.name == name else ""
        table.add_row(marker, profile.name, profile.data_path)
    console.print(table)


@profile_app.command("select")
def profile_select(name: str = typer.Argument(..., help="Profile name to activate.")) -> None:
    ProfileManager.set_active(name)
    console.print(f"[cyan]Active profile:[/cyan] {name}")


@profile_app.command("create")
def profile_create(
    name: str = typer.Option(..., "--name", help="Profile name."),
    data_path: str = typer.Option(..., "--data-path", help="Document path."),
    persona: str = typer.Option(settings.ADVISER_PERSONA, "--persona", help="Custom adviser persona."),
) -> None:
    db_path = str((Path.home() / ".local" / "share" / "adviser" / name / "chroma_db").expanduser())
    providers = [provider.name for provider in settings.get_provider_chain()]
    profile = ProfileManager.create(
        name=name,
        persona=persona,
        data_path=str(Path(data_path).expanduser()),
        db_path=db_path,
        providers=providers,
    )
    console.print(f"[cyan]Profile created:[/cyan] {profile.name}")


@sync_app.callback(invoke_without_command=True)
def sync_placeholder() -> None:
    """Placeholder sync router for future extension."""


def run_chat(profile_name: str | None, debug: bool) -> None:
    profile = _activate_runtime_profile(profile_name)
    try:
        settings.validate()
    except (RuntimeError, FileNotFoundError) as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        console.print("Set your keys in `.env` or run `adviser init` to create a profile.")
        raise typer.Exit(code=1) from exc

    providers = _selected_providers(profile)
    if not providers:
        console.print("[bold red]No providers are enabled for the active profile.[/bold red]")
        raise typer.Exit(code=1)

    retriever = HybridRetriever()
    with console.status("[dim]Working...[/dim]", spinner="dots"):
        stats = retriever.load()
    client = LLMClient(providers=providers)
    memory = ConversationMemory(settings.CONVERSATION_WINDOW)
    session = PromptSession(
        style=PROMPT_STYLE,
        auto_suggest=AutoSuggestFromHistory(),
    )
    
    # Redesign prompt layout for inline status bar
    from prompt_toolkit.layout.containers import Window
    from prompt_toolkit.layout.controls import FormattedTextControl
    
    def _status_bar_text() -> list[tuple[str, str]]:
        left = "? for shortcuts | /exit to quit | /clear to reset"
        right = f"{client.primary_provider_name}"
        width = console.width
        padding = max(1, width - len(left) - len(right) - 1)
        return [
            ("class:status-bar", left),
            ("", " " * padding),
            ("class:status-provider", right),
        ]
        
    spacer = Window(height=1)
    status_control = FormattedTextControl(_status_bar_text)
    status_window = Window(content=status_control, height=1)
    
    session.layout.container.children.append(spacer)
    session.layout.container.children.append(status_window)

    # Get active user and home-contracted paths to match premium pop-os terminal design
    import getpass
    active_user = getpass.getuser()
    cwd = Path.cwd()
    home = Path.home()
    try:
        if cwd.is_relative_to(home):
            cwd_str = f"~/{cwd.relative_to(home)}"
        else:
            cwd_str = str(cwd)
    except (ValueError, AttributeError):
        cwd_str = str(cwd)

    # Clean, high-fidelity unique ASCII landing header for Adviser
    logo = (
        f"\n  [bold cyan]▄███▄[/bold cyan]\n"
        f" [bold cyan]█▀ ▲ ▀█[/bold cyan]      [bold white]Adviser CLI v{__version__}[/bold white]\n"
        f" [bold cyan]█ █▀█ █[/bold cyan]      [dim]{active_user} (Local RAG Brain)[/dim]\n"
        f" [bold cyan]▀█▄▄▄█▀[/bold cyan]      [dim]{client.primary_provider_name} (Medium / Medium Hardware)[/dim]\n"
        f"   [bold cyan]▀▀▀[/bold cyan]        [dim]{cwd_str}[/dim]\n"
    )
    console.print(logo)
    console.print("─" * console.width, style="dim")

    while True:
        # Print a vertical spacer line to visually isolate the input interaction space
        console.print()
        
        # Get user prompt session input
        try:
            query = session.prompt(
                [('class:prefix', '> '), ('class:prompt', 'User ❯ ')]
            )
        except (KeyboardInterrupt, EOFError):
            break
            
        if not query.strip():
            # Clear the active single input line and the vertical spacer line above it
            sys.stdout.write("\033[A\033[2K\033[A\033[2K")
            sys.stdout.flush()
            continue
            
        # 3. Clean up active prompt lines to preserve clean scrollback history
        # Move up 2 lines (prompt input line and the vertical spacer line above it) and clear them
        sys.stdout.write("\033[A\033[2K\033[A\033[2K")
        sys.stdout.flush()
        
        # Print clean, high-fidelity prompt line in conversation history
        # bounded cleanly by vertical spacer lines to keep the interaction visually isolated
        console.print()
        console.print(f"[bold royal_blue]> {query.strip()}[/bold royal_blue]")
        console.print()
        
        # 4. Parse slash commands
        query_strip = query.strip()
        if query_strip.startswith("/") or query_strip == "?":
            cmd_parts = query_strip.split()
            cmd = cmd_parts[0].lower()
            
            if cmd in {"/exit", "/quit", "/q"}:
                break
            elif cmd in {"/clear", "/c"}:
                memory.clear()
                console.print("[cyan]Conversation memory cleared.[/cyan]")
                console.print("─" * console.width, style="dim")
                continue
            elif cmd in {"/sources", "/s"}:
                _print_sources(stats.get("sources", []))
                console.print("─" * console.width, style="dim")
                continue
            elif cmd in {"/help", "?", "/h"}:
                console.print("\n[bold cyan]=== Adviser CLI Slash Commands ===[/bold cyan]")
                console.print("  [bold cyan]/q[/bold cyan], [bold cyan]/exit[/bold cyan], [bold cyan]/quit[/bold cyan]   Exit the interactive chat session")
                console.print("  [bold cyan]/c[/bold cyan], [bold cyan]/clear[/bold cyan]            Clear the conversational memory window")
                console.print("  [bold cyan]/s[/bold cyan], [bold cyan]/sources[/bold cyan]          List all indexed local source files")
                console.print("  [bold cyan]/h[/bold cyan], [bold cyan]/help[/bold cyan], [bold cyan]?[/bold cyan]             Show this command reference guide\n")
                console.print("─" * console.width, style="dim")
                continue
            else:
                console.print(f"[yellow]Unknown command: {cmd}. Type /help or ? for shortcuts.[/yellow]")
                console.print("─" * console.width, style="dim")
                continue

        # Transparently support legacy non-slash commands
        command = query_strip.lower()
        if command in {"exit", "quit"}:
            break
        if command == "clear":
            memory.clear()
            console.print("[cyan]Conversation memory cleared. Tip: Use slash command /clear or /c[/cyan]")
            console.print("─" * console.width, style="dim")
            continue
        if command == "sources":
            _print_sources(stats.get("sources", []))
            console.print("[dim]Tip: Use slash command /sources or /s[/dim]")
            console.print("─" * console.width, style="dim")
            continue

        # 6. Search database and execute local RAG generation loop
        hits = retriever.search(query, settings.TOP_K_RETRIEVE)
        if debug:
            _print_debug_hits(hits)
        context = retriever.format_context(hits, max_chars=settings.MAX_CONTEXT_TOKENS * 2)
        messages = memory.get_messages(settings.ADVISER_PERSONA, query, context)
        answer = client.chat(messages)
        console.print("─" * console.width, style="dim")
        memory.add("user", query)
        memory.add("assistant", answer)


def _activate_runtime_profile(profile_name: str | None) -> Profile | None:
    profile = ProfileManager.load(profile_name) if profile_name else ProfileManager.get_active()
    if profile:
        settings.apply_profile(profile)
    return profile


def _selected_providers(profile: Profile | None) -> list[settings.ProviderConfig]:
    providers = settings.get_provider_chain()
    if profile and profile.providers:
        providers = [provider for provider in providers if provider.name in profile.providers]
    return providers


def _print_sources(sources: list[str]) -> None:
    table = Table(title="Indexed Sources", expand=False)
    table.add_column("Source", style="cyan")
    for source in sources:
        table.add_row(source)
    console.print(table)


def _print_debug_hits(hits: list[dict[str, object]]) -> None:
    rows = []
    for hit in hits:
        snippet = str(hit["document"]).replace("\n", " ")[:120]
        source = Path(str(hit["metadata"].get("source", "unknown"))).name  # type: ignore[index]
        score = f"{float(hit.get('rrf_score', 0.0)):.4f}"
        rows.append(f"{score} | {source} | {snippet}")
    console.print(Panel("\n".join(rows) or "No hits", title="Retrieval Debug", border_style="dim"))


def _hardware_summary() -> dict[str, str | int]:
    ram_gb = "unknown"
    meminfo = Path("/proc/meminfo")
    if meminfo.exists():
        for line in meminfo.read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                kb = int(line.split()[1])
                ram_gb = str(round(kb / 1024 / 1024))
                break
    gpu = "detected" if shutil.which("nvidia-smi") else "not detected"
    return {"cpu_cores": os.cpu_count() or 1, "ram_gb": ram_gb, "gpu": gpu}
