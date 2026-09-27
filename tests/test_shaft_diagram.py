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
    assert 'src="app/static/shaft_with_parking.webp"' in html
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


def test_parking_appears_only_when_room_under_pit_is_present() -> None:
    with_room = shaft_diagram_html({"room_under_pit": "ДА"})
    without_room = shaft_diagram_html({"room_under_pit": "НЕТ"})

    assert 'class="shaft-parking"' not in with_room
    assert '<img class="shaft-art" src="app/static/shaft_with_parking.webp"' in with_room
    assert 'class="shaft-parking"' not in without_room
    assert 'class="shaft-card shaft-card--parking"' in with_room
    assert 'class="shaft-card"' in without_room
    assert 'viewBox="0 0 1024 1832"' in with_room
    assert 'viewBox="0 0 1024 1536"' in without_room
    assert '<img class="shaft-art" src="app/static/shaft_cutaway.webp"' in without_room
    assert with_room.count('class="shaft-art"') == 1
    assert 'class="shaft-car-brand"' in with_room
    assert 'href="app/static/epss_car_wordmark.webp"' in with_room
    assert 'class="shaft-car-brand"' not in without_room
    assert len(with_room.encode("utf-8")) < 100_000
    assert len(without_room.encode("utf-8")) < 100_000


def test_winch_is_hidden_with_machine_room_in_both_shaft_variants() -> None:
    for parking_choice in ("ДА", "НЕТ"):
        with_machine_room = shaft_diagram_html({
            "machine_room": "С машинным помещением",
            "room_under_pit": parking_choice,
        })
        without_machine_room = shaft_diagram_html({
            "machine_room": "Без машинного помещения",
            "room_under_pit": parking_choice,
        })

        assert '<img class="shaft-winch"' not in with_machine_room
        assert "с лебёдкой" not in with_machine_room
        assert '<img class="shaft-winch"' in without_machine_room
        assert 'src="app/static/traction_winch.webp"' in without_machine_room
        assert "с лебёдкой" in without_machine_room
