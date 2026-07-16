# -*- coding: utf-8 -*-
from __future__ import annotations

from src.models import LiftGroup, ProjectInfo, Questionnaire


def test_questionnaire_defaults():
    questionnaire = Questionnaire()
    assert isinstance(questionnaire.project, ProjectInfo)
    assert questionnaire.lift_groups == []


def test_legacy_preparer_surname_is_normalized():
    project = ProjectInfo(prepared_by="Другалев")

    assert project.prepared_by == "Другалёв"


def test_lift_group_accepts_optional_empty_fields():
    group = LiftGroup(lift_name="Лифт 1")
    assert group.lift_name == "Лифт 1"
    assert group.door_model == "NBSL"

