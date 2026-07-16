# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass

from .models import LiftGroup, Questionnaire


MGN_ACCESSIBILITY_WARNING = (
    "Для этой группы не забудьте выбрать панель управления и вызывные посты со шрифтом Брайля."
)


@dataclass(frozen=True)
class ValidationMessage:
    level: str
    location: str
    message: str


def _positive(value: int | float | None, field_label: str, location: str) -> list[ValidationMessage]:
    if value is None:
        return []
    if value <= 0:
        return [ValidationMessage("error", location, f"{field_label} должно быть больше 0.")]
    return []


def validate_lift_group(group: LiftGroup, index: int = 1) -> list[ValidationMessage]:
    location = f"Группа {index}"
    messages: list[ValidationMessage] = []
    messages += _positive(group.quantity, "Количество лифтов", location)
    messages += _positive(group.capacity_kg, "Грузоподъемность", location)
    messages += _positive(group.speed_ms, "Скорость", location)
    messages += _positive(group.stops, "Количество остановок", location)
    messages += _positive(group.doors_count, "Количество дверей", location)

    for value, label in [
        (group.cabin_width_mm, "Ширина кабины"),
        (group.cabin_depth_mm, "Глубина кабины"),
        (group.cabin_height_mm, "Высота кабины"),
        (group.landing_door_width_mm, "Ширина дверей"),
        (group.landing_door_height_mm, "Высота дверей"),
        (group.pit_depth_mm, "Глубина приямка"),
        (group.overhead_mm, "Высота верхнего этажа"),
    ]:
        messages += _positive(value, label, location)

    if group.doors_count and group.stops and group.doors_count < group.stops:
        messages.append(
            ValidationMessage(
                "warning",
                location,
                "Количество дверей меньше количества остановок. Проверьте, есть ли непроходные этажи.",
            )
        )

    if group.lifting_height_mm and group.stops and group.stops > 1:
        avg_floor_height = group.lifting_height_mm / (group.stops - 1)
        if avg_floor_height < 2200 or avg_floor_height > 6000:
            messages.append(
                ValidationMessage(
                    "warning",
                    location,
                    "Высота подъема выглядит несогласованной с количеством остановок.",
                )
            )

    if (group.firefighter_mode or "").upper() in {"ДА", "YES"}:
        fire = (group.fire_resistance or "").upper()
        if "EI-60" not in fire and "EI-90" not in fire:
            messages.append(
                ValidationMessage(
                    "warning",
                    location,
                    "Для пожарного режима желательно указать предел огнестойкости EI-60 или выше.",
                )
            )

    if (group.mgn_accessibility or "").upper() in {"ДА", "YES"}:
        messages.append(ValidationMessage("warning", location, MGN_ACCESSIBILITY_WARNING))

    return messages


def validate_questionnaire(questionnaire: Questionnaire) -> list[ValidationMessage]:
    messages: list[ValidationMessage] = []
    if not questionnaire.lift_groups:
        messages.append(ValidationMessage("error", "Опросник", "Добавьте хотя бы одну группу лифтов."))
    for index, group in enumerate(questionnaire.lift_groups, start=1):
        messages.extend(validate_lift_group(group, index))
    return messages

