"""Snapshot backup and restore helpers."""

from __future__ import annotations

import shutil
import tarfile
from pathlib import Path

from rich.console import Console

from adviser.config import settings

console = Console()


class SnapshotManager:
    @staticmethod
    def save(output_path: Path) -> Path:
        output_path = output_path.expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        settings.DB_PATH.mkdir(parents=True, exist_ok=True)
        with tarfile.open(output_path, "w:gz") as archive:
            archive.add(settings.DB_PATH, arcname=settings.DB_PATH.name)
        console.print(f"[cyan]Snapshot saved:[/cyan] {output_path}")
        return output_path

    @staticmethod
    def load(input_path: Path) -> Path:
        input_path = input_path.expanduser().resolve()
        if not input_path.exists():
            raise FileNotFoundError(f"Snapshot archive not found: {input_path}")

        target = settings.DB_PATH.expanduser().resolve()
        backup = target.with_name(f"{target.name}.bak")

        if target.exists():
            if backup.exists():
                if backup.is_dir():
                    shutil.rmtree(backup)
                else:
                    backup.unlink()
            target.rename(backup)

        target.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(input_path, "r:gz") as archive:
            archive.extractall(path=target.parent)
        console.print(f"[cyan]Snapshot restored:[/cyan] {input_path}")
        return target
