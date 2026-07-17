# -*- coding: utf-8 -*-
from __future__ import annotations

import base64
import html
import json
import random
import re
from datetime import date
from pathlib import Path
from typing import Any

import streamlit as st
from pydantic import ValidationError

from src.additional_options import ADDITIONAL_OPTION_FIELDS, ADDITIONAL_OPTION_TRANSLATIONS
from src.excel_generator import ExcelGenerationError, generate_questionnaire_xlsx
from src.file_utils import safe_filename
from src.models import LiftGroup, ProjectInfo, Questionnaire
from src.options_manager import OptionsManager
from src.version import app_version_label
from src.validators import MGN_ACCESSIBILITY_WARNING, ValidationMessage, validate_questionnaire


ROOT = Path(__file__).resolve().parent
DEFAULT_TEMPLATE = ROOT / "templates" / "questionnaire_template.xlsx"
MAPPING_PATH = ROOT / "data" / "excel_mapping.json"
OPTIONS_PATH = ROOT / "data" / "options.json"
DRAFT_FILE_KIND = "epss_lift_questionnaire_draft"
DRAFT_SCHEMA_VERSION = 1
LIFT_TEAM_SURNAMES = (
    "Баранова",
    "Другалёв",
    "Конопельнюк",
    "Платонов",
    "Зимин",
    "Попов",
)
APP_DIR = Path(__file__).resolve().parent
LOCAL_TEMPLATES = APP_DIR / "templates"
PREVIOUS_CP_TEMPLATES = (
    Path(r"C:\Users\Drugalev\Documents\Codex\2026-05-21\senior-python-b2b-1-excel-2")
    / "elevator_cp_generator"
    / "templates"
)
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
IMAGE_OPTION_DIRS = {
    "finish": LOCAL_TEMPLATES / "Walls_photo",
    "signal_steel_finish": LOCAL_TEMPLATES / "Walls_photo",
    "ceiling_steel_finish": LOCAL_TEMPLATES / "Walls_photo",
    "floor_finish": LOCAL_TEMPLATES / "Floor_photo",
    "ceiling_type": LOCAL_TEMPLATES / "Ceiling_photo",
    "handrail_type": LOCAL_TEMPLATES / "Handrails_photo",
    "mirror": LOCAL_TEMPLATES / "Mirrors_photo",
    "cop_type": LOCAL_TEMPLATES / "COPHOP_photo",
    "lop_type": LOCAL_TEMPLATES / "LOP_photo",
}
FALLBACK_IMAGE_OPTION_DIRS = {
    "finish": PREVIOUS_CP_TEMPLATES / "Walls_photo",
    "signal_steel_finish": PREVIOUS_CP_TEMPLATES / "Walls_photo",
    "ceiling_steel_finish": PREVIOUS_CP_TEMPLATES / "Walls_photo",
    "floor_finish": PREVIOUS_CP_TEMPLATES / "Floor_photo",
    "ceiling_type": PREVIOUS_CP_TEMPLATES / "Ceiling_photo",
    "handrail_type": PREVIOUS_CP_TEMPLATES / "Handrails_photo",
    "mirror": PREVIOUS_CP_TEMPLATES / "Mirrors_photo",
    "cop_type": PREVIOUS_CP_TEMPLATES / "COPHOP_photo",
    "lop_type": PREVIOUS_CP_TEMPLATES / "LOP_photo",
}
IMAGE_OPTION_PREFIX_FILTERS = {
    "signal_steel_finish": ("EX-HS", "EX-MS"),
    "ceiling_steel_finish": ("EX-HS", "EX-MS", "EX-YS"),
}
EXCLUDED_IMAGE_OPTION_ARTICLES = {
    "cop_type": {"EX-HX99", "IC-CARD", "IC CARD"},
}
MATERIAL_PREFIX_NAMES = [
    ("HX-ES", "Шлифованная нержавеющая сталь"),
    ("EX-HS", "Шлифованная нержавеющая сталь"),
    ("EX-YS", "Окрашенная сталь"),
    ("EX-RS", "Матовая нержавеющая сталь"),
    ("EX-MS", "Зеркальная нержавеющая сталь"),
    ("EX-ES", "Травленая нержавеющая сталь"),
    ("EX-TS", "Текстурированная нержавеющая сталь"),
    ("E-", "Покрытие под дерево"),
    ("TF", "Покрытие под ткань"),
    ("LF", "Покрытие под кожу"),
    ("PM", "Натуральное дерево, шпон"),
    ("CG", "Стекло"),
]
MATERIAL_IMAGE_SORT_PREFIXES = {
    "HX-ES": 0,
    "EX-HS": 0,
    "EX-MS": 1,
    "EX-RS": 2,
    "EX-ES": 3,
    "EX-TS": 4,
    "EX-YS": 5,
    "CG": 6,
    "EX-DB": 7,
    "EX-DM": 7,
    "EX-DS": 7,
    "EX-DA": 7,
    "EX-DR": 7,
    "E-": 8,
    "TF": 9,
    "LF": 10,
    "PM": 11,
}
MATERIAL_ARTICLE_NAMES = {
    "CG-00": "Прозрачное стекло",
    "CG-04": "Цветное стекло",
    "CG-23": "Цветное стекло",
}
MIRROR_ARTICLE_DESCRIPTIONS = {
    "MEX-1": "в неполную ширину до поручня",
    "MEX-2": "в неполную ширину и неполную высоту",
    "MEX-3": "во всю ширину стены до поручня",
    "MEX-4": "во всю ширину стены до пола",
}
FLOOR_PREFIX_NAMES = [
    ("EX-DB", "Прорезиненное покрытие, PVC"),
    ("EX-DM", "Керамогранит"),
    ("EX-DS", "Рифлёная сталь"),
    ("EX-DA", "Рифлёная сталь"),
    ("EX-DR", "Резиновое покрытие"),
]
MANUAL_OPTION_VALUES = {
    "floor_finish": ["Под отделку"],
}
MANUAL_FIELD_OPTION_VALUES = {
    "skirting_finish": ["Нет"],
}
EXCLUDED_SELECT_OPTION_VALUES = {
    "ceiling_type": {"Стандартный"},
    "cop_type": {
        "EX-AC99А, шлифованная нержавеющая сталь EX-HS01",
        "EX-AC99A, шлифованная нержавеющая сталь EX-HS01",
        "EX-AC98А",
        "Стандартная панель",
    },
    "door_opening_type": {"Распашное"},
    "floor_finish": {"EX-DB210", "ПВХ", "Керамогранит", "Рифленый алюминий"},
    "lift_type": {"Больничный"},
    "lop_type": {
        "EX-JC99А, шлифованная нержавеющая сталь EX-HS01",
        "EX-JC99A, шлифованная нержавеющая сталь EX-HS01",
        "Стандартный пост вызова",
    },
    "shaft_material": {"Монолитная", "Бетонная"},
}
GENERIC_FINISH_TEXT_OPTIONS = {"Зеркальная нержавеющая сталь", "Окрашенная сталь", "Ламинированная панель"}
EXCLUDED_FIELD_SELECT_OPTION_VALUES = {
    "side_wall_finish": GENERIC_FINISH_TEXT_OPTIONS,
    "rear_wall_finish": GENERIC_FINISH_TEXT_OPTIONS,
    "front_wall_finish": GENERIC_FINISH_TEXT_OPTIONS,
    "skirting_finish": GENERIC_FINISH_TEXT_OPTIONS,
    "cabin_door_finish": GENERIC_FINISH_TEXT_OPTIONS,
    "main_floor_landing_door_finish": GENERIC_FINISH_TEXT_OPTIONS,
    "other_floors_landing_door_finish": GENERIC_FINISH_TEXT_OPTIONS,
    "handrail_finish": GENERIC_FINISH_TEXT_OPTIONS,
    "ceiling_finish": GENERIC_FINISH_TEXT_OPTIONS,
}
SELECT_WITHOUT_CUSTOM_OPTION_KEYS = {
    "cabin_type",
    "ceiling_type",
    "cop_type",
    "display_type",
    "door_model",
    "door_opening_type",
    "floor_finish",
    "fire_resistance",
    "group_operation",
    "handrail_type",
    "lift_type",
    "lop_type",
    "mirror",
    "seismic",
    "shaft_material",
    "yes_no",
}
STRICT_SELECT_OPTION_KEYS = {
    "cop_type",
    "door_model",
    "lop_type",
    "seismic",
}
SELECT_WITHOUT_EMPTY_FIELDS = {
    "door_model",
}
SELECT_WITHOUT_CUSTOM_FIELDS = {
    "side_wall_finish",
    "rear_wall_finish",
    "front_wall_finish",
    "skirting_finish",
    "cabin_door_finish",
    "main_floor_landing_door_finish",
    "other_floors_landing_door_finish",
    "handrail_finish",
    "ceiling_finish",
}
INLINE_PREVIEW_OPTION_KEYS = {
    "finish",
    "signal_steel_finish",
    "ceiling_steel_finish",
    "floor_finish",
    "ceiling_type",
    "handrail_type",
    "mirror",
}
OTHER_OPTION = "Другое..."
SECTION_COMPLETE_MARK = "✅"

NUMERIC_FIELDS = {
    "quantity": int,
    "capacity_kg": int,
    "speed_ms": float,
    "lifting_height_mm": int,
    "stops": int,
    "underground_floors": int,
    "doors_count": int,
    "cabin_width_mm": int,
    "cabin_depth_mm": int,
    "cabin_height_mm": int,
    "landing_door_width_mm": int,
    "landing_door_height_mm": int,
    "shaft_width_mm": int,
    "shaft_depth_mm": int,
    "pit_depth_mm": int,
    "overhead_mm": int,
}

CAPACITY_OPTIONS_KG = [
    400,
    450,
    630,
    800,
    1000,
    1050,
    1150,
    1275,
    1350,
    1600,
    1800,
    2000,
    2500,
    3000,
    3500,
    4000,
    4500,
    5000,
]

SPEED_OPTIONS_MS = [
    "0.25",
    "0.5",
    "1",
    "1.6",
    "1.75",
    "2",
    "2.5",
    "3",
    "4",
    "5",
    "6",
]
DEFAULT_LIFT_TYPE = "Грузопассажирский"
DEFAULT_MAIN_LANDING_FLOOR = "1"
DEFAULT_MACHINE_ROOM = "Без машинного помещения"
DEFAULT_SHAFT_MATERIAL = "Железобетон"
DEFAULT_SEISMIC = "НЕТ"
DEFAULT_FIRE_RESISTANCE = "EI-60"
DEFAULT_DOOR_MODEL = "NBSL"
HELPER_GROUP_FIELDS = {"underground_floors"}
HELPER_GROUP_FIELDS.update(ADDITIONAL_OPTION_TRANSLATIONS)
SIGNAL_FINISH_FIELDS = {
    "cop_type": "cop_finish",
    "main_floor_lop_type": "main_floor_lop_finish",
    "other_floors_lop_type": "other_floors_lop_finish",
}
SIGNAL_PREVIEW_FIELD_PAIRS = (
    ("cop_type", "cop_finish"),
    ("main_floor_lop_type", "main_floor_lop_finish"),
    ("other_floors_lop_type", "other_floors_lop_finish"),
)
CABIN_COMPONENT_FINISH_FIELDS = {
    "handrail_type": "handrail_finish",
    "ceiling_type": "ceiling_finish",
}
SYNCABLE_GROUP_FIELDS = {
    "cabin_type",
    "side_wall_finish",
    "rear_wall_finish",
    "front_wall_finish",
    "floor_finish",
    "handrail_type",
    "handrail_finish",
    "ceiling_type",
    "ceiling_finish",
    "skirting_finish",
    "mirror",
    "door_opening_type",
    "door_model",
    "cabin_door_finish",
    "main_floor_landing_door_finish",
    "other_floors_landing_door_finish",
    "fire_resistance",
    "firefighter_mode",
    "cop_type",
    "cop_finish",
    "display_type",
    "main_floor_lop_type",
    "main_floor_lop_finish",
    "other_floors_lop_type",
    "other_floors_lop_finish",
    "machine_room",
    "shaft_material",
    "room_under_pit",
    "seismic",
    "mgn_accessibility",
}
SYNCABLE_GROUP_FIELDS.update(ADDITIONAL_OPTION_TRANSLATIONS)

