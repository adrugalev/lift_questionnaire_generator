from src.shaft_diagram import shaft_diagram_html


def test_shaft_diagram_shows_only_the_four_relevant_dimensions() -> None:
    html = shaft_diagram_html({
        "shaft_width_mm": 2900,
        "shaft_depth_mm": 3150,
        "pit_depth_mm": 1150,
        "overhead_mm": 4200,
        "machine_room": "С машинным помещением",
        "shaft_material": "Железобетон",
        "room_under_pit": "ДА",
        "seismic": "НЕТ",
    })

    for field, value in (
        ("shaft_width_mm", "2900 мм"),
        ("shaft_depth_mm", "3150 мм"),
        ("pit_depth_mm", "1150 мм"),
        ("overhead_mm", "4200 мм"),
    ):
        assert f'data-field="{field}"' in html
        assert f'<strong class="shaft-dim-value">{value}</strong>' in html
    assert "data:image/webp;base64," in html
    assert "Машинное помещение" not in html
    assert "Железобетон" not in html
    assert "Сейсмичность" not in html


def test_shaft_diagram_leaves_unknown_values_blank_and_escapes_input() -> None:
    html = shaft_diagram_html({
        "shaft_width_mm": '<script>alert("x")</script>',
        "machine_room": "Без машинного помещения",
        "machine_room_height_mm": 2500,
    })

    assert '<script>' not in html
    assert '&lt;script&gt;' in html
    assert '<strong class="shaft-dim-value">—</strong>' in html
    assert 'data-field="machine_room_height_mm"' not in html
    assert "Без машинного помещения" not in html
