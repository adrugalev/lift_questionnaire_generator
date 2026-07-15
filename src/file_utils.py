# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


def safe_filename(value: str, default: str = "questionnaire") -> str:
    value = value.strip() or default
    value = re.sub(r"[^\wа-яА-ЯёЁ\u4e00-\u9fff.-]+", "_", value, flags=re.UNICODE)
    value = re.sub(r"_+", "_", value).strip("._")
    return value or default


def build_output_path(output_dir: str | Path, project_name: str | None) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = safe_filename(project_name or "questionnaire")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"{name}_{timestamp}.xlsx"

