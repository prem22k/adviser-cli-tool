"""CLI entrypoints for Adviser."""

import typer

app = typer.Typer(help="Adviser CLI")


@app.callback(invoke_without_command=True)
def main() -> None:
    """Placeholder callback until full CLI wiring is implemented."""