FIELD_GROUPS = {
    "Основные": [
        ("section", "№ дома / № секции", "text", None),
        ("lift_name", "№ лифта / описание группы", "text", None),
        ("quantity", "Количество лифтов", "number", None),
        ("lift_type", "Тип лифта", "select", "lift_type"),
        ("capacity_kg", "Грузоподъемность, кг", "capacity_select", None),
        ("speed_ms", "Скорость, м/с", "speed_select", None),
        ("lifting_height_mm", "Высота подъема, мм", "number", None),
        ("stops", "Количество остановок", "number", None),
        ("underground_floors", "Количество подземных этажей", "number", None),
        ("doors_count", "Количество дверей", "number", None),
        ("group_operation", "Работа в группе", "select", "group_operation"),
        ("button_marking", "Маркировка кнопок", "text", None),
        ("main_landing_floor", "Основной посадочный этаж", "text", None),
    ],
    "Кабина": [
        ("cabin_type", "Тип кабины", "select", "cabin_type"),
        ("cabin_width_mm", "Ширина кабины, мм", "number", None),
        ("cabin_depth_mm", "Глубина кабины, мм", "number", None),
        ("cabin_height_mm", "Высота кабины, мм", "number", None),
        ("side_wall_finish", "Облицовка боковых стен", "select", "finish"),
        ("rear_wall_finish", "Облицовка задней стены", "select", "finish"),
        ("front_wall_finish", "Облицовка передней стены", "select", "finish"),
        ("floor_finish", "Пол", "select", "floor_finish"),
        ("handrail_type", "Тип поручня", "select", "handrail_type"),
        ("handrail_finish", "Материал поручня", "select", "signal_steel_finish"),
        ("ceiling_type", "Тип потолка", "select", "ceiling_type"),
        ("ceiling_finish", "Материал потолка", "select", "ceiling_steel_finish"),
        ("skirting_finish", "Плинтус", "select", "finish"),
        ("mirror", "Зеркало", "select", "mirror"),
    ],
    "Двери": [
        ("door_opening_type", "Тип открывания дверей", "select", "door_opening_type"),
        ("cabin_door_finish", "Облицовка дверей кабины", "select", "finish"),
        ("door_model", "Модель дверей", "select", "door_model"),
        ("landing_door_width_mm", "Ширина дверей, мм", "number", None),
        ("main_floor_landing_door_finish", "Облицовка на основном посадочном этаже", "select", "finish"),
        ("other_floors_landing_door_finish", "Облицовка на остальных этажах", "select", "finish"),
        ("landing_door_height_mm", "Высота дверей, мм", "number", None),
        ("firefighter_mode", "Режим перевозки пожарных подразделений", "select", "yes_no"),
        ("fire_resistance", "Предел огнестойкости", "select", "fire_resistance"),
    ],
    "Сигнализация": [
        ("cop_type", "Панель управления кабины", "select", "cop_type"),
        ("cop_finish", "Материал панели управления кабины", "select", "signal_steel_finish"),
        ("main_floor_lop_type", "Пост вызова на основном посадочном этаже", "select", "lop_type"),
        ("main_floor_lop_finish", "Материал поста вызова на основном этаже", "select", "signal_steel_finish"),
        ("other_floors_lop_type", "Посты вызова на остальных этажах", "select", "lop_type"),
        ("other_floors_lop_finish", "Материал постов вызова на остальных этажах", "select", "signal_steel_finish"),
        ("display_type", "Тип дисплея", "select", "display_type"),
    ],
    "Шахта": [
        ("machine_room", "Машинное помещение", "select", "machine_room"),
        ("shaft_material", "Материал шахты", "select", "shaft_material"),
        ("shaft_width_mm", "Ширина шахты, мм", "number", None),
        ("shaft_depth_mm", "Глубина шахты, мм", "number", None),
        ("pit_depth_mm", "Глубина приямка, мм", "number", None),
        ("overhead_mm", "Высота верхнего этажа, мм", "number", None),
        ("room_under_pit", "Наличие помещения под приямком", "select", "yes_no"),
        ("seismic", "Сейсмичность", "select", "seismic"),
    ],
    "Дополнительные опции": [
        ("mgn_accessibility", "Доступность МГН", "checkbox_yes_no", None),
        *[(field, label, "checkbox_yes_no", None) for field, label in ADDITIONAL_OPTION_FIELDS],
    ],
}

DOOR_FINISH_FIELDS = {
    "cabin_door_finish",
    "main_floor_landing_door_finish",
    "other_floors_landing_door_finish",
}
WALL_FINISH_FIELDS = ("side_wall_finish", "rear_wall_finish", "front_wall_finish")
WALL_LINKED_FINISH_FIELDS = (
    "handrail_finish",
    "ceiling_finish",
    "skirting_finish",
    "cabin_door_finish",
    "main_floor_landing_door_finish",
    "other_floors_landing_door_finish",
    "cop_finish",
    "main_floor_lop_finish",
    "other_floors_lop_finish",
)
MGN_ACCESSIBILITY_FIELD = "mgn_accessibility"
MGN_VOICE_OPTION_FIELD = "option_russian_voice"


def _render_version_caption(options: OptionsManager) -> None:
    st.markdown(
        '<span class="version-trigger-scope"></span>',
        unsafe_allow_html=True,
    )
    if st.button(app_version_label(), key="version_test_fill_click"):
        _handle_version_test_fill_click(options)


def _handle_version_test_fill_click(options: OptionsManager) -> None:
    click_count = int(st.session_state.get("epss_test_fill_click_count", 0)) + 1
    if click_count < 4:
        st.session_state.epss_test_fill_click_count = click_count
        return

    st.session_state.epss_test_fill_click_count = 0
    _apply_test_questionnaire(options)
    st.rerun()


def _apply_test_questionnaire(options: OptionsManager) -> None:
    project = _random_test_project()
    groups = _random_test_groups(options)

    st.session_state.prefill_project = dict(project)
    for field, value in project.items():
        st.session_state[f"project_{field}"] = value

    st.session_state.group_count = len(groups)
    st.session_state.prefill_groups = [dict(group) for group in groups]
    st.session_state.extracted_group_fields = [set() for _ in groups]
    _sync_group_widgets_from_group_data(groups)


def _random_test_project() -> dict[str, Any]:
    projects = [
        {
            "project_name": "UNO Соколиная гора",
            "customer": "ООО СЗ ЮНИТ Девелопмент",
            "address": "г. Москва, район Соколиная гора, ул. 8-я Соколиной Горы, вл. 15",
        },
        {
            "project_name": "ЖК Северный квартал",
            "customer": "ООО Специализированный застройщик Север",
            "address": "г. Санкт-Петербург, проспект Просвещения, участок 12",
        },
        {
            "project_name": "Бизнес-центр Орбита",
            "customer": "АО ИнвестПроект",
            "address": "г. Казань, ул. Космонавтов, д. 31",
        },
    ]
    project = dict(random.choice(projects))
    project["report_date"] = date.today()
    return project


def _random_test_groups(options: OptionsManager) -> list[dict[str, Any]]:
    group_count = random.randint(2, 4)
    next_lift_number = 1
    groups: list[dict[str, Any]] = []
    for index in range(group_count):
        quantity = random.randint(1, 3)
        lift_name = f"Л{next_lift_number}"
        next_lift_number += quantity
        stops = random.randint(8, 18)
        underground_floors = random.randint(0, min(2, stops - 1))
        cabin_type = random.choice(["Непроходная", "Проходная"])
        doors_count = stops if cabin_type == "Непроходная" else random.randint(stops, stops + underground_floors + 3)
        capacity = random.choice(CAPACITY_OPTIONS_KG)
        cabin_width, cabin_depth = _test_cabin_size(capacity)
        wall_finish = _random_select_value(options, "finish") or "Шлифованная нержавеющая сталь EX-HS01"
        signal_finish = _random_select_value(options, "signal_steel_finish") or "Шлифованная нержавеющая сталь EX-HS01"
        ceiling_finish = _random_select_value(options, "ceiling_steel_finish") or signal_finish

        group = {
            "section": f"Секция {index + 1}",
            "lift_name": lift_name,
            "quantity": quantity,
            "lift_type": DEFAULT_LIFT_TYPE,
            "capacity_kg": capacity,
            "speed_ms": random.choice(["1", "1.6", "1.75", "2"]),
            "lifting_height_mm": (stops - 1) * random.choice([3000, 3150, 3300]),
            "stops": stops,
            "underground_floors": underground_floors,
            "doors_count": doors_count,
            "group_operation": "Одиночное" if quantity == 1 else random.choice(["Групповое", "DDS"]),
            "button_marking": _button_marking_from_stops(stops, underground_floors),
            "main_landing_floor": DEFAULT_MAIN_LANDING_FLOOR,
            "cabin_type": cabin_type,
            "cabin_width_mm": cabin_width,
            "cabin_depth_mm": cabin_depth,
            "cabin_height_mm": random.choice([2200, 2300, 2400]),
            "side_wall_finish": wall_finish,
            "rear_wall_finish": wall_finish,
            "front_wall_finish": wall_finish,
            "floor_finish": _random_select_value(options, "floor_finish") or "Под отделку",
            "handrail_type": _random_select_value(options, "handrail_type") or "EX-FS01",
            "handrail_finish": signal_finish,
            "ceiling_type": _random_select_value(options, "ceiling_type") or "EX-J135",
            "ceiling_finish": ceiling_finish,
            "skirting_finish": wall_finish,
            "mirror": _random_select_value(options, "mirror") or "Нет",
            "door_opening_type": random.choice(["Телескопическое", "Центральное"]),
            "door_model": DEFAULT_DOOR_MODEL,
            "cabin_door_finish": wall_finish,
            "fire_resistance": DEFAULT_FIRE_RESISTANCE,
            "landing_door_width_mm": random.choice([800, 900, 1000, 1100]),
            "landing_door_height_mm": random.choice([2100, 2200, 2300]),
            "main_floor_landing_door_finish": wall_finish,
            "other_floors_landing_door_finish": wall_finish,
            "firefighter_mode": random.choice(["ДА", "НЕТ"]),
            "cop_type": _random_select_value(options, "cop_type") or "EX-AC99A",
            "cop_finish": signal_finish,
            "main_floor_lop_type": _random_select_value(options, "lop_type") or "EX-JC99A",
            "main_floor_lop_finish": signal_finish,
            "other_floors_lop_type": _random_select_value(options, "lop_type") or "EX-JC99A",
            "other_floors_lop_finish": signal_finish,
            "display_type": random.choice(["DOT-Matrix LED", "LCD (7-сегментный)", 'LCD 10,4"', 'LCD 15"']),
            "machine_room": DEFAULT_MACHINE_ROOM,
            "shaft_material": DEFAULT_SHAFT_MATERIAL,
            "shaft_width_mm": cabin_width + random.choice([800, 900, 1000]),
            "shaft_depth_mm": cabin_depth + random.choice([650, 800, 950]),
            "pit_depth_mm": random.choice([1150, 1250, 1400, 1500]),
            "overhead_mm": random.choice([3600, 3800, 4000, 4200]),
            "room_under_pit": random.choice(["ДА", "НЕТ"]),
            "seismic": DEFAULT_SEISMIC,
            "mgn_accessibility": "ДА",
        }
        _apply_random_additional_options(group)
        groups.append(group)
    return groups


def _test_cabin_size(capacity: int) -> tuple[int, int]:
    if capacity <= 630:
        return random.choice([(1100, 1400), (1100, 1500)])
    if capacity <= 1000:
        return random.choice([(1100, 2100), (1200, 2100), (1400, 1600)])
    if capacity <= 1600:
        return random.choice([(1400, 2400), (1500, 2500)])
    return random.choice([(2000, 2500), (2100, 2800), (2400, 3000)])


def _random_select_value(options: OptionsManager, option_key: str, field: str | None = None) -> str | None:
    values = _select_values(options, option_key, field)
    return random.choice(values) if values else None


def _apply_random_additional_options(group: dict[str, Any]) -> None:
    for field, _ in ADDITIONAL_OPTION_FIELDS:
        group[field] = random.random() < 0.22
    group["option_ard"] = True
    group["option_russian_voice"] = True


def main() -> None:
    st.set_page_config(page_title="Генератор опросных листов EPSS", layout="wide")
    _inject_filled_field_styles()
    options = OptionsManager(OPTIONS_PATH)
    _init_state()
    _apply_pending_draft_restore()
    st.markdown('<div class="app-header-title">Генератор опросных листов EPSS</div>', unsafe_allow_html=True)
    _render_version_caption(options)

    _render_lift_team_sidebar()
    _render_project_summary_sidebar()

    project_data = _project_block()
    group_data = _groups_block(options)
    _draft_sidebar(project_data, group_data)

    questionnaire = _build_questionnaire(project_data, group_data)
    if questionnaire:
        _validation_block(questionnaire)
        _download_block(questionnaire)


def _inject_filled_field_styles() -> None:
    st.markdown(_filled_field_styles_css(), unsafe_allow_html=True)


