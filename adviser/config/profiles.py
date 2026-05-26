"""Profile persistence for Adviser."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path

from ruamel.yaml import YAML

YAML_ENGINE = YAML()
CONFIG_ROOT = Path.home() / ".config" / "adviser"
PROFILES_DIR = CONFIG_ROOT / "profiles"
ACTIVE_PROFILE_FILE = CONFIG_ROOT / "active"


@dataclass(slots=True)
class Profile:
    name: str
    persona: str
    data_path: str
    db_path: str
    chunk_size: int = 400
    chunk_overlap: int = 80
    top_k: int = 15
    providers: list[str] = field(default_factory=list)

    def save(self) -> Path:
        PROFILES_DIR.mkdir(parents=True, exist_ok=True)
        target = PROFILES_DIR / f"{self.name}.yaml"
        with target.open("w", encoding="utf-8") as handle:
            YAML_ENGINE.dump(asdict(self), handle)
        return target


class ProfileManager:
    @staticmethod
    def create(
        name: str,
        persona: str,
        data_path: str,
        db_path: str,
        providers: list[str],
    ) -> Profile:
        profile = Profile(
            name=name,
            persona=persona,
            data_path=data_path,
            db_path=db_path,
            providers=providers,
        )
        profile.save()
        return profile

    @staticmethod
    def load(name: str) -> Profile:
        target = PROFILES_DIR / f"{name}.yaml"
        if not target.exists():
            raise FileNotFoundError(f"Profile not found: {name}")
        with target.open("r", encoding="utf-8") as handle:
            data = YAML_ENGINE.load(handle) or {}
        return Profile(**data)

    @staticmethod
    def list_profiles() -> list[str]:
        if not PROFILES_DIR.exists():
            return []
        return sorted(path.stem for path in PROFILES_DIR.glob("*.yaml"))

    @staticmethod
    def set_active(name: str) -> None:
        if not (PROFILES_DIR / f"{name}.yaml").exists():
            raise FileNotFoundError(f"Profile not found: {name}")
        CONFIG_ROOT.mkdir(parents=True, exist_ok=True)
        ACTIVE_PROFILE_FILE.write_text(name, encoding="utf-8")

    @staticmethod
    def get_active() -> Profile | None:
        if not ACTIVE_PROFILE_FILE.exists():
            return None
        name = ACTIVE_PROFILE_FILE.read_text(encoding="utf-8").strip()
        if not name:
            return None
        try:
            return ProfileManager.load(name)
        except FileNotFoundError:
            return None

    @staticmethod
    def delete(name: str) -> None:
        target = PROFILES_DIR / f"{name}.yaml"
        if target.exists():
            target.unlink()
        if ACTIVE_PROFILE_FILE.exists() and ACTIVE_PROFILE_FILE.read_text(encoding="utf-8").strip() == name:
            ACTIVE_PROFILE_FILE.unlink()
