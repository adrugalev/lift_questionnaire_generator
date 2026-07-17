# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import date
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


DimensionValue = Annotated[int, Field(gt=0)] | str


class ProjectInfo(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    project_name: Optional[str] = None
    customer: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    report_date: Optional[date] = None
    prepared_by: Optional[str] = None
    comment: Optional[str] = None

    @field_validator("prepared_by", mode="before")
    @classmethod
    def normalize_preparer_surname(cls, value):
        if isinstance(value, str) and value.strip() == "Другалев":
            return "Другалёв"
        return value


class LiftGroup(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    section: Optional[str] = None
    lift_name: Optional[str] = None
    quantity: Optional[int] = Field(default=None, gt=0)
    lift_type: Optional[str] = None
    capacity_kg: Optional[int] = Field(default=None, gt=0)
    speed_ms: Optional[float] = Field(default=None, gt=0)
    lifting_height_mm: Optional[int] = Field(default=None, gt=0)
    stops: Optional[int] = Field(default=None, gt=0)
    doors_count: Optional[int] = Field(default=None, gt=0)
    group_operation: Optional[str] = None
    button_marking: Optional[str] = None
    main_landing_floor: Optional[str] = None
    cabin_type: Optional[str] = None
    cabin_width_mm: Optional[DimensionValue] = None
    cabin_depth_mm: Optional[DimensionValue] = None
    cabin_height_mm: Optional[DimensionValue] = None
    side_wall_finish: Optional[str] = None
    rear_wall_finish: Optional[str] = None
    front_wall_finish: Optional[str] = None
    floor_finish: Optional[str] = None
    handrail_type: Optional[str] = None
    handrail_finish: Optional[str] = None
    ceiling_type: Optional[str] = None
    ceiling_finish: Optional[str] = None
    skirting_finish: Optional[str] = None
    mirror: Optional[str] = None
    door_opening_type: Optional[str] = None
    door_model: Optional[str] = "NBSL"
    cabin_door_finish: Optional[str] = None
    landing_door_width_mm: Optional[int] = Field(default=None, gt=0)
    landing_door_height_mm: Optional[int] = Field(default=None, gt=0)
    main_floor_landing_door_finish: Optional[str] = None
    other_floors_landing_door_finish: Optional[str] = None
    fire_resistance: Optional[str] = None
    firefighter_mode: Optional[str] = None
    cop_type: Optional[str] = None
    cop_finish: Optional[str] = None
    display_type: Optional[str] = None
    main_floor_lop_type: Optional[str] = None
    main_floor_lop_finish: Optional[str] = None
    other_floors_lop_type: Optional[str] = None
    other_floors_lop_finish: Optional[str] = None
    machine_room: Optional[str] = None
    shaft_material: Optional[str] = None
    shaft_width_mm: Optional[DimensionValue] = None
    shaft_depth_mm: Optional[DimensionValue] = None
    pit_depth_mm: Optional[DimensionValue] = None
    overhead_mm: Optional[DimensionValue] = None
    room_under_pit: Optional[str] = None
    seismic: Optional[str] = None
    additional_options: Optional[str] = None
    mgn_accessibility: Optional[str] = None
    price: Optional[str] = None
    containers_count: Optional[int] = Field(default=None, gt=0)

    @field_validator(
        "cabin_width_mm",
        "cabin_depth_mm",
        "cabin_height_mm",
        "shaft_width_mm",
        "shaft_depth_mm",
        "pit_depth_mm",
        "overhead_mm",
        mode="before",
    )
    @classmethod
    def normalize_dimension_value(cls, value):
        if not isinstance(value, str):
            return value
        text = value.strip()
        try:
            number = float(text.replace(",", "."))
        except ValueError:
            return text
        return int(number) if number.is_integer() else text


class Questionnaire(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    project: ProjectInfo = Field(default_factory=ProjectInfo)
    lift_groups: list[LiftGroup] = Field(default_factory=list)
