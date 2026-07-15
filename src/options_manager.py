# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class OptionsManager:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._options: dict[str, list[str]] = {}
        self.load()

    def load(self) -> dict[str, list[str]]:
        if not self.path.exists():
            self._options = {}
            return self._options
        with self.path.open("r", encoding="utf-8") as file:
            raw: dict[str, Any] = json.load(file)
        self._options = {key: list(map(str, values)) for key, values in raw.items()}
        return self._options

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(self._options, file, ensure_ascii=False, indent=2)

    def get(self, key: str) -> list[str]:
        return self._options.get(key, [])

    def add(self, key: str, value: str) -> None:
        value = value.strip()
        if not value:
            return
        values = self._options.setdefault(key, [])
        if value not in values:
            values.append(value)
            values.sort(key=str.lower)
            self.save()

    @property
    def options(self) -> dict[str, list[str]]:
        return self._options

