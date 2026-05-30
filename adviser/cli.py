"""CLI entrypoints for Adviser."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import typer
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
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
PROMPT_STYLE = Style.from_dict({"prompt": "bold ansicyan"})

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
    session = PromptSession()

    header = Panel.fit(
        f"[bold white on cyan] ADVISER v{__version__} [/bold white on cyan]\n"
        f"Loaded chunks: {stats.get('total_chunks', 0)}\n"
        f"Primary provider: {client.primary_provider_name}\n"
        "Type exit to quit | clear to reset | sources to list files",
        border_style="cyan",
    )
    console.print(header)

    while True:
        query = session.prompt(HTML("<prompt>User ❯ </prompt>"), style=PROMPT_STYLE)
        if not query.strip():
            continue
        command = query.strip().lower()
        if command in {"exit", "quit"}:
            break
        if command == "clear":
            memory.clear()
            console.print("[cyan]Conversation memory cleared.[/cyan]")
            continue
        if command == "sources":
            _print_sources(stats.get("sources", []))
            continue

        hits = retriever.search(query, settings.TOP_K_RETRIEVE)
        if debug:
            _print_debug_hits(hits)
        context = retriever.format_context(hits, max_chars=settings.MAX_CONTEXT_TOKENS * 2)
        messages = memory.get_messages(settings.ADVISER_PERSONA, query, context)
        console.print("[bold green]Assistant ❯[/bold green] ", end="")
        answer = client.chat(messages)
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
