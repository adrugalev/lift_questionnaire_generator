# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture()
def template_path(project_root: Path) -> Path:
    return project_root / "templates" / "questionnaire_template.xlsx"


@pytest.fixture()
def mapping_path(project_root: Path) -> Path:
    return project_root / "data" / "excel_mapping.json"

