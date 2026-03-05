from __future__ import annotations

import json
from pathlib import Path

from .models import AppConfig


def ProjectRoot() -> Path:
    return Path(__file__).resolve().parents[2]


def VarDir() -> Path:
    return ProjectRoot() / "var"


def ConfigPath() -> Path:
    return VarDir() / "config.json"


class ConfigLoader:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or ConfigPath()

    def Load(self) -> AppConfig:
        if not self.path.exists():
            self.CreateDefaultConfig()
            raise FileNotFoundError(
                f"Created default config at {self.path}. "
                "Update it, then run again."
            )

        with self.path.open("r", encoding="utf-8") as handle:
            jsonData = json.load(handle)

        return AppConfig.model_validate(jsonData)

    def CreateDefaultConfig(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        defaultConfig = AppConfig.Template().model_dump(mode="json")
        self.path.write_text(json.dumps(defaultConfig, indent=2), encoding="utf-8")
