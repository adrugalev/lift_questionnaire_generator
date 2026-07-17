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


def test_lift_group_accepts_text_cabin_and_shaft_dimensions():
    group = LiftGroup(
        cabin_width_mm="РАСЧЁТНОЕ",
        cabin_depth_mm="МАКСИМАЛЬНОЕ",
        shaft_width_mm="МАКСИМАЛЬНОЕ",
        pit_depth_mm="МИНИМАЛЬНОЕ",
    )

    assert group.cabin_width_mm == "РАСЧЁТНОЕ"
    assert group.cabin_depth_mm == "МАКСИМАЛЬНОЕ"
    assert group.shaft_width_mm == "МАКСИМАЛЬНОЕ"
    assert group.pit_depth_mm == "МИНИМАЛЬНОЕ"


def test_lift_group_preserves_arbitrary_text_in_dimensions():
    group = LiftGroup(cabin_width_mm="ПО ПРОЕКТУ")

    assert group.cabin_width_mm == "ПО ПРОЕКТУ"


def test_lift_group_converts_numeric_dimension_text_to_integer():
    group = LiftGroup(
        cabin_width_mm="2700",
        cabin_depth_mm="1750.0",
        shaft_width_mm="1500,0",
    )

    assert group.cabin_width_mm == 2700
    assert group.cabin_depth_mm == 1750
    assert group.shaft_width_mm == 1500