def _filled_field_styles_css() -> str:
    return """
        <style>
        @media (min-width: 768px) {
            section[data-testid="stSidebar"],
            section[data-testid="stSidebar"] > div {
                min-width: 20.5rem !important;
                width: 20.5rem !important;
            }
        }

        div[data-testid="stElementContainer"]:has(.app-header-title) {
            margin-bottom: -0.65rem !important;
        }

        .app-header-title {
            color: #313340;
            font-size: 3.05rem;
            font-weight: 700;
            letter-spacing: 0;
            line-height: 1.08;
            margin: 0;
        }

        div[data-testid="stElementContainer"]:has(.version-trigger-scope) {
            height: 0 !important;
            margin: 0 !important;
            overflow: hidden !important;
        }

        div[data-testid="stElementContainer"]:has(.version-trigger-scope) + div[data-testid="stElementContainer"] {
            margin-bottom: -0.1rem !important;
            margin-top: -0.1rem !important;
        }

        div[data-testid="stElementContainer"]:has(.version-trigger-scope) + div[data-testid="stElementContainer"] button,
        div[data-testid="stElementContainer"]:has(.version-trigger-scope) + div[data-testid="stElementContainer"] button:hover,
        div[data-testid="stElementContainer"]:has(.version-trigger-scope) + div[data-testid="stElementContainer"] button:focus,
        div[data-testid="stElementContainer"]:has(.version-trigger-scope) + div[data-testid="stElementContainer"] button:active {
            background: transparent !important;
            border: 0 !important;
            box-shadow: none !important;
            color: #8b8f98 !important;
            cursor: default;
            height: 1.15rem !important;
            min-height: 0 !important;
            outline: none !important;
            padding: 0 !important;
            text-align: left !important;
            transform: none !important;
        }

        div[data-testid="stElementContainer"]:has(.version-trigger-scope) + div[data-testid="stElementContainer"] button p {
            font-size: 0.875rem;
            line-height: 1.15;
            margin: 0 !important;
        }

        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stDateInput"] input,
        div[data-testid="stSelectbox"] div[role="group"],
        div[data-testid="stSelectbox"] input,
        div[data-testid="stSelectbox"] button {
            background-color: #eef1f5 !important;
            transition: background-color 120ms ease, box-shadow 120ms ease;
        }

        div[data-testid="stTextInput"] input:not(:placeholder-shown),
        div[data-testid="stTextArea"] textarea:not(:placeholder-shown),
        div[data-testid="stDateInput"] input:not(:placeholder-shown),
        div[data-testid="stSelectbox"]:has(input[value]:not([value=""])) div[role="group"],
        div[data-testid="stSelectbox"]:has(input[value]:not([value=""])) input,
        div[data-testid="stSelectbox"]:has(input[value]:not([value=""])) button {
            background-color: #e5f6ec !important;
            outline: 1px solid #6ec48a !important;
            outline-offset: -1px !important;
        }

        div[data-testid="stTextInput"]:focus-within *,
        div[data-testid="stTextArea"]:focus-within *,
        div[data-testid="stDateInput"]:focus-within *,
        div[data-baseweb="input"]:focus-within,
        div[data-baseweb="input"]:focus-within *,
        div[data-baseweb="textarea"]:focus-within,
        div[data-baseweb="textarea"]:focus-within * {
            border-color: #111111 !important;
            outline-color: #111111 !important;
            outline: none !important;
        }

        div[data-testid="stTextInput"]:focus-within div,
        div[data-testid="stTextArea"]:focus-within div,
        div[data-testid="stDateInput"]:focus-within div,
        div[data-baseweb="input"]:focus-within,
        div[data-baseweb="input"]:focus-within *,
        div[data-baseweb="textarea"]:focus-within,
        div[data-baseweb="textarea"]:focus-within * {
            box-shadow: none !important;
        }

        div[data-testid="stTextInput"] div[data-baseweb="input"]:has(input:focus),
        div[data-testid="stTextArea"] div[data-baseweb="textarea"]:has(textarea:focus),
        div[data-testid="stDateInput"] div[data-baseweb="input"]:has(input:focus) {
            border-color: #111111 !important;
            box-shadow: none !important;
            outline: none !important;
        }

        div[data-testid="stTextInput"] input:focus,
        div[data-testid="stTextArea"] textarea:focus,
        div[data-testid="stDateInput"] input:focus {
            border-color: #111111 !important;
            box-shadow: inset 0 0 0 2px #111111 !important;
            outline: none !important;
        }

        div[data-testid="stSelectbox"] div[role="group"]:focus-within {
            border-color: #111111 !important;
            box-shadow: inset 0 0 0 2px #111111 !important;
        }

        div[data-testid="stButton"] button {
            min-height: 2.5rem !important;
            height: 2.5rem !important;
            padding: 0.25rem 0.85rem !important;
            white-space: normal !important;
            line-height: 1.2 !important;
        }

        div[data-testid="stButton"] button p {
            white-space: normal !important;
            overflow-wrap: normal !important;
            word-break: normal !important;
            text-align: center !important;
            line-height: 1.2 !important;
        }

        div[data-testid="stButton"] button[kind="primary"] {
            background-color: #2e9b57 !important;
            border-color: #2e9b57 !important;
            color: #ffffff !important;
        }

        div[data-testid="stButton"] button[kind="primary"]:hover {
            background-color: #237a44 !important;
            border-color: #237a44 !important;
            color: #ffffff !important;
        }

        div[data-testid="stButton"] button[kind="primary"]:disabled {
            background-color: #dceee3 !important;
            border-color: #c3dfcc !important;
            color: #7fa28b !important;
        }

        div[data-testid="stButton"] button:not([kind="primary"]) {
            background-color: #fff3e4 !important;
            border-color: #f0a54a !important;
            color: #5f3200 !important;
        }

        div[data-testid="stButton"] button:not([kind="primary"]):hover {
            background-color: #ffe5c2 !important;
            border-color: #e58d22 !important;
            color: #4b2800 !important;
        }

        div[data-testid="stButton"] button:not([kind="primary"]):disabled {
            background-color: #fff7ec !important;
            border-color: #f1cfaa !important;
            color: #b08a64 !important;
        }

        div[data-testid="stElementContainer"]:has(.management-button-marker) {
            height: 0 !important;
            margin: 0 !important;
            overflow: hidden !important;
        }

        div[data-testid="stElementContainer"]:has(.management-button-marker)
            + div[data-testid="stElementContainer"] {
            margin-top: -0.75rem !important;
        }

        div[data-testid="stElementContainer"]:has(.management-button-marker)
            + div[data-testid="stElementContainer"] div[data-testid="stButton"] button {
            align-items: center !important;
            display: flex !important;
            justify-content: center !important;
            min-height: 2.3rem !important;
            height: 2.3rem !important;
            padding: 0.2rem 0.65rem !important;
        }

        div[data-testid="stElementContainer"]:has(.management-button-marker)
            + div[data-testid="stElementContainer"] div[data-testid="stButton"] button p {
            font-size: 0.9rem !important;
            line-height: 1.05 !important;
            white-space: nowrap !important;
        }

        div[data-testid="stElementContainer"]:has(.group-nav-button-marker) {
            height: 0 !important;
            margin: 0 !important;
            overflow: hidden !important;
        }

        div[data-testid="stElementContainer"]:has(.group-nav-button-marker)
            + div[data-testid="stElementContainer"] {
            margin-top: -0.75rem !important;
        }

        div[data-testid="stElementContainer"]:has(.group-nav-button-marker)
            + div[data-testid="stElementContainer"] div[data-testid="stButton"] button:not([kind="primary"]) {
            background-color: #eef6ff !important;
            border-color: #86b8ea !important;
            color: #174d7e !important;
        }

        div[data-testid="stElementContainer"]:has(.group-nav-button-marker)
            + div[data-testid="stElementContainer"] div[data-testid="stButton"] button:not([kind="primary"]):hover {
            background-color: #dcecff !important;
            border-color: #5ea0e4 !important;
            color: #123c63 !important;
        }

        div[data-testid="stElementContainer"]:has(.group-nav-button-marker)
            + div[data-testid="stElementContainer"] div[data-testid="stButton"] button[kind="primary"] {
            background-color: #2563eb !important;
            border-color: #1d4ed8 !important;
            color: #ffffff !important;
        }

        div[data-testid="stElementContainer"]:has(.group-nav-button-marker)
            + div[data-testid="stElementContainer"] div[data-testid="stButton"] button[kind="primary"]:hover {
            background-color: #1d4ed8 !important;
            border-color: #1e40af !important;
            color: #ffffff !important;
        }

        .mgn-attention-block {
            background: #fff9dc;
            border: 1px solid #f0d575;
            border-left: 5px solid #d99600;
            border-radius: 8px;
            color: #4c3500;
            margin: 0.75rem 0 1rem;
            padding: 0.85rem 1rem 0.9rem;
        }

        .mgn-attention-title {
            color: #2d2400;
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 0.55rem;
        }

        .mgn-attention-meta {
            align-items: center;
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-bottom: 0.55rem;
        }

        .mgn-attention-label {
            color: #7c6100;
            font-size: 0.9rem;
            font-weight: 600;
            margin-right: 0.15rem;
        }

        .mgn-attention-chip {
            background: #ffe2a8;
            border: 1px solid #e0a83a;
            border-radius: 999px;
            color: #4d2f00;
            display: inline-flex;
            font-size: 0.92rem;
            font-weight: 700;
            line-height: 1;
            padding: 0.35rem 0.62rem;
        }

        .mgn-attention-text {
            color: #6c4c00;
            font-size: 0.95rem;
            line-height: 1.45;
        }

        div[data-testid="stSelectbox"] div[role="group"] {
            min-height: 2.5rem !important;
            height: 2.5rem !important;
        }

        div[data-testid="stSelectbox"] input,
        div[data-testid="stSelectbox"] button {
            min-height: 2.5rem !important;
            height: 2.5rem !important;
        }

        div[data-testid="stExpanderDetails"] {
            padding-top: 0.75rem !important;
            padding-bottom: 0.75rem !important;
        }

        div[data-testid="stVerticalBlock"] {
            gap: 0.75rem !important;
        }

        div[data-testid="stHorizontalBlock"] {
            gap: 1rem !important;
        }

        div[data-testid="stWidgetLabel"] {
            margin-bottom: 0.25rem !important;
        }

        div[data-testid="stDateInput"] div[data-baseweb="input"],
        div[data-testid="stDateInput"] div[data-baseweb="base-input"],
        div[data-testid="stDateInput"] input {
            min-height: 2.5rem !important;
            height: 2.5rem !important;
        }

        div[data-testid="stDateInput"] div[data-baseweb="base-input"],
        div[data-testid="stDateInput"] input {
            min-height: calc(2.5rem - 2px) !important;
            height: calc(2.5rem - 2px) !important;
        }

        div[data-testid="stDateInput"] input:not(:placeholder-shown) {
            outline: none !important;
        }

        div[data-testid="stDateInput"] div[data-baseweb="input"]:has(input:not(:placeholder-shown)) {
            background-color: #e5f6ec !important;
            border: 1px solid #6ec48a !important;
            box-shadow: none !important;
            outline: none !important;
            box-sizing: border-box !important;
            overflow: visible !important;
        }

        div[data-testid="stDateInput"] div[data-baseweb="base-input"]:has(input:not(:placeholder-shown)),
        div[data-testid="stDateInput"] div[data-baseweb="input"]:has(input:not(:placeholder-shown)) input {
            background-color: transparent !important;
            border: 0 !important;
            box-shadow: none !important;
            outline: none !important;
        }

        .image-picker-label {
            color: #0f172a;
            font-size: 0.875rem;
            font-weight: 400;
            line-height: 1.35;
            margin-bottom: 0.25rem;
        }

        .image-picker-thumb {
            align-items: center;
            background: #eef1f5;
            border: 1px solid #d1d5db;
            border-radius: 0.45rem;
            box-sizing: border-box;
            display: flex;
            height: 2.5rem;
            justify-content: center;
            overflow: hidden;
            width: 2.5rem;
        }

        .image-picker-thumb img {
            display: block;
            height: 100%;
            object-fit: contain;
            width: 100%;
        }

        button[data-testid="stPopoverButton"] {
            min-height: 2.5rem !important;
            height: 2.5rem !important;
            padding: 0.25rem 0.5rem !important;
            white-space: nowrap !important;
        }

        button[data-testid="stPopoverButton"] > div {
            align-items: center !important;
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 0.1rem !important;
            height: 100% !important;
            justify-content: center !important;
        }

        button[data-testid="stPopoverButton"] p {
            line-height: 1 !important;
            margin: 0 !important;
            white-space: nowrap !important;
        }

        button[data-testid="stPopoverButton"] span[data-testid="stIconMaterial"] {
            font-size: 1rem !important;
            line-height: 1 !important;
        }

        .section-fields-spacer {
            height: 1rem;
        }

        .section-fields-spacer.compact {
            height: 0.35rem;
        }

        .selected-image-card {
            align-items: center;
            background: #f8fafc;
            border: 1px solid #d8dee8;
            border-radius: 0.5rem;
            box-sizing: border-box;
            display: grid;
            gap: 0.75rem;
            grid-template-columns: 5.5rem minmax(0, 1fr);
            margin-bottom: 0.55rem;
            min-height: 6.5rem;
            padding: 0.65rem;
        }

        .selected-image-preview-wrap {
            padding: 0 0.25rem 0.55rem 0;
        }

        .selected-image-card img {
            border-radius: 0.4rem;
            display: block;
            height: 5rem;
            object-fit: contain;
            width: 5rem;
        }

        .selected-image-card-title {
            color: #475569;
            font-size: 0.82rem;
            line-height: 1.2;
            margin-bottom: 0.35rem;
        }

        .selected-image-card-value {
            color: #0f172a;
            font-size: 1rem;
            font-weight: 600;
            line-height: 1.25;
            overflow-wrap: anywhere;
        }

        .image-dialog-tile {
            align-items: center;
            display: flex;
            flex-direction: column;
            gap: 0.35rem;
            min-height: 9.7rem;
        }

        .image-dialog-image {
            align-items: center;
            display: flex;
            height: 6.1rem;
            justify-content: center;
            width: 100%;
        }

        .image-dialog-image img {
            display: block;
            max-height: 6.1rem;
            max-width: 6.1rem;
            object-fit: contain;
        }

        .image-dialog-label {
            align-items: center;
            color: #6b7280;
            display: flex;
            font-size: 0.72rem;
            height: 2.85rem;
            justify-content: center;
            line-height: 1.08;
            overflow-wrap: anywhere;
            text-align: center;
            width: 100%;
        }

        .project-summary-card {
            background: #ffffff;
            border: 1px solid #dce3eb;
            border-radius: 0.8rem;
            box-shadow: 0 0.15rem 0.55rem rgba(49, 51, 64, 0.06);
            margin: 0;
            padding: 0.9rem 1rem;
        }

        .project-summary-title {
            color: #313340;
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }

        .project-summary-name {
            color: #6b7280;
            font-size: 0.78rem;
            line-height: 1.25;
            margin-bottom: 0.75rem;
            overflow-wrap: anywhere;
        }

        .project-summary-metrics {
            display: grid;
            gap: 0.55rem;
            grid-template-columns: 1fr 1fr;
        }

        .project-summary-metric {
            background: #f4f7fb;
            border-radius: 0.6rem;
            display: flex;
            flex-direction: column;
            padding: 0.55rem 0.65rem;
        }

        .project-summary-metric-label {
            color: #6b7280;
            display: block;
            font-size: 0.72rem;
            line-height: 1.15;
            min-height: 1.15em;
        }

        .project-summary-metric-value {
            color: #2f66e8;
            display: block;
            font-size: 1.45rem;
            font-weight: 700;
            line-height: 1.15;
            margin-top: 0.18rem;
        }

        .project-summary-breakdown {
            border-top: 1px solid #e1e7ef;
            color: #667085;
            font-size: 0.68rem;
            line-height: 1.35;
            margin-top: 0.7rem;
            padding: 0.65rem 0.15rem 0;
        }

        .project-summary-breakdown-line + .project-summary-breakdown-line {
            margin-top: 0.28rem;
        }

        .lift-team-sidebar-label {
            color: #313340;
            font-size: 1rem;
            font-weight: 700;
            line-height: 1.2;
            margin-bottom: 0;
        }

        .lift-team-sidebar-gap {
            height: 0.5rem;
        }

        .sidebar-block-gap {
            height: 1.25rem;
        }

        .draft-sidebar-gap {
            height: 2.5rem;
        }

        section[data-testid="stSidebar"] [class*="st-key-draft_upload"] div[data-testid="stFileUploaderDropzone"] {
            box-sizing: border-box !important;
            padding: 0.75rem 0.85rem 0.95rem !important;
        }

        section[data-testid="stSidebar"] [class*="st-key-draft_upload"] button {
            box-sizing: border-box !important;
            font-size: 0.9rem !important;
            margin-left: calc(50% + 0.35rem) !important;
            min-width: 0 !important;
            min-height: 2.55rem !important;
            padding: 0.35rem 0.55rem !important;
            width: 7.15rem !important;
        }

        section[data-testid="stSidebar"] [class*="st-key-draft_upload"] button p {
            font-size: 0 !important;
        }

        section[data-testid="stSidebar"] [class*="st-key-draft_upload"] button p::after {
            content: "Загрузить";
            font-size: 0.9rem !important;
        }

        section[data-testid="stSidebar"] [class*="st-key-draft_save"] {
            margin-bottom: 2.55rem !important;
            margin-left: calc(50% - 7.5rem) !important;
            margin-top: -6.2rem !important;
            position: relative;
            width: 7.15rem !important;
            z-index: 2;
        }

        section[data-testid="stSidebar"] [class*="st-key-draft_save"] button {
            box-sizing: border-box !important;
            font-size: 0.9rem !important;
            min-width: 0 !important;
            min-height: 2.55rem !important;
            padding: 0.35rem 0.55rem !important;
        }

        section[data-testid="stSidebar"]:has(
            [class*="st-key-draft_upload"] [data-testid="stFileChip"]
        ) [class*="st-key-draft_save"] {
            margin-bottom: 0 !important;
            margin-left: auto !important;
            margin-right: auto !important;
            margin-top: 0.6rem !important;
            z-index: auto !important;
        }

        section[data-testid="stSidebar"] [class*="st-key-project_preparer_"] button {
            background: #f5f7fa !important;
            border: 1px solid #cbd1da !important;
            border-radius: 999px !important;
            box-shadow: none !important;
            color: #1f2937 !important;
            font-size: 0.78rem !important;
            min-height: 2rem !important;
            padding: 0.25rem 0.65rem !important;
        }

        section[data-testid="stSidebar"] [class*="st-key-project_preparer_"] button p {
            color: #1f2937 !important;
        }

        </style>
        """


