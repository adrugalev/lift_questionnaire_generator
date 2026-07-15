# -*- coding: utf-8 -*-
from __future__ import annotations

import base64
import json
import os
import re
from io import BytesIO
from pathlib import Path

from .models import Questionnaire


SYSTEM_PROMPT = """Извлеки параметры лифтового опросного листа из текста ТЗ.
Верни только JSON по схеме Questionnaire. Не придумывай отсутствующие значения: используй null."""

VISION_PROMPT = """Изучи страницы PDF/ТЗ по лифтам и извлеки параметры для опросного листа EPSS.
Верни только JSON без markdown.
Схема:
{
  "project": {
    "project_name": "string|null",
    "customer": "string|null",
    "address": "string|null",
    "report_date": "YYYY-MM-DD|null"
  },
  "lift_groups": [
    {
      "section": "string|null",
      "lift_name": "string|null",
      "quantity": "int|null",
      "lift_type": "string|null",
      "capacity_kg": "int|null",
      "speed_ms": "float|null",
      "lifting_height_mm": "int|null",
      "stops": "int|null",
      "doors_count": "int|null",
      "group_operation": "string|null",
      "button_marking": "string|null",
      "main_landing_floor": "string|null",
      "cabin_type": "string|null",
      "cabin_width_mm": "int|null",
      "cabin_depth_mm": "int|null",
      "cabin_height_mm": "int|null",
      "door_opening_type": "string|null",
      "fire_resistance": "string|null",
      "machine_room": "string|null",
      "shaft_material": "string|null",
      "pit_depth_mm": "int|null",
      "overhead_mm": "int|null"
    }
  ]
}
Правила:
- Не придумывай отсутствующие значения, используй null.
- Если есть несколько колонок/групп лифтов, верни несколько lift_groups.
- Значения высоты подъема в метрах переводи в миллиметры.
- EI60 нормализуй как EI-60.
- Стоимость и количество контейнеров не извлекай.
"""


def extract_with_llm(text: str) -> Questionnaire | None:
    if not os.getenv("OPENAI_API_KEY"):
        return None
    try:
        from openai import OpenAI
    except ImportError:
        return None

    client = OpenAI()
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text[:50000]},
        ],
    )
    raw = response.output_text.strip()
    data = _json_from_model_output(raw)
    return Questionnaire(**data)


def extract_pdf_with_vision(path_or_bytes: str | Path | bytes, max_pages: int = 5) -> Questionnaire | None:
    if not os.getenv("OPENAI_API_KEY"):
        return None
    try:
        from openai import OpenAI
    except ImportError:
        return None

    images = _pdf_page_data_urls(path_or_bytes, max_pages=max_pages)
    if not images:
        return None

    content = [{"type": "input_text", "text": VISION_PROMPT}]
    content.extend({"type": "input_image", "image_url": image_url} for image_url in images)

    client = OpenAI()
    response = client.responses.create(
        model=os.getenv("OPENAI_VISION_MODEL", os.getenv("OPENAI_MODEL", "gpt-4.1-mini")),
        input=[{"role": "user", "content": content}],
    )
    data = _json_from_model_output(response.output_text)
    return Questionnaire(**data)


def _pdf_page_data_urls(path_or_bytes: str | Path | bytes, max_pages: int) -> list[str]:
    try:
        import fitz
    except ImportError:
        return []

    if isinstance(path_or_bytes, bytes):
        document = fitz.open(stream=path_or_bytes, filetype="pdf")
    else:
        document = fitz.open(path_or_bytes)

    data_urls: list[str] = []
    for page in document[:max_pages]:
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        png = pix.tobytes("png")
        encoded = base64.b64encode(png).decode("ascii")
        data_urls.append(f"data:image/png;base64,{encoded}")
    return data_urls


def _json_from_model_output(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)
