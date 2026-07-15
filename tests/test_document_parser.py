# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

from docx import Document
from reportlab.pdfgen import canvas

from src.document_parser import (
    _fire_resistance,
    _parse_ocr_project_info,
    _quantity_from_section,
    extract_text,
    parse_text,
)


def test_extract_text_from_docx(tmp_path: Path):
    path = tmp_path / "spec.docx"
    document = Document()
    document.add_paragraph("Грузоподъемность: 1000 кг. Скорость: 1,6 м/с. Остановок: 10.")
    document.save(path)
    text = extract_text(path)
    assert "Грузоподъемность" in text


def test_extract_text_from_pdf(tmp_path: Path):
    path = tmp_path / "spec.pdf"
    pdf = canvas.Canvas(str(path))
    pdf.drawString(40, 800, "Capacity text. Skorost substitute.")
    pdf.save()
    text = extract_text(path)
    assert "Capacity text" in text


def test_basic_lift_parameter_detection():
    text = "Проект: ЖК Тест. Грузоподъемность: 1000 кг. Скорость: 1,6 м/с. Остановок: 10."
    questionnaire, found = parse_text(text)
    group = questionnaire.lift_groups[0]
    assert questionnaire.project.project_name == "ЖК Тест"
    assert group.capacity_kg == 1000
    assert group.speed_ms == 1.6
    assert group.stops == 10
    assert found["capacity_kg"] is True


def test_table_like_lift_sheet_detection():
    text = "\n".join(
        [
            "\t\tЛифт пассажирский г/п 1000 кг. Секция 1-3\tЛифт пассажирский г/п 1000 кг. Секция 4-7\tПримечание",
            "4\tтип лифта\tпассажирский\tпассажирский\t",
            "5\tгрузоподъемность лифта (кг) и его скорость (м/с)\tQ = 1000; V = 1,0\tQ = 1000; V = 1,0\t",
            "6\tвысота подъема кабины в м\t25.520\t28.570\t",
            "7\tразмер кабины (ширина х глубина) в мм\t1100x2100\t1100x2100\t",
            "8\tтребуется ли выход из кабины в две противоположные стороны\tнет\tнет\t",
            "9\tчисло дверей шахты\t9\t10\t",
            "10\tчисло остановок кабины\t9\t10\t",
            "13\tуправление лифтами\tодиночное\tодиночное\t",
            "16\tконструкция шахты лифта\tмонолитная\tмонолитная\t",
            "17\tособые требования\tДвери шахты лифта противопожарные с пределом огнестойкости EI60\tДвери шахты лифта противопожарные с пределом огнестойкости EI60\t",
            "18\tкол-во заказываемых лифтов\t3\t4\t",
            "19\tглубина приямка\t1150 мм\t1150 мм\t",
            "20\tвысота верхнего этажа\t3600 мм\t3600 мм\t",
        ]
    )
    questionnaire, found = parse_text(text)

    assert len(questionnaire.lift_groups) == 2
    first, second = questionnaire.lift_groups
    assert first.section == "Секция 1-3"
    assert second.section == "Секция 4-7"
    assert first.quantity == 3
    assert second.quantity == 4
    assert first.capacity_kg == 1000
    assert first.speed_ms == 1.0
    assert first.lifting_height_mm == 25520
    assert second.lifting_height_mm == 28570
    assert first.cabin_width_mm == 1100
    assert first.cabin_depth_mm == 2100
    assert first.cabin_type == "Непроходная"
    assert second.doors_count == 10
    assert second.stops == 10
    assert first.group_operation == "Одиночное"
    assert first.shaft_material == "Железобетон"
    assert first.fire_resistance == "EI-60"
    assert first.pit_depth_mm == 1150
    assert first.overhead_mm == 3600
    assert found["quantity"] is True


def test_quantity_can_be_derived_from_section_range():
    assert _quantity_from_section("Секция 1-3") == 3
    assert _quantity_from_section("Секция 4-7") == 4


def test_fire_resistance_handles_ocr_digit_one():
    assert _fire_resistance("c npedenoM o2Hecmoukocmu E160") == "EI-60"


def test_ocr_title_block_extracts_object_and_address():
    items = [
        {"text": "/eHUH2padcKa9 onacmb,BcebonoxCKuu MyHuuunanbHblu pauoH, 3aHebcKoe", "xc": 2000, "yc": 1390},
        {"text": "2opodcKoe noceneHue, 3eMenbHblu yyQcmoK C KadacmpobbIM HoMepoM", "xc": 2000, "yc": 1415},
        {"text": "47:07:1044001:82044", "xc": 2000, "yc": 1436},
        {"text": "MH02oKbapmupHblu doM", "xc": 1875, "yc": 1478},
        {"text": "co bcmpoeHHo-npucmpoeHHbIMU", "xc": 1876, "yc": 1504},
        {"text": "nOMeWeHUAMU", "xc": 1876, "yc": 1528},
        {"text": 'OOOC3"ACIEKTMIJIOC"', "xc": 1800, "yc": 1163},
    ]

    project = _parse_ocr_project_info(items)

    assert project.project_name == "Многоквартирный дом со встроенно-пристроенными помещениями"
    assert project.customer == 'ООО СЗ "АСПЕКТ ПЛЮС"'
    assert project.address and "47:07:1044001:82044" in project.address