def _init_state() -> None:
    st.session_state.setdefault("group_count", 1)
    st.session_state.setdefault("prefill_groups", [{}])
    st.session_state.setdefault("group_drafts", [{}])
    st.session_state.setdefault("prefill_project", {})
    st.session_state.setdefault("extracted_group_fields", [])
    st.session_state.setdefault("active_group_index", 0)
    st.session_state.setdefault("group_section_widget_revision", 0)
    st.session_state.setdefault("draft_upload_revision", 0)


def _render_project_summary_sidebar() -> None:
    summary = _project_summary_from_state()
    project_name = html.escape(summary["project_name"] or "Название проекта не указано")
    lift_breakdown = "".join(
        f'<div class="project-summary-breakdown-line">{html.escape(line)}</div>'
        for line in summary["lift_breakdown"]
    )
    lift_breakdown_block = (
        f'<div class="project-summary-breakdown">{lift_breakdown}</div>' if lift_breakdown else ""
    )
    st.sidebar.markdown('<div class="sidebar-block-gap"></div>', unsafe_allow_html=True)
    st.sidebar.markdown(
        f"""
        <div class="project-summary-card">
            <div class="project-summary-title">Кратко о проекте</div>
            <div class="project-summary-name">{project_name}</div>
            <div class="project-summary-metrics">
                <div class="project-summary-metric">
                    <span class="project-summary-metric-label">Лифты</span>
                    <span class="project-summary-metric-value">{summary["lift_count"]}</span>
                </div>
                <div class="project-summary-metric">
                    <span class="project-summary-metric-label">Группы</span>
                    <span class="project-summary-metric-value">{summary["group_count"]}</span>
                </div>
            </div>
            {lift_breakdown_block}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _draft_sidebar(project_data: dict[str, Any], group_data: list[dict[str, Any]]) -> None:
    restored_notice = st.session_state.pop("draft_restore_notice", None)
    restore_error = st.session_state.pop("draft_restore_error", None)
    payload = _draft_payload(project_data, group_data)
    content = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    st.sidebar.markdown('<div class="draft-sidebar-gap"></div>', unsafe_allow_html=True)
    with st.sidebar.container(border=True):
        st.markdown("**Черновик заполнения**")
        uploaded_file = st.file_uploader(
            "Загрузить черновик",
            type=["json"],
            key=f"draft_upload_{int(st.session_state.get('draft_upload_revision', 0))}",
            label_visibility="collapsed",
        )
        st.download_button(
            "Сохранить",
            data=content,
            file_name=_draft_download_filename(project_data),
            mime="application/json",
            key="draft_save",
            use_container_width=True,
        )
        if restored_notice:
            st.success(restored_notice)
        if restore_error:
            st.error(restore_error)
        if uploaded_file is None:
            return
        content = uploaded_file.getvalue()
        digest = str(hash(content))
        if st.session_state.get("last_loaded_draft_digest") == digest:
            return
        try:
            payload = json.loads(content.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError) as exc:
            st.error(f"Не удалось загрузить черновик: {exc}")
            return
        st.session_state.last_loaded_draft_digest = digest
        st.session_state.pending_draft_payload = payload
        st.rerun()


def _apply_pending_draft_restore() -> None:
    payload = st.session_state.pop("pending_draft_payload", None)
    if payload is None:
        return
    try:
        _apply_draft_payload(payload)
    except (ValueError, TypeError) as exc:
        st.session_state.draft_restore_error = f"Не удалось загрузить черновик: {exc}"
        _reset_draft_uploader()
        return
    st.session_state.draft_restore_notice = "Черновик загружен. Можно продолжать заполнение."
    _reset_draft_uploader()


def _reset_draft_uploader() -> None:
    revision = int(st.session_state.get("draft_upload_revision", 0) or 0)
    st.session_state.draft_upload_revision = revision + 1
    st.session_state.pop("last_loaded_draft_digest", None)


def _draft_payload(project_data: dict[str, Any], group_data: list[dict[str, Any]]) -> dict[str, Any]:
    active_sections = {
        str(index): section
        for index in range(len(group_data))
        if (section := _normalize_group_section_name(st.session_state.get(f"group_{index}_active_section")))
    }
    return {
        "type": DRAFT_FILE_KIND,
        "schema_version": DRAFT_SCHEMA_VERSION,
        "saved_at": date.today().isoformat(),
        "app_version": app_version_label(),
        "project": _json_ready(_drop_empty(project_data)),
        "groups": [_json_ready(_drop_empty(group)) for group in group_data],
        "active_group_index": int(st.session_state.get("active_group_index", 0) or 0),
        "active_sections": active_sections,
    }


def _apply_draft_payload(payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise ValueError("файл черновика должен содержать JSON-объект")
    if payload.get("type") != DRAFT_FILE_KIND:
        raise ValueError("это не файл черновика генератора EPSS")
    if int(payload.get("schema_version", 0) or 0) > DRAFT_SCHEMA_VERSION:
        raise ValueError("черновик создан в более новой версии приложения")

    project = _normalize_draft_project(payload.get("project", {}))
    groups = _normalize_draft_groups(payload.get("groups", []))
    active_group_index = _delete_group_index_value(payload.get("active_group_index", 0)) or 0
    active_group_index = min(max(0, active_group_index), len(groups) - 1)

    st.session_state.prefill_project = project
    _sync_project_widgets_from_draft(project)

    st.session_state.group_count = len(groups)
    st.session_state.prefill_groups = [{} for _ in groups]
    st.session_state.group_drafts = [dict(group) for group in groups]
    st.session_state.extracted_group_fields = [set() for _ in groups]
    st.session_state.active_group_index = active_group_index
    _sync_group_widgets_from_group_data(groups)
    st.session_state.active_group_index = active_group_index

    active_sections = payload.get("active_sections", {})
    if isinstance(active_sections, dict):
        for key, section in active_sections.items():
            index = _delete_group_index_value(key)
            normalized_section = _normalize_group_section_name(section)
            if index is not None and index < len(groups) and normalized_section:
                st.session_state[f"group_{index}_active_section"] = normalized_section


def _normalize_draft_project(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    allowed_fields = set(ProjectInfo.model_fields)
    project = {key: _parse_draft_value(item) for key, item in value.items() if key in allowed_fields}
    report_date = project.get("report_date")
    if isinstance(report_date, str) and report_date:
        try:
            project["report_date"] = date.fromisoformat(report_date)
        except ValueError:
            project.pop("report_date", None)
    return _drop_empty(project)


def _normalize_draft_groups(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return [{}]
    allowed_fields = {field for fields in FIELD_GROUPS.values() for field, _, _, _ in fields}
    groups = []
    for item in value:
        if not isinstance(item, dict):
            continue
        group = {
            key: _parse_draft_value(raw_value)
            for key, raw_value in item.items()
            if key in allowed_fields
        }
        groups.append(_drop_empty(group))
    return groups or [{}]


def _parse_draft_value(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return str(value).strip()


def _sync_project_widgets_from_draft(project: dict[str, Any]) -> None:
    for field in ("customer", "project_name", "address"):
        key = f"project_{field}"
        value = project.get(field)
        if value not in ("", None):
            st.session_state[key] = value
        else:
            st.session_state.pop(key, None)
    report_date = project.get("report_date")
    if isinstance(report_date, date):
        st.session_state["project_report_date"] = report_date
    else:
        st.session_state.pop("project_report_date", None)
    prepared_by = _normalize_preparer_surname(project.get("prepared_by"))
    if prepared_by:
        st.session_state["project_prepared_by"] = prepared_by


def _json_ready(value: Any) -> Any:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, set):
        return sorted(_json_ready(item) for item in value)
    return value


def _draft_download_filename(project_data: dict[str, Any]) -> str:
    project_name = str(project_data.get("project_name") or "").strip() or "Черновик_опросника"
    return f"{safe_filename(project_name)}_черновик_{date.today():%d.%m.%Y}.json"


def _render_lift_team_sidebar() -> str | None:
    prefill_project = st.session_state.get("prefill_project", {})
    prefilled_surname = _normalize_preparer_surname(prefill_project.get("prepared_by"))
    selected_surname = _normalize_preparer_surname(
        st.session_state.get("project_prepared_by", prefilled_surname)
    )
    if selected_surname:
        st.session_state["project_prepared_by"] = selected_surname

    with st.sidebar.container(border=True):
        selected_index = (
            LIFT_TEAM_SURNAMES.index(selected_surname)
            if selected_surname in LIFT_TEAM_SURNAMES
            else None
        )
        selected_style = (
            _selected_preparer_button_css(selected_index)
            if selected_index is not None
            else ""
        )
        st.markdown(
            '<div class="lift-team-sidebar-label">Заполняет:</div>'
            '<div class="lift-team-sidebar-gap"></div>'
            f"{selected_style}",
            unsafe_allow_html=True,
        )
        button_columns = st.columns(2, gap="small")
        for index, surname in enumerate(LIFT_TEAM_SURNAMES):
            with button_columns[index % 2]:
                st.button(
                    surname,
                    key=f"project_preparer_{index}",
                    type="secondary",
                    use_container_width=True,
                    on_click=_select_preparer_surname,
                    args=(surname,),
                )

        return _normalize_preparer_surname(st.session_state.get("project_prepared_by"))


def _select_preparer_surname(surname: str) -> None:
    selected_surname = _normalize_preparer_surname(surname)
    if selected_surname:
        st.session_state["project_prepared_by"] = selected_surname
        prefill_project = dict(st.session_state.get("prefill_project", {}))
        prefill_project["prepared_by"] = selected_surname
        st.session_state["prefill_project"] = prefill_project


def _normalize_preparer_surname(value: Any) -> str | None:
    surname = str(value or "").strip()
    if surname == "Другалев":
        surname = "Другалёв"
    return surname if surname in LIFT_TEAM_SURNAMES else None


def _selected_preparer_button_css(selected_index: int) -> str:
    key_class = f"st-key-project_preparer_{selected_index}"
    return f"""
        <style>
        section[data-testid="stSidebar"] [class*="st-key-project_preparer_"].{key_class} button,
        section[data-testid="stSidebar"] [class*="st-key-project_preparer_"].{key_class} button:hover,
        section[data-testid="stSidebar"] [class*="st-key-project_preparer_"].{key_class} button:focus,
        section[data-testid="stSidebar"] [class*="st-key-project_preparer_"].{key_class} button:focus-visible {{
            background: #e8f5ed !important;
            border: 1px solid #32a66a !important;
            box-shadow: 0 0 0 0.15rem rgba(50, 166, 106, 0.22) !important;
            color: #23784a !important;
            outline: none !important;
        }}

        section[data-testid="stSidebar"] [class*="st-key-project_preparer_"].{key_class} button p {{
            color: #23784a !important;
        }}
        </style>
    """


def _project_summary_from_state() -> dict[str, Any]:
    group_count = max(1, int(st.session_state.get("group_count", 1)))
    prefill_project = st.session_state.get("prefill_project", {})
    project_name = str(
        st.session_state.get("project_project_name", prefill_project.get("project_name")) or ""
    ).strip()
    lift_count = 0
    groups: list[dict[str, Any]] = []
    for index in range(group_count):
        defaults = _group_defaults(index)
        quantity = st.session_state.get(f"group_{index}_quantity", defaults.get("quantity"))
        lift_count += _parse_positive_int_silent(quantity) or 0
        groups.append({
            "quantity": quantity,
            "speed_ms": st.session_state.get(f"group_{index}_speed_ms", defaults.get("speed_ms")),
            "capacity_kg": st.session_state.get(
                f"group_{index}_capacity_kg", defaults.get("capacity_kg")
            ),
            "stops": st.session_state.get(f"group_{index}_stops", defaults.get("stops")),
        })
    return {
        "project_name": project_name,
        "group_count": group_count,
        "lift_count": lift_count,
        "lift_breakdown": _lift_summary_breakdown(groups),
    }


def _lift_summary_breakdown(groups: list[dict[str, Any]]) -> list[str]:
    quantities_by_spec: dict[tuple[str, int | None, int | None], int] = {}
    for group in groups:
        quantity = _parse_positive_int_silent(group.get("quantity"))
        if quantity is None:
            continue
        speed = _format_decimal_option(group.get("speed_ms")).replace(".", ",")
        capacity = _parse_positive_int_silent(group.get("capacity_kg"))
        stops = _parse_positive_int_silent(group.get("stops"))
        if not any((speed, capacity, stops)):
            continue
        spec = (speed, capacity, stops)
        quantities_by_spec[spec] = quantities_by_spec.get(spec, 0) + quantity

    lines: list[str] = []
    for (speed, capacity, stops), quantity in quantities_by_spec.items():
        details: list[str] = []
        if speed:
            details.append(f"{speed} м/с")
        if capacity is not None:
            details.append(f"{capacity} кг")
        if stops is not None:
            details.append(f"{stops} ост.")
        quantity_text = f"{quantity} {_lift_noun(quantity)}"
        lines.append(f"{quantity_text} — {', '.join(details)}")
    return lines


def _lift_noun(quantity: int) -> str:
    if quantity % 10 == 1 and quantity % 100 != 11:
        return "лифт"
    if quantity % 10 in {2, 3, 4} and quantity % 100 not in {12, 13, 14}:
        return "лифта"
    return "лифтов"


def _sync_group_widgets_from_prefill(groups: list[dict[str, Any]]) -> None:
    _sync_group_widgets_from_group_data(groups)


def _sync_group_widgets_from_group_data(groups: list[dict[str, Any]]) -> None:
    groups = [_group_with_lift_name_range(group) for group in groups]
    for key in list(st.session_state.keys()):
        key_parts = key.split("_", 2)
        if len(key_parts) == 3 and key_parts[0] == "group" and key_parts[1].isdigit():
            st.session_state.pop(key, None)

    st.session_state.group_drafts = [dict(group) for group in groups]
    for index, group in enumerate(groups):
        for fields in FIELD_GROUPS.values():
            for field, _, kind, _ in fields:
                value = group.get(field)
                if value not in ("", None):
                    st.session_state[f"group_{index}_{field}"] = _widget_state_value(kind, value)
    _refresh_group_section_widgets()


def _widget_state_value(kind: str, value: Any) -> Any:
    if kind in {"number", "text", "textarea", "capacity_select", "speed_select"}:
        return str(value)
    if kind == "checkbox_yes_no":
        return _truthy_yes_no(value)
    return value


def _project_block() -> dict[str, Any]:
    defaults = st.session_state.prefill_project
    prepared_by = st.session_state.get("project_prepared_by") or defaults.get("prepared_by")
    with st.expander("Данные проекта", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            customer = st.text_input(
                "Заказчик",
                value=str(defaults.get("customer") or ""),
                key="project_customer",
                placeholder=" ",
            )
            project_name = st.text_input(
                "Название объекта",
                value=str(defaults.get("project_name") or ""),
                key="project_project_name",
                placeholder=" ",
            )
        with col2:
            address = st.text_input(
                "Адрес объекта",
                value=str(defaults.get("address") or ""),
                key="project_address",
                placeholder=" ",
            )
            report_date = st.date_input(
                "Дата заполнения",
                value=defaults.get("report_date") or date.today(),
                key="project_report_date",
            )
    return {
        "project_name": project_name,
        "customer": customer,
        "address": address,
        "report_date": report_date,
        "prepared_by": prepared_by,
    }


def _groups_block(options: OptionsManager) -> list[dict[str, Any]]:
    _normalize_group_lists()
    _sync_group_lift_name_ranges_before_render()
    _clamp_active_group_selection()

    header_cols = st.columns([1.35, 2.35, 2.15, 4.15])
    with header_cols[0]:
        st.markdown('<span class="management-button-marker"></span>', unsafe_allow_html=True)
        if st.button("Добавить группу", use_container_width=True):
            _add_group()
            st.rerun()
    with header_cols[1]:
        st.markdown('<span class="management-button-marker"></span>', unsafe_allow_html=True)
        if st.button("Копировать выбранную группу", use_container_width=True):
            _copy_group(int(st.session_state.active_group_index))
            st.rerun()
    with header_cols[2]:
        st.markdown('<span class="management-button-marker"></span>', unsafe_allow_html=True)
        if st.button("Удалить выбранную группу", use_container_width=True):
            _delete_group(int(st.session_state.active_group_index))
            st.rerun()
    with header_cols[3]:
        st.markdown('<span class="management-button-marker"></span>', unsafe_allow_html=True)
        if st.button(
            "Перенести отделки и опции из выбранной группы",
            disabled=st.session_state.group_count <= 1,
            use_container_width=True,
        ):
            source_index = int(st.session_state.active_group_index)
            source_label = _group_display_label(source_index)
            _sync_common_fields_from_selected_group(source_index)
            st.session_state.group_sync_notice = (
                f"Отделки и опции перенесены из группы «{source_label}» "
                f"в остальные группы ({st.session_state.group_count - 1})."
            )
            st.rerun()

    nav_groups = [_collect_group_from_state(index, _group_defaults(index)) for index in range(st.session_state.group_count)]
    _render_group_navigation(nav_groups)
    group_sync_notice = st.session_state.pop("group_sync_notice", None)
    if group_sync_notice:
        st.success(group_sync_notice)

    groups = nav_groups
    index = int(st.session_state.active_group_index)
    defaults = _group_defaults(index)
    group = groups[index]
    with st.expander(_group_display_label(index), expanded=True):
        section_names = list(FIELD_GROUPS.keys())
        completed_sections = _completed_sections(group)
        active_section_key = f"group_{index}_active_section"
        stored_section = _normalize_group_section_name(st.session_state.get(active_section_key)) or section_names[0]
        st.session_state[active_section_key] = stored_section
        selected_additional_options_count = _selected_additional_options_count(group)
        section_widget_key = (
            f"{active_section_key}_widget_{int(st.session_state.group_section_widget_revision)}_"
            f"{selected_additional_options_count}"
        )
        widget_section = _normalize_group_section_name(st.session_state.get(section_widget_key))
        if widget_section is None:
            st.session_state[section_widget_key] = stored_section
        elif widget_section != st.session_state.get(section_widget_key):
            st.session_state[section_widget_key] = widget_section
        section = st.radio(
            "Раздел параметров",
            section_names,
            horizontal=True,
            label_visibility="collapsed",
            key=section_widget_key,
            format_func=lambda name: _section_display_label(name, completed_sections, group),
        )
        section = _normalize_group_section_name(section) or section_names[0]
        st.session_state[active_section_key] = section
        st.markdown('<div class="section-fields-spacer"></div>', unsafe_allow_html=True)
        fields = FIELD_GROUPS[section]
        if section == "Двери":
            upper_fields = [item for item in fields if item[0] not in DOOR_FINISH_FIELDS]
            finish_fields = [item for item in fields if item[0] in DOOR_FINISH_FIELDS]
            _render_group_field_grid(upper_fields, 2, group, defaults, options, index)
            st.markdown('<div class="section-fields-spacer"></div>', unsafe_allow_html=True)
            _render_group_field_grid(finish_fields, 2, group, defaults, options, index)
        else:
            has_visual_options = any(option_key in IMAGE_OPTION_DIRS for _, _, _, option_key in fields)
            column_count = 2 if has_visual_options else 3 if len(fields) >= 8 else 2
            if section == "Сигнализация":
                _render_signalization_fields(fields, group, defaults, options, index)
            else:
                _render_group_field_grid(fields, column_count, group, defaults, options, index)
            if section == "Сигнализация":
                _render_selected_image_previews(fields, group)
    groups[index] = group
    return groups


def _add_group() -> None:
    new_index = st.session_state.group_count
    st.session_state.group_count += 1
    st.session_state.prefill_groups.append({})
    st.session_state.group_drafts.append({})
    _activate_group(new_index)


def _copy_group(index: int) -> None:
    _normalize_group_lists()
    if index < 0 or index >= st.session_state.group_count:
        return

    current_groups = [
        _collect_group_from_state(group_index, _group_defaults(group_index))
        for group_index in range(st.session_state.group_count)
    ]
    copy_index = index + 1
    current_groups.insert(copy_index, dict(current_groups[index]))
    _renumber_following_group_lift_names(current_groups, index)

    extracted_fields = set(st.session_state.extracted_group_fields[index])
    st.session_state.extracted_group_fields.insert(copy_index, extracted_fields)
    prefill_groups = [dict(group) for group in st.session_state.prefill_groups]
    prefill_groups.insert(copy_index, {})
    st.session_state.prefill_groups = prefill_groups[: len(current_groups)]
    st.session_state.group_count = len(current_groups)
    _normalize_group_lists()
    st.session_state.active_group_index = copy_index
    _sync_group_widgets_from_group_data(current_groups)


def _render_group_field_grid(
    fields: list[tuple[str, str, str, str | None]],
    column_count: int,
    group: dict[str, Any],
    defaults: dict[str, Any],
    options: OptionsManager,
    group_index: int,
) -> None:
    cols = st.columns(column_count)
    for item_index, (field, label, kind, option_key) in enumerate(fields):
        with cols[item_index % column_count]:
            key = f"group_{group_index}_{field}"
            default = defaults.get(field)
            group[field] = _field_widget(label, kind, key, default, options, option_key, group_index, field)


def _render_group_field_rows(
    fields: list[tuple[str, str, str, str | None]],
    column_count: int,
    group: dict[str, Any],
    defaults: dict[str, Any],
    options: OptionsManager,
    group_index: int,
) -> None:
    for row_start in range(0, len(fields), column_count):
        cols = st.columns(column_count)
        for column_index, (field, label, kind, option_key) in enumerate(fields[row_start : row_start + column_count]):
            with cols[column_index]:
                key = f"group_{group_index}_{field}"
                default = defaults.get(field)
                group[field] = _field_widget(label, kind, key, default, options, option_key, group_index, field)


def _render_signalization_fields(
    fields: list[tuple[str, str, str, str | None]],
    group: dict[str, Any],
    defaults: dict[str, Any],
    options: OptionsManager,
    group_index: int,
) -> None:
    regular_fields = [item for item in fields if item[0] != "display_type"]
    display_fields = [item for item in fields if item[0] == "display_type"]
    _render_group_field_rows(regular_fields, 2, group, defaults, options, group_index)
    if display_fields:
        cols = st.columns([1, 1, 1])
        with cols[0]:
            field, label, kind, option_key = display_fields[0]
            key = f"group_{group_index}_{field}"
            default = defaults.get(field)
            group[field] = _field_widget(label, kind, key, default, options, option_key, group_index, field)


def _render_selected_image_previews(
    fields: list[tuple[str, str, str, str | None]],
    group: dict[str, Any],
) -> None:
    if _is_signalization_preview_fields(fields):
        _render_signalization_image_previews(fields, group)
        return

    preview_items = _selected_image_preview_items(fields, group)
    if not preview_items:
        return

    st.markdown('<div class="section-fields-spacer"></div>', unsafe_allow_html=True)
    st.markdown('<div class="selected-image-preview-wrap">', unsafe_allow_html=True)
    _render_image_card_grid(preview_items)
    st.markdown("</div>", unsafe_allow_html=True)


def _is_signalization_preview_fields(fields: list[tuple[str, str, str, str | None]]) -> bool:
    field_names = {field for field, _, _, _ in fields}
    return all(device_field in field_names and finish_field in field_names for device_field, finish_field in SIGNAL_PREVIEW_FIELD_PAIRS)


def _render_signalization_image_previews(
    fields: list[tuple[str, str, str, str | None]],
    group: dict[str, Any],
) -> None:
    preview_columns = _signalization_image_preview_columns(fields, group)
    if not preview_columns:
        return

    st.markdown('<div class="section-fields-spacer"></div>', unsafe_allow_html=True)
    st.markdown('<div class="selected-image-preview-wrap">', unsafe_allow_html=True)
    cols = st.columns(len(preview_columns))
    for column_index, column_items in enumerate(preview_columns):
        with cols[column_index]:
            for label, value, image_path in column_items:
                st.markdown(_selected_image_card_html(label, value, image_path), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def _signalization_image_preview_columns(
    fields: list[tuple[str, str, str, str | None]],
    group: dict[str, Any],
) -> list[list[tuple[str, str, Path]]]:
    field_meta = {field: (label, option_key) for field, label, _, option_key in fields}
    preview_columns: list[list[tuple[str, str, Path]]] = []
    for device_field, finish_field in SIGNAL_PREVIEW_FIELD_PAIRS:
        column_items = []
        for field in (device_field, finish_field):
            preview_item = _selected_image_preview_item(field, field_meta, group)
            if preview_item:
                column_items.append(preview_item)
        if column_items:
            preview_columns.append(column_items)
    return preview_columns


def _render_image_card_grid(preview_items: list[tuple[str, str, Path]], column_count: int = 3) -> None:
    columns_per_row = min(column_count, len(preview_items))
    for row_start in range(0, len(preview_items), columns_per_row):
        cols = st.columns(columns_per_row)
        for column_index, (label, value, image_path) in enumerate(preview_items[row_start : row_start + columns_per_row]):
            with cols[column_index]:
                st.markdown(_selected_image_card_html(label, value, image_path), unsafe_allow_html=True)


def _render_group_navigation(groups: list[dict[str, Any]]) -> None:
    nav_items = _group_navigation_items(groups)
    if not nav_items:
        return
    cols = st.columns(min(len(nav_items), 8))
    for item_index, (group_index, label) in enumerate(nav_items):
        with cols[item_index % len(cols)]:
            button_type = "primary" if group_index == st.session_state.active_group_index else "secondary"
            st.markdown('<span class="group-nav-button-marker"></span>', unsafe_allow_html=True)
            if st.button(label, key=f"group_nav_{group_index}", type=button_type, use_container_width=True):
                _activate_group(group_index)
                st.rerun()


def _activate_group(index: int) -> None:
    st.session_state.active_group_index = index
    _refresh_group_section_widgets()


def _refresh_group_section_widgets() -> None:
    revision = int(st.session_state.get("group_section_widget_revision", 0)) + 1
    st.session_state.group_section_widget_revision = revision
    for key in list(st.session_state.keys()):
        if re.fullmatch(r"group_\d+_active_section_widget_\d+(?:_\d+)?", str(key)):
            st.session_state.pop(key, None)


def _group_navigation_items(groups: list[dict[str, Any]]) -> list[tuple[int, str]]:
    items: list[tuple[int, str]] = []
    for index, group in enumerate(groups):
        capacity = group.get("capacity_kg")
        label = _format_group_display_label(group.get("lift_name"), group.get("quantity"), capacity)
        if not label:
            label = _append_capacity_to_group_label(f"Группа {index + 1}", capacity)
        items.append((index, label))
    return items


def _selected_image_preview_items(
    fields: list[tuple[str, str, str, str | None]],
    group: dict[str, Any],
) -> list[tuple[str, str, Path]]:
    preview_items: list[tuple[str, str, Path]] = []
    field_meta = {field: (label, option_key) for field, label, _, option_key in fields}
    for field, _, _, _ in fields:
        preview_item = _selected_image_preview_item(field, field_meta, group)
        if preview_item:
            preview_items.append(preview_item)
    return preview_items


def _selected_image_preview_item(
    field: str,
    field_meta: dict[str, tuple[str, str | None]],
    group: dict[str, Any],
) -> tuple[str, str, Path] | None:
    label, option_key = field_meta.get(field, ("", None))
    if option_key not in IMAGE_OPTION_DIRS:
        return None
    value = group.get(field)
    image_path = _image_path_for_value(option_key, value)
    if value and image_path:
        return (label, str(value), image_path)
    return None


def _group_display_label(index: int) -> str:
    defaults = _group_defaults(index)
    lift_name = st.session_state.get(f"group_{index}_lift_name", defaults.get("lift_name"))
    quantity = st.session_state.get(f"group_{index}_quantity", defaults.get("quantity"))
    capacity = st.session_state.get(f"group_{index}_capacity_kg", defaults.get("capacity_kg"))
    return _format_group_display_label(lift_name, quantity, capacity) or _append_capacity_to_group_label(
        f"Группа {index + 1}", capacity
    )


def _format_group_display_label(lift_name: Any, quantity: Any, capacity_kg: Any = None) -> str | None:
    text = str(lift_name or "").strip()
    if not text:
        return None
    count = _parse_positive_int_silent(quantity)
    label = _lift_name_for_quantity(text, count) if count is not None else text
    return _append_capacity_to_group_label(label, capacity_kg)


def _append_capacity_to_group_label(label: str, capacity_kg: Any) -> str:
    capacity = _parse_positive_int_silent(capacity_kg)
    return f"{label} ({capacity} кг)" if capacity is not None else label


def _parse_positive_int_silent(value: Any) -> int | None:
    if value in ("", None):
        return None
    try:
        number = int(float(str(value).replace(",", ".")))
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _lift_name_range(lift_name: str, quantity: int) -> str | None:
    return _lift_name_for_quantity(lift_name, quantity)


def _lift_name_for_quantity(lift_name: Any, quantity: Any) -> str:
    text = str(lift_name or "").strip()
    count = _parse_positive_int_silent(quantity)
    if not text or count is None:
        return text
    match = re.match(r"^(.*?)(\d+)([^0-9–—-]*)", text)
    if not match:
        return text
    prefix, start_text, suffix = match.groups()
    start = int(start_text)
    start_label = f"{prefix}{start_text}{suffix}"
    if count <= 1:
        return start_label
    end = start + count - 1
    width = len(start_text) if start_text.startswith("0") else 0
    end_text = f"{end:0{width}d}" if width else str(end)
    return f"{start_label}-{prefix}{end_text}{suffix}"


def _next_group_lift_name(lift_name: Any, quantity: Any) -> str | None:
    text = str(lift_name or "").strip()
    count = _parse_positive_int_silent(quantity)
    if not text or count is None:
        return None
    match = re.match(r"^(.*?)(\d+)([^0-9–—-]*)", text)
    if not match:
        return None
    prefix, start_text, suffix = match.groups()
    next_number = int(start_text) + count
    width = len(start_text) if start_text.startswith("0") else 0
    next_text = f"{next_number:0{width}d}" if width else str(next_number)
    return f"{prefix}{next_text}{suffix}"


def _renumber_following_group_lift_names(groups: list[dict[str, Any]], anchor_index: int) -> None:
    for index in range(anchor_index + 1, len(groups)):
        previous = groups[index - 1]
        next_name = _next_group_lift_name(previous.get("lift_name"), previous.get("quantity"))
        if next_name is None:
            break
        groups[index]["lift_name"] = _lift_name_for_quantity(next_name, groups[index].get("quantity"))


def _group_with_lift_name_range(group: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(group)
    lift_name = _lift_name_for_quantity(normalized.get("lift_name"), normalized.get("quantity"))
    if lift_name:
        normalized["lift_name"] = lift_name
    return normalized


def _sync_group_lift_name_ranges_before_render() -> None:
    for index in range(st.session_state.group_count):
        prefill = st.session_state.prefill_groups[index]
        draft = st.session_state.group_drafts[index]
        lift_name_key = f"group_{index}_lift_name"
        quantity_key = f"group_{index}_quantity"
        lift_name = st.session_state.get(
            lift_name_key,
            draft.get("lift_name", prefill.get("lift_name")),
        )
        quantity = st.session_state.get(
            quantity_key,
            draft.get("quantity", prefill.get("quantity")),
        )
        updated_lift_name = _lift_name_for_quantity(lift_name, quantity)
        if not updated_lift_name:
            continue
        prefill["lift_name"] = updated_lift_name
        draft["lift_name"] = updated_lift_name
        st.session_state[lift_name_key] = updated_lift_name


def _renumber_following_group_lift_names_in_state(anchor_index: int) -> None:
    _normalize_group_lists()
    if anchor_index < 0 or anchor_index >= st.session_state.group_count:
        return
    groups = [
        _collect_group_from_state(index, _group_defaults(index))
        for index in range(st.session_state.group_count)
    ]
    _renumber_following_group_lift_names(groups, anchor_index)
    for index in range(anchor_index + 1, len(groups)):
        lift_name = groups[index].get("lift_name")
        if lift_name in ("", None):
            continue
        _ensure_group_draft(index)["lift_name"] = lift_name
        st.session_state.prefill_groups[index]["lift_name"] = lift_name
        st.session_state[f"group_{index}_lift_name"] = lift_name


def _sync_group_lift_name_range_in_state(group_index: int) -> None:
    _normalize_group_lists()
    if group_index < 0 or group_index >= st.session_state.group_count:
        return
    defaults = _group_defaults(group_index)
    lift_name_key = f"group_{group_index}_lift_name"
    quantity_key = f"group_{group_index}_quantity"
    lift_name = st.session_state.get(lift_name_key, defaults.get("lift_name"))
    quantity = st.session_state.get(quantity_key, defaults.get("quantity"))
    updated_lift_name = _lift_name_for_quantity(lift_name, quantity)
    if not updated_lift_name:
        return
    _ensure_group_draft(group_index)["lift_name"] = updated_lift_name
    st.session_state.prefill_groups[group_index]["lift_name"] = updated_lift_name
    st.session_state[lift_name_key] = updated_lift_name


def _completed_sections(group: dict[str, Any]) -> set[str]:
    return {section for section in FIELD_GROUPS if _section_is_complete(section, group)}


def _section_is_complete(section: str, group: dict[str, Any]) -> bool:
    return all(
        _field_is_complete(field, group)
        for field, _, _, _ in FIELD_GROUPS[section]
    )


def _field_is_complete(field: str, group: dict[str, Any]) -> bool:
    if field in ADDITIONAL_OPTION_TRANSLATIONS:
        return True
    paired_source = _paired_finish_source_field(field)
    if paired_source:
        source_value = group.get(paired_source)
        if _is_no_finish_required_value(source_value):
            return True
    return _is_filled_value(group.get(field))


def _paired_finish_source_field(finish_field: str) -> str | None:
    for source_field, paired_finish_field in {**SIGNAL_FINISH_FIELDS, **CABIN_COMPONENT_FINISH_FIELDS}.items():
        if paired_finish_field == finish_field:
            return source_field
    return None


def _is_no_finish_required_value(value: Any) -> bool:
    if not _is_filled_value(value):
        return True
    text = str(value).strip().lower()
    return text == "нет" or text.startswith("без ")


def _is_filled_value(value: Any) -> bool:
    return value not in ("", None, OTHER_OPTION)


def _section_display_label(
    section: str,
    completed_sections: set[str],
    group: dict[str, Any] | None = None,
) -> str:
    if section == "Дополнительные опции":
        return f"{section} ({_selected_additional_options_count(group or {})})"
    return f"{section} {SECTION_COMPLETE_MARK}" if section in completed_sections else section


def _selected_additional_options_count(group: dict[str, Any]) -> int:
    fields = (field for field, _, _, _ in FIELD_GROUPS["Дополнительные опции"])
    return sum(1 for field in fields if _truthy_yes_no(group.get(field)))


def _normalize_group_section_name(value: Any) -> str | None:
    if value in ("", None):
        return None
    section = str(value).strip()
    if section == "Дополнительно":
        section = "Дополнительные опции"
    section = re.sub(r"\s+\(\d+\)$", "", section)
    if section.endswith(SECTION_COMPLETE_MARK):
        section = section[: -len(SECTION_COMPLETE_MARK)].rstrip()
    return section if section in FIELD_GROUPS else None


def _normalize_group_lists() -> None:
    group_count = max(1, int(st.session_state.group_count))
    st.session_state.group_count = group_count

    while len(st.session_state.prefill_groups) < group_count:
        st.session_state.prefill_groups.append({})
    while len(st.session_state.group_drafts) < group_count:
        st.session_state.group_drafts.append({})
    while len(st.session_state.extracted_group_fields) < group_count:
        st.session_state.extracted_group_fields.append(set())

    st.session_state.prefill_groups = st.session_state.prefill_groups[:group_count]
    st.session_state.group_drafts = st.session_state.group_drafts[:group_count]
    st.session_state.extracted_group_fields = st.session_state.extracted_group_fields[:group_count]


def _clamp_active_group_selection() -> None:
    max_index = max(0, st.session_state.group_count - 1)
    selected = _delete_group_index_value(st.session_state.get("active_group_index", 0))
    if selected is None:
        st.session_state.active_group_index = 0
    elif selected > max_index:
        st.session_state.active_group_index = max_index
    else:
        st.session_state.active_group_index = selected


def _delete_group_index_value(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if value in ("", None):
        return None
    text = str(value).strip()
    if text.isdigit():
        return int(text)
    return None


def _delete_group(index: int) -> None:
    _normalize_group_lists()
    if index < 0 or index >= st.session_state.group_count:
        return

    if st.session_state.group_count == 1:
        st.session_state.group_count = 1
        st.session_state.prefill_groups = [{}]
        st.session_state.extracted_group_fields = [set()]
        _sync_group_widgets_from_group_data([{}])
        return

    current_groups = [_collect_group_from_state(i, _group_defaults(i)) for i in range(st.session_state.group_count)]
    deleted_lift_name = current_groups[index].get("lift_name")
    current_groups.pop(index)
    st.session_state.prefill_groups.pop(index)
    st.session_state.extracted_group_fields.pop(index)

    if index < len(current_groups) and deleted_lift_name not in ("", None):
        current_groups[index]["lift_name"] = deleted_lift_name
        _renumber_following_group_lift_names(current_groups, index)
    elif index > 0:
        _renumber_following_group_lift_names(current_groups, index - 1)
    for group_index in range(index, len(current_groups)):
        lift_name = current_groups[group_index].get("lift_name")
        if lift_name not in ("", None):
            st.session_state.prefill_groups[group_index]["lift_name"] = lift_name

    st.session_state.group_count = len(current_groups)
    _sync_group_widgets_from_group_data(current_groups)


def _sync_common_fields_from_selected_group(source_index: int) -> None:
    _normalize_group_lists()
    if source_index < 0 or source_index >= st.session_state.group_count:
        return

    active_sections = {
        index: _normalize_group_section_name(st.session_state.get(f"group_{index}_active_section"))
        for index in range(st.session_state.group_count)
    }
    groups = [
        _collect_group_from_state(index, _group_defaults(index))
        for index in range(st.session_state.group_count)
    ]
    source = dict(groups[source_index])
    for index in range(st.session_state.group_count):
        if index == source_index:
            continue
        target = groups[index]
        for field in SYNCABLE_GROUP_FIELDS:
            value = source.get(field)
            if value in ("", None, OTHER_OPTION):
                target.pop(field, None)
            else:
                target[field] = value

    st.session_state.prefill_groups = [dict(group) for group in groups]
    _sync_group_widgets_from_group_data(groups)
    for index, section in active_sections.items():
        if section:
            st.session_state[f"group_{index}_active_section"] = section


def _field_kind(field_name: str) -> str:
    for fields in FIELD_GROUPS.values():
        for field, _, kind, _ in fields:
            if field == field_name:
                return kind
    return "text"


def _ensure_group_draft(index: int) -> dict[str, Any]:
    while len(st.session_state.group_drafts) <= index:
        st.session_state.group_drafts.append({})
    return st.session_state.group_drafts[index]


def _group_defaults(index: int) -> dict[str, Any]:
    prefill = st.session_state.prefill_groups[index] if index < len(st.session_state.prefill_groups) else {}
    draft = _ensure_group_draft(index)
    merged = dict(prefill)
    merged.update({key: value for key, value in draft.items() if value not in ("", None)})
    merged.setdefault("lift_type", DEFAULT_LIFT_TYPE)
    merged.setdefault("main_landing_floor", DEFAULT_MAIN_LANDING_FLOOR)
    merged.setdefault("machine_room", DEFAULT_MACHINE_ROOM)
    merged["shaft_material"] = _normalize_shaft_material(merged.get("shaft_material")) or DEFAULT_SHAFT_MATERIAL
    merged["seismic"] = _normalize_seismic(merged.get("seismic")) or DEFAULT_SEISMIC
    merged.setdefault("fire_resistance", DEFAULT_FIRE_RESISTANCE)
    merged.setdefault("door_model", DEFAULT_DOOR_MODEL)
    return merged


def _collect_group_from_state(index: int, defaults: dict[str, Any]) -> dict[str, Any]:
    group: dict[str, Any] = {}
    draft = _ensure_group_draft(index)
    for fields in FIELD_GROUPS.values():
        for field, _, kind, option_key in fields:
            key = f"group_{index}_{field}"
            value = st.session_state.get(key, draft.get(field, defaults.get(field)))
            if value == OTHER_OPTION:
                value = st.session_state.get(f"{key}_custom")
            if kind == "checkbox_yes_no":
                if field in ADDITIONAL_OPTION_TRANSLATIONS:
                    if not _truthy_yes_no(value):
                        draft.pop(field, None)
                        continue
                    value = "ДА"
                else:
                    value = "ДА" if _truthy_yes_no(value) else "НЕТ"
            if value not in ("", None, OTHER_OPTION):
                value = _storage_value_for_option(option_key, value)
                if field == "shaft_material":
                    value = _normalize_shaft_material(value)
                if option_key == "finish" and st.session_state.get(key) not in ("", None, OTHER_OPTION, value):
                    st.session_state[key] = value
                group[field] = value
                draft[field] = value
    if group.get("stops") not in ("", None):
        _apply_stops_derived_fields(index, group.get("stops"))
        if not _is_through_cabin_for_group(index, draft):
            group["doors_count"] = draft.get("doors_count")
        group["button_marking"] = draft.get("button_marking")
    return group


def _field_widget(
    label: str,
    kind: str,
    key: str,
    default: Any,
    options: OptionsManager,
    option_key: str | None,
    group_index: int,
    field: str,
) -> Any:
    default = _apply_pending_widget_choice(key, group_index, field, default)
    if field == "main_landing_floor":
        return _main_landing_floor_widget(label, key, default, group_index, field)
    if kind == "speed_select":
        values = [""] + SPEED_OPTIONS_MS
        current = _format_decimal_option(default)
        state_value = _format_decimal_option(st.session_state.get(key))
        if state_value and state_value not in values:
            values.append(state_value)
        if current and current not in values:
            values.append(current)
        index = values.index(current) if current in values else 0
        selected = st.selectbox(
            label,
            values,
            index=index,
            key=key,
            on_change=_save_group_widget_value,
            args=(group_index, field, key),
        )
        return _parse_number(str(selected), key) if selected else None
    if kind == "capacity_select":
        values = [""] + [str(value) for value in CAPACITY_OPTIONS_KG]
        current = "" if default is None else str(_parse_number(str(default), key) or default)
        state_value = st.session_state.get(key)
        if state_value not in (None, ""):
            state_value = str(_parse_number(str(state_value), key) or state_value)
        if state_value not in (None, "") and state_value not in values:
            values.append(str(state_value))
        if current and current not in values:
            values.append(current)
        index = values.index(current) if current in values else 0
        selected = st.selectbox(
            label,
            values,
            index=index,
            key=key,
            on_change=_save_group_widget_value,
            args=(group_index, field, key),
        )
        return _parse_number(str(selected), key) if selected else None
    if kind == "number":
        value = st.text_input(
            label,
            value="" if default is None else str(default),
            key=key,
            placeholder=" ",
            on_change=_save_group_widget_value,
            args=(group_index, field, key),
        )
        if field == "doors_count" and _is_through_cabin_for_group(group_index, _ensure_group_draft(group_index)):
            st.caption("Для проходного лифта проверьте количество дверей: оно может отличаться от количества остановок.")
        return _parse_number(value, key)
    if kind == "textarea":
        return st.text_area(
            label,
            value=str(default or ""),
            key=key,
            height=100,
            placeholder=" ",
            on_change=_save_group_widget_value,
            args=(group_index, field, key),
        )
    if kind == "checkbox_yes_no":
        current = _truthy_yes_no(st.session_state.get(key, default))
        checked = st.checkbox(
            label,
            value=current,
            key=key,
            on_change=_save_group_checkbox_value,
            args=(group_index, field, key),
        )
        return "ДА" if checked else "НЕТ"
    if kind == "select" and option_key:
        values = _select_values(options, option_key, field)
        if field not in SELECT_WITHOUT_EMPTY_FIELDS:
            values = [""] + values
        allows_custom = option_key not in SELECT_WITHOUT_CUSTOM_OPTION_KEYS and field not in SELECT_WITHOUT_CUSTOM_FIELDS
        if allows_custom:
            values.append(OTHER_OPTION)
        state_value = st.session_state.get(key)
        if state_value not in (None, "") and state_value not in values:
            insert_at = max(1, len(values) - (0 if not allows_custom else 1))
            if option_key not in STRICT_SELECT_OPTION_KEYS and _is_allowed_select_value(option_key, str(state_value), field):
                values.insert(insert_at, str(state_value))
        current = str(default or "")
        index = values.index(current) if current in values else 0
        if _has_image_options(option_key):
            selected = _image_select_widget(
                label,
                values,
                index,
                key,
                option_key,
                group_index,
                field,
            )
        else:
            selected = st.selectbox(
                label,
                values,
                index=index,
                key=key,
                on_change=_save_group_widget_value,
                args=(group_index, field, key),
            )
        if selected == OTHER_OPTION:
            custom = st.text_input(
                f"{label}: другое значение",
                key=f"{key}_custom",
                placeholder=" ",
                on_change=_save_group_custom_value,
                args=(group_index, field, f"{key}_custom"),
            )
            if custom:
                options.add(option_key, custom)
            return custom
        return selected or None
    return st.text_input(
        label,
        value=str(default or ""),
        key=key,
        placeholder=" ",
        on_change=_save_group_widget_value,
        args=(group_index, field, key),
    ) or None


def _main_landing_floor_widget(label: str, key: str, default: Any, group_index: int, field: str) -> str | None:
    draft = _ensure_group_draft(group_index)
    underground_floors = _underground_floors_for_group(group_index, draft)
    if underground_floors <= 0:
        return st.text_input(
            label,
            value=str(default or ""),
            key=key,
            placeholder=" ",
            on_change=_save_group_widget_value,
            args=(group_index, field, key),
        ) or None

    stops = _stops_for_group(group_index, draft)
    values = _main_landing_floor_options(underground_floors, stops)
    current = str(default or "")
    state_value = st.session_state.get(key)
    if state_value not in (None, ""):
        state_value = str(state_value)
    for value in (state_value, current):
        if value and value not in values:
            values.append(value)
    index = values.index(current) if current in values else 0
    selected = st.selectbox(
        label,
        values,
        index=index,
        key=key,
        on_change=_save_group_widget_value,
        args=(group_index, field, key),
        accept_new_options=True,
    )
    return str(selected).strip() if selected not in ("", None) else None


def _main_landing_floor_options(underground_floors: int, stops: int | None = None) -> list[str]:
    underground_count = max(0, int(underground_floors))
    if underground_count <= 0:
        return []
    underground_options = [str(floor) for floor in range(-min(2, underground_count), 0)]
    if stops is None:
        main_count = 2
    else:
        main_count = max(1, min(2, int(stops) - underground_count))
    return [*underground_options, *[str(floor) for floor in range(1, main_count + 1)]]


def _select_values(options: OptionsManager, option_key: str, field: str | None = None) -> list[str]:
    image_values = list(_image_options_for_key(option_key).keys())
    manual_values = MANUAL_OPTION_VALUES.get(option_key, []) + MANUAL_FIELD_OPTION_VALUES.get(field or "", [])
    configured_values = options.get(option_key)
    merged: list[str] = []
    for value in image_values + manual_values + configured_values:
        value = _normalize_select_option_value(option_key, value)
        if value and value not in merged and _is_allowed_select_value(option_key, value, field):
            merged.append(value)
    return merged


def _normalize_select_option_value(option_key: str | None, value: Any) -> str:
    if option_key == "shaft_material":
        return _normalize_shaft_material(value) or ""
    if option_key == "seismic":
        return _normalize_seismic(value) or ""
    return str(value)


def _normalize_shaft_material(value: Any) -> str | None:
    if value in ("", None, OTHER_OPTION):
        return None
    text = str(value).strip()
    normalized = text.casefold()
    if normalized in {"бетонная", "бетон", "железобетон", "ж/б", "жб", "монолитная", "монолит"}:
        return "Железобетон"
    return text


def _normalize_seismic(value: Any) -> str | None:
    if value in ("", None, OTHER_OPTION):
        return None
    text = str(value).strip()
    normalized = text.casefold()
    if normalized in {"нет", "нeт", "no", "none", "нет."}:
        return "НЕТ"
    allowed = {"НЕТ", "6 баллов", "7 баллов", "8 баллов", "9 баллов"}
    return text if text in allowed else None


def _is_allowed_select_value(option_key: str | None, value: str, field: str | None = None) -> bool:
    if value in EXCLUDED_SELECT_OPTION_VALUES.get(option_key or "", set()):
        return False
    return value not in EXCLUDED_FIELD_SELECT_OPTION_VALUES.get(field or "", set())


def _image_select_widget(
    label: str,
    values: list[str],
    index: int,
    key: str,
    option_key: str,
    group_index: int,
    field: str,
) -> Any:
    st.markdown(f'<div class="image-picker-label">{html.escape(label)}</div>', unsafe_allow_html=True)
    show_inline_preview = option_key in INLINE_PREVIEW_OPTION_KEYS
    columns = [4.8, 0.55, 1.55] if show_inline_preview else [4.8, 1.55]
    field_cols = st.columns(columns, gap="small")
    select_col = field_cols[0]
    picker_col = field_cols[-1]
    with select_col:
        selected = st.selectbox(
            label,
            values,
            index=index,
            key=key,
            label_visibility="collapsed",
            on_change=_save_group_widget_value,
            args=(group_index, field, key),
        )
    if show_inline_preview:
        with field_cols[1]:
            preview_path = _image_path_for_value(option_key, selected)
            st.markdown(_image_preview_html(preview_path), unsafe_allow_html=True)
    with picker_col:
        _image_option_picker(label, option_key, key, group_index, field)
    return selected


def _has_image_options(option_key: str) -> bool:
    return bool(_image_options_for_key(option_key))


def _image_options_for_key(option_key: str) -> dict[str, Path]:
    folder = _image_option_dir_for_key(option_key)
    if not folder or not folder.exists():
        return {}
    files = [
        path
        for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
        and not _is_excluded_image_option(option_key, path)
        and _matches_image_option_filter(option_key, path)
    ]
    options = {_image_option_label(path, option_key): path for path in files}
    return dict(sorted(options.items(), key=lambda item: _image_option_sort_key(option_key, item[0], item[1])))


def _image_option_dir_for_key(option_key: str) -> Path | None:
    folder = IMAGE_OPTION_DIRS.get(option_key)
    if folder and folder.exists():
        return folder
    fallback_folder = FALLBACK_IMAGE_OPTION_DIRS.get(option_key)
    if fallback_folder and fallback_folder.exists():
        return fallback_folder
    return folder


def _image_option_sort_key(option_key: str, label: str, path: Path) -> list[Any]:
    if option_key in {"finish", "signal_steel_finish", "ceiling_steel_finish", "floor_finish"}:
        article = _normalized_file_article(path)
        return [_material_image_sort_group(article), *_natural_sort_key(article)]
    return _natural_sort_key(label)


def _material_image_sort_group(article: str) -> int:
    for prefix, group in MATERIAL_IMAGE_SORT_PREFIXES.items():
        if article.startswith(prefix):
            return group
    return 99


def _matches_image_option_filter(option_key: str, path: Path) -> bool:
    prefixes = IMAGE_OPTION_PREFIX_FILTERS.get(option_key)
    if not prefixes:
        return True
    article = _normalized_file_article(path)
    return any(article.startswith(prefix) for prefix in prefixes)


def _is_excluded_image_option(option_key: str, path: Path) -> bool:
    excluded_articles = EXCLUDED_IMAGE_OPTION_ARTICLES.get(option_key, set())
    if not excluded_articles:
        return False
    article = _normalized_file_article(path)
    compact_article = article.replace(" ", "-")
    return article in excluded_articles or compact_article in excluded_articles


def _normalized_file_article(path: Path) -> str:
    return re.sub(r"\s+", " ", path.stem.replace("_", " ")).strip().upper()


def _image_option_label(path: Path, option_key: str | None = None) -> str:
    article = re.sub(r"\s+", " ", path.stem.replace("_", " ")).strip()
    if option_key == "mirror":
        return _mirror_value_with_description(article)
    name = _name_for_article(option_key, article)
    return f"{name} {article}" if name else article


def _name_for_article(option_key: str | None, article: str) -> str | None:
    if option_key in {"finish", "signal_steel_finish", "ceiling_steel_finish"}:
        return _material_name_for_article(article)
    if option_key == "floor_finish":
        return _floor_name_for_article(article)
    return None


def _material_name_for_article(article: str) -> str | None:
    normalized_article = article.upper().replace("_", " ").strip()
    if normalized_article in MATERIAL_ARTICLE_NAMES:
        return MATERIAL_ARTICLE_NAMES[normalized_article]
    for prefix, material_name in MATERIAL_PREFIX_NAMES:
        if normalized_article.startswith(prefix):
            return material_name
    return None


def _floor_name_for_article(article: str) -> str | None:
    normalized_article = article.upper().replace("_", " ").strip()
    for prefix, floor_name in FLOOR_PREFIX_NAMES:
        if normalized_article.startswith(prefix):
            return floor_name
    return None


def _storage_value_for_option(option_key: str | None, value: Any) -> Any:
    if option_key == "seismic":
        return _normalize_seismic(value)
    if option_key == "mirror" and value not in ("", None, OTHER_OPTION):
        return _mirror_value_with_description(str(value).strip())
    if option_key not in {"finish", "floor_finish", "signal_steel_finish", "ceiling_steel_finish"} or value in ("", None, OTHER_OPTION):
        return value
    text = str(value).strip()
    name = _name_for_article(option_key, text)
    return f"{name} {text}" if name else value


def _mirror_value_with_description(value: str) -> str:
    article = _mirror_article_from_value(value)
    if not article:
        return value
    description = MIRROR_ARTICLE_DESCRIPTIONS.get(article)
    return f"{article}, {description}" if description else value


def _mirror_article_from_value(value: str) -> str | None:
    match = re.search(r"\bMEX[\s-]*(\d+)\b", value.upper())
    if not match:
        return None
    return f"MEX-{int(match.group(1))}"


def _natural_sort_key(value: str) -> list[Any]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", value)]


def _image_option_picker(label: str, option_key: str, key: str, group_index: int, field: str) -> None:
    image_options = _image_options_for_key(option_key)
    if not image_options:
        return

    if st.button("Фото", key=f"{key}_photo_open", use_container_width=True):
        _image_picker_dialog(label, option_key, key, group_index, field)


@st.dialog("Выбор по фото")
def _image_picker_dialog(label: str, option_key: str, key: str, group_index: int, field: str) -> None:
    image_options = _image_options_for_key(option_key)
    st.caption(label)
    items = list(image_options.items())
    for row_start in range(0, len(items), 4):
        cols = st.columns(4)
        for item_index, (option_label, image_path) in enumerate(items[row_start : row_start + 4], start=row_start):
            with cols[item_index % 4]:
                st.markdown(_dialog_image_tile_html(option_label, image_path), unsafe_allow_html=True)
                if st.button("Выбрать", key=f"{key}_image_{item_index}", use_container_width=True):
                    st.session_state[key] = option_label
                    _ensure_group_draft(group_index)[field] = option_label
                    _sync_empty_wall_finish_fields(group_index, field, option_label)
                    st.rerun()


def _image_preview_html(path: Path | None) -> str:
    if not path or not path.exists():
        return '<div class="image-picker-thumb"></div>'
    mime_type = "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else f"image/{path.suffix.lower().lstrip('.')}"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return (
        '<div class="image-picker-thumb">'
        f'<img src="data:{mime_type};base64,{encoded}" alt="{html.escape(path.stem)}">'
        "</div>"
    )


def _selected_image_card_html(label: str, value: str, path: Path) -> str:
    mime_type = "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else f"image/{path.suffix.lower().lstrip('.')}"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return (
        '<div class="selected-image-card">'
        f'<img src="data:{mime_type};base64,{encoded}" alt="{html.escape(value)}">'
        "<div>"
        f'<div class="selected-image-card-title">{html.escape(label)}</div>'
        f'<div class="selected-image-card-value">{html.escape(value)}</div>'
        "</div>"
        "</div>"
    )


def _dialog_image_tile_html(label: str, path: Path) -> str:
    mime_type = "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else f"image/{path.suffix.lower().lstrip('.')}"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return (
        '<div class="image-dialog-tile">'
        f'<div class="image-dialog-image"><img src="data:{mime_type};base64,{encoded}" alt="{html.escape(label)}"></div>'
        f'<div class="image-dialog-label">{html.escape(label)}</div>'
        "</div>"
    )


def _apply_pending_widget_choice(key: str, group_index: int, field: str, default: Any) -> Any:
    pending_key = f"{key}_pending_choice"
    if pending_key not in st.session_state:
        return default
    pending_value = st.session_state.pop(pending_key)
    st.session_state.pop(key, None)
    _ensure_group_draft(group_index)[field] = pending_value
    return pending_value


def _image_path_for_value(option_key: str, value: Any) -> Path | None:
    if value in ("", None, OTHER_OPTION):
        return None
    normalized_value = _normalize_article_value(str(value))
    if not normalized_value:
        return None
    image_options = _image_options_for_key(option_key)
    for label, image_path in image_options.items():
        if _normalize_article_value(label) == normalized_value:
            return image_path
    for label, image_path in sorted(
        image_options.items(),
        key=lambda item: len(_normalize_article_value(item[0])),
        reverse=True,
    ):
        normalized_label = _normalize_article_value(label)
        if normalized_label and (normalized_label in normalized_value or normalized_value in normalized_label):
            return image_path
    return None


def _normalize_article_value(value: str) -> str:
    cyrillic_to_latin = str.maketrans(
        {
            "А": "A",
            "В": "B",
            "Е": "E",
            "К": "K",
            "М": "M",
            "Н": "H",
            "О": "O",
            "Р": "P",
            "С": "C",
            "Т": "T",
            "У": "Y",
            "Х": "X",
        }
    )
    normalized = value.upper().translate(cyrillic_to_latin)
    return re.sub(r"[^A-Z0-9]+", "", normalized)


def _save_group_widget_value(group_index: int, field: str, key: str) -> None:
    value = st.session_state.get(key)
    if value == OTHER_OPTION:
        return
    draft = _ensure_group_draft(group_index)
    if value in ("", None):
        draft.pop(field, None)
    else:
        draft[field] = value
        _sync_empty_wall_finish_fields(group_index, field, value)
    if field == "stops":
        _apply_stops_derived_fields(group_index, value)
    if field == "cabin_type":
        stops_value = st.session_state.get(f"group_{group_index}_stops", draft.get("stops"))
        _apply_stops_derived_fields(group_index, stops_value)
    if field == "underground_floors":
        stops_value = st.session_state.get(f"group_{group_index}_stops", draft.get("stops"))
        _apply_stops_derived_fields(group_index, stops_value)
    if field in {"lift_name", "quantity"}:
        _sync_group_lift_name_range_in_state(group_index)
        _renumber_following_group_lift_names_in_state(group_index)


def _save_group_custom_value(group_index: int, field: str, key: str) -> None:
    value = st.session_state.get(key)
    draft = _ensure_group_draft(group_index)
    if value in ("", None):
        draft.pop(field, None)
    else:
        draft[field] = value
        _sync_empty_wall_finish_fields(group_index, field, value)


def _save_group_checkbox_value(group_index: int, field: str, key: str) -> None:
    draft = _ensure_group_draft(group_index)
    checked = bool(st.session_state.get(key))
    if field in ADDITIONAL_OPTION_TRANSLATIONS and not checked:
        draft.pop(field, None)
        return
    draft[field] = "ДА" if checked else "НЕТ"
    if field == MGN_ACCESSIBILITY_FIELD and checked:
        voice_key = f"group_{group_index}_{MGN_VOICE_OPTION_FIELD}"
        st.session_state[voice_key] = True
        draft[MGN_VOICE_OPTION_FIELD] = "ДА"


def _truthy_yes_no(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().upper() in {"ДА", "YES", "TRUE", "1"}


def _sync_empty_wall_finish_fields(group_index: int, source_field: str, value: Any) -> None:
    if source_field not in WALL_FINISH_FIELDS or value in ("", None, OTHER_OPTION):
        return
    draft = _ensure_group_draft(group_index)
    for field in (*WALL_FINISH_FIELDS, *WALL_LINKED_FINISH_FIELDS):
        if field == source_field:
            continue
        paired_source = _paired_finish_source_field(field)
        if paired_source:
            paired_value = st.session_state.get(f"group_{group_index}_{paired_source}", draft.get(paired_source))
            if _is_filled_value(paired_value) and _is_no_finish_required_value(paired_value):
                continue
        key = f"group_{group_index}_{field}"
        current_value = st.session_state.get(key, draft.get(field))
        if current_value in ("", None, OTHER_OPTION):
            draft[field] = value
            st.session_state[key] = value


def _apply_stops_derived_fields(group_index: int, stops_value: Any) -> None:
    stops = _parse_number(str(stops_value), f"group_{group_index}_stops")
    if stops is None:
        return
    stops = int(stops)
    if stops <= 0:
        return

    draft = _ensure_group_draft(group_index)
    underground_floors = _underground_floors_for_group(group_index, draft)
    button_marking = _button_marking_from_stops(stops, underground_floors)
    draft["button_marking"] = button_marking
    if not _is_through_cabin_for_group(group_index, draft):
        draft["doors_count"] = stops
        st.session_state[f"group_{group_index}_doors_count"] = str(stops)
    st.session_state[f"group_{group_index}_button_marking"] = button_marking


def _is_through_cabin_for_group(group_index: int, draft: dict[str, Any]) -> bool:
    value = st.session_state.get(f"group_{group_index}_cabin_type", draft.get("cabin_type"))
    return str(value or "").strip().casefold() == "проходная"


def _underground_floors_for_group(group_index: int, draft: dict[str, Any]) -> int:
    value = st.session_state.get(f"group_{group_index}_underground_floors", draft.get("underground_floors"))
    underground_floors = _parse_number(str(value or ""), f"group_{group_index}_underground_floors")
    if underground_floors is None:
        return 0
    return max(0, int(underground_floors))


def _stops_for_group(group_index: int, draft: dict[str, Any]) -> int | None:
    value = st.session_state.get(f"group_{group_index}_stops", draft.get("stops"))
    return _parse_positive_int_silent(value)


def _button_marking_from_stops(stops: int, underground_floors: int = 0) -> str:
    stops = max(0, int(stops))
    underground_floors = min(max(0, int(underground_floors)), stops)
    floors = [*range(-underground_floors, 0), *range(1, stops - underground_floors + 1)]
    return ", ".join(str(floor) for floor in floors)


def _format_decimal_option(value: Any) -> str:
    if value in ("", None):
        return ""
    try:
        number = float(str(value).replace(",", "."))
    except ValueError:
        return str(value)
    if number.is_integer():
        return str(int(number))
    return f"{number:g}"


def _parse_number(value: Any, key: str) -> int | float | None:
    if value is None:
        return None
    value = str(value).strip().replace(",", ".")
    if value.casefold() in {"none", "null", "nan"}:
        return None
    if not value:
        return None
    parser = NUMERIC_FIELDS.get(key.rsplit("_", 1)[-1])
    if parser is None:
        field_name = key.split("_", 2)[-1]
        parser = NUMERIC_FIELDS.get(field_name, float)
    try:
        if parser is int:
            return int(float(value))
        return float(value)
    except ValueError:
        st.warning(f"Поле содержит нечисловое значение: {value}")
        return None


def _build_questionnaire(project_data: dict[str, Any], group_data: list[dict[str, Any]]) -> Questionnaire | None:
    try:
        project = ProjectInfo(**_drop_empty(project_data))
        groups = [LiftGroup(**_drop_empty(_prepare_group_for_model(group))) for group in group_data]
        return Questionnaire(project=project, lift_groups=groups)
    except ValidationError as exc:
        st.error("Есть ошибки в заполнении числовых полей.")
        st.json(exc.errors())
        return None


def _validation_block(questionnaire: Questionnaire) -> None:
    messages = validate_questionnaire(questionnaire)
    errors = [message for message in messages if message.level == "error"]
    warnings = [message for message in messages if message.level == "warning"]
    mgn_attention_labels, other_warnings = _split_mgn_attention_warnings(warnings, questionnaire)
    for message in errors:
        st.error(f"{message.location}: {message.message}")
    if mgn_attention_labels:
        _render_mgn_attention_block(mgn_attention_labels)
    for message in other_warnings:
        st.warning(f"{message.location}: {message.message}")


def _split_mgn_attention_warnings(
    warnings: list[ValidationMessage],
    questionnaire: Questionnaire,
) -> tuple[list[str], list[ValidationMessage]]:
    attention_labels: list[str] = []
    other_warnings: list[ValidationMessage] = []
    for message in warnings:
        if not _is_mgn_attention_warning(message):
            other_warnings.append(message)
            continue

        label = _label_for_validation_location(message.location, questionnaire)
        if label not in attention_labels:
            attention_labels.append(label)
    return attention_labels, other_warnings


def _is_mgn_attention_warning(message: ValidationMessage) -> bool:
    return message.level == "warning" and message.message.strip() == MGN_ACCESSIBILITY_WARNING


def _label_for_validation_location(location: str, questionnaire: Questionnaire) -> str:
    match = re.search(r"\d+", str(location))
    if not match:
        return str(location)

    group_index = int(match.group()) - 1
    if group_index < 0 or group_index >= len(questionnaire.lift_groups):
        return str(location)

    group = questionnaire.lift_groups[group_index]
    return _format_group_display_label(group.lift_name, group.quantity, group.capacity_kg) or str(location)


def _render_mgn_attention_block(labels: list[str]) -> None:
    chips = "".join(f'<span class="mgn-attention-chip">{html.escape(label)}</span>' for label in labels)
    attention_text = _mgn_attention_text(labels)
    st.markdown(
        f"""
        <div class="mgn-attention-block">
            <div class="mgn-attention-title">Комментарии по проверке</div>
            <div class="mgn-attention-meta">
                <span class="mgn-attention-label">Обратить внимание:</span>
                {chips}
            </div>
            <div class="mgn-attention-text">{html.escape(attention_text)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _mgn_attention_text(labels: list[str]) -> str:
    group_reference = "этой группы" if len(labels) == 1 else "данных групп"
    return (
        f"Для {group_reference} выбрана опция «Доступность МГН», не забудьте выбрать "
        "панель управления и вызывные посты со шрифтом Брайля."
    )


def _download_block(questionnaire: Questionnaire) -> None:
    disabled = any(message.level == "error" for message in validate_questionnaire(questionnaire))
    include_summary_sheet = st.checkbox(
        "Добавить саммэри-лист в опросник",
        value=True,
        key="include_summary_sheet",
    )
    if st.button("Сгенерировать опросник", type="primary", disabled=disabled):
        try:
            content = generate_questionnaire_xlsx(
                DEFAULT_TEMPLATE,
                questionnaire,
                MAPPING_PATH,
                include_summary_sheet=include_summary_sheet,
            )
            file_name = _questionnaire_download_filename(questionnaire)
            st.download_button(
                "Скачать заполненный Excel",
                data=content,
                file_name=file_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        except ExcelGenerationError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Не удалось сформировать Excel: {exc}")


def _questionnaire_download_filename(questionnaire: Questionnaire) -> str:
    project_name = safe_filename(questionnaire.project.project_name or "questionnaire")
    prepared_by = questionnaire.project.prepared_by
    report_date = questionnaire.project.report_date or date.today()
    file_parts = [project_name]
    if prepared_by:
        file_parts.append(safe_filename(prepared_by))
    file_parts.append(f"{report_date:%d.%m.%Y}")
    return f"{'_'.join(file_parts)}.xlsx"


def _drop_empty(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if value not in ("", None)}


def _prepare_group_for_model(data: dict[str, Any]) -> dict[str, Any]:
    group = dict(data)
    _apply_paired_finish_fields(group, SIGNAL_FINISH_FIELDS)
    _apply_paired_finish_fields(group, CABIN_COMPONENT_FINISH_FIELDS)
    _apply_mgn_option_dependency(group)
    _apply_additional_options(group)
    return _drop_group_helpers(group)


def _apply_mgn_option_dependency(group: dict[str, Any]) -> None:
    if _truthy_yes_no(group.get(MGN_ACCESSIBILITY_FIELD)):
        group[MGN_VOICE_OPTION_FIELD] = "ДА"


def _apply_additional_options(group: dict[str, Any]) -> None:
    selected_options = [
        translation
        for field, translation in ADDITIONAL_OPTION_TRANSLATIONS.items()
        if _truthy_yes_no(group.get(field))
    ]
    if selected_options:
        group["additional_options"] = "\n".join(selected_options)
    elif any(field in group for field in ADDITIONAL_OPTION_TRANSLATIONS):
        group.pop("additional_options", None)


def _apply_paired_finish_fields(group: dict[str, Any], paired_fields: dict[str, str]) -> None:
    for device_field, finish_field in paired_fields.items():
        device_value = group.get(device_field)
        finish_value = group.get(finish_field)
        if device_value in ("", None):
            continue
        if finish_value in ("", None):
            if not _is_no_finish_required_value(device_value):
                group.pop(device_field, None)
            continue
        if finish_value == OTHER_OPTION:
            group.pop(device_field, None)
            continue
        device_text = str(device_value).strip()
        finish_text = str(finish_value).strip()
        if not device_text or not finish_text:
            continue
        if _normalize_article_value(finish_text) in _normalize_article_value(device_text):
            continue
        group[device_field] = f"{device_text}, {finish_text}"


def _drop_group_helpers(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if key not in HELPER_GROUP_FIELDS}


if __name__ == "__main__":
    main()
