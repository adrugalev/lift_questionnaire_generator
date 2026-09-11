from __future__ import annotations

import re
from typing import Any


AFP_MATERIAL_FIELDS_BY_FLAG = {
    "cabin_wall_afp": ("side_wall_finish", "rear_wall_finish", "front_wall_finish"),
    "door_finish_afp": (
        "cabin_door_finish",
        "main_floor_landing_door_finish",
        "other_floors_landing_door_finish",
    ),
    "signal_finish_afp": ("cop_finish", "main_floor_lop_finish", "other_floors_lop_finish"),
}

STAINLESS_STEEL_ARTICLE_RE = re.compile(
    r"\b(?:HX-ES|EX-(?:HS|MS|RS|ES|TS))\d+[A-Z]*\b",
    re.IGNORECASE,
)


def is_stainless_steel_finish(value: Any) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    normalized = text.casefold().replace("ё", "е")
    return (
        "нержавеющ" in normalized
        or "stainless steel" in normalized
        or bool(STAINLESS_STEEL_ARTICLE_RE.search(text))
    )
