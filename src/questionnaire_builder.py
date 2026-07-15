# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from .models import LiftGroup, ProjectInfo, Questionnaire


def build_questionnaire(project_data: dict[str, Any], group_data: list[dict[str, Any]]) -> Questionnaire:
    project = ProjectInfo(**_drop_empty(project_data))
    groups = [LiftGroup(**_drop_empty(item)) for item in group_data]
    return Questionnaire(project=project, lift_groups=groups)


def merge_questionnaires(base: Questionnaire, extracted: Questionnaire | None) -> Questionnaire:
    if extracted is None:
        return base
    project_data = base.project.model_dump()
    extracted_project = extracted.project.model_dump()
    project_data.update({k: v for k, v in extracted_project.items() if project_data.get(k) in (None, "") and v})

    if not base.lift_groups and extracted.lift_groups:
        groups = extracted.lift_groups
    else:
        groups = base.lift_groups
    return Questionnaire(project=ProjectInfo(**project_data), lift_groups=groups)


def _drop_empty(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if value not in ("", None)}

