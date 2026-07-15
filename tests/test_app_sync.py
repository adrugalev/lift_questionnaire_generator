import app
from app import SYNCABLE_GROUP_FIELDS
from src.models import LiftGroup, Questionnaire
from src.validators import ValidationMessage


class FakeSessionState(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, value):
        self[name] = value


def test_syncable_fields_exclude_geometry_and_core_specs() -> None:
    excluded = {
        "quantity",
        "capacity_kg",
        "speed_ms",
        "lifting_height_mm",
        "stops",
        "doors_count",
        "cabin_width_mm",
        "cabin_depth_mm",
        "cabin_height_mm",
        "landing_door_width_mm",
        "landing_door_height_mm",
        "shaft_width_mm",
        "shaft_depth_mm",
        "pit_depth_mm",
        "overhead_mm",
    }

    assert SYNCABLE_GROUP_FIELDS.isdisjoint(excluded)


def test_capacity_options_are_standard_values() -> None:
    assert app.CAPACITY_OPTIONS_KG == [
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


def test_speed_options_are_standard_values() -> None:
    assert app.SPEED_OPTIONS_MS == ["0.25", "0.5", "1", "1.6", "1.75", "2", "2.5", "3", "4", "5", "6"]


def test_random_test_groups_fill_every_form_field(monkeypatch) -> None:
    values_by_key = {
        "finish": ["Шлифованная нержавеющая сталь EX-HS01"],
        "floor_finish": ["Под отделку"],
        "handrail_type": ["EX-FS01"],
        "signal_steel_finish": ["Шлифованная нержавеющая сталь EX-HS01"],
        "ceiling_type": ["EX-J135"],
        "ceiling_steel_finish": ["Окрашенная сталь EX-YS01"],
        "mirror": ["MEX-1"],
        "cop_type": ["EX-AC99A"],
        "lop_type": ["EX-JC99A"],
    }

    def fake_select_values(options, option_key: str, field: str | None = None) -> list[str]:
        return values_by_key.get(option_key, [])

    monkeypatch.setattr(app, "_select_values", fake_select_values)
    app.random.seed(1)

    groups = app._random_test_groups(object())

    assert 2 <= len(groups) <= 4
    for group in groups:
        for fields in app.FIELD_GROUPS.values():
            for field, _, _, _ in fields:
                assert field in group
                assert group[field] not in ("", None)


def test_random_test_project_has_required_fields() -> None:
    app.random.seed(1)

    project = app._random_test_project()

    assert project["project_name"]
    assert project["customer"]
    assert project["address"]
    assert project["report_date"] == app.date.today()


def test_version_test_fill_click_requires_four_clicks(monkeypatch) -> None:
    session_state = FakeSessionState()
    applied = []
    reruns = []
    monkeypatch.setattr(app.st, "session_state", session_state)
    monkeypatch.setattr(app.st, "rerun", lambda: reruns.append(True))
    monkeypatch.setattr(app, "_apply_test_questionnaire", lambda options: applied.append(options))

    app._handle_version_test_fill_click("options")
    app._handle_version_test_fill_click("options")
    app._handle_version_test_fill_click("options")

    assert session_state["epss_test_fill_click_count"] == 3
    assert applied == []
    assert reruns == []

    app._handle_version_test_fill_click("options")

    assert session_state["epss_test_fill_click_count"] == 0
    assert applied == ["options"]
    assert reruns == [True]


def test_shaft_material_options_are_curated_and_without_custom_choice(monkeypatch) -> None:
    class FakeOptions:
        def get(self, option_key: str) -> list[str]:
            return ["Монолитная", "Кирпичная", "Металлокаркас", "Бетонная"]

    assert app._select_values(FakeOptions(), "shaft_material") == [
        "Железобетон",
        "Кирпичная",
        "Металлокаркас",
    ]
    assert "shaft_material" in app.SELECT_WITHOUT_CUSTOM_OPTION_KEYS


def test_fire_resistance_has_no_custom_choice(monkeypatch) -> None:
    class FakeOptions:
        def get(self, option_key: str) -> list[str]:
            return ["Нет", "EI-30", "EI-60", "EI-90"]

    assert app._select_values(FakeOptions(), "fire_resistance") == ["Нет", "EI-30", "EI-60", "EI-90"]
    assert "fire_resistance" in app.SELECT_WITHOUT_CUSTOM_OPTION_KEYS


def test_yes_no_has_no_custom_choice(monkeypatch) -> None:
    class FakeOptions:
        def get(self, option_key: str) -> list[str]:
            return ["ДА", "НЕТ"]

    assert app._select_values(FakeOptions(), "yes_no") == ["ДА", "НЕТ"]
    assert "yes_no" in app.SELECT_WITHOUT_CUSTOM_OPTION_KEYS


def test_display_type_has_curated_values_and_no_custom_choice() -> None:
    class FakeOptions:
        def get(self, option_key: str) -> list[str]:
            return ["DOT-Matrix LED", "LCD (7-сегментный)", 'LCD 10,4"', 'LCD 15"']

    assert app._select_values(FakeOptions(), "display_type") == [
        "DOT-Matrix LED",
        "LCD (7-сегментный)",
        'LCD 10,4"',
        'LCD 15"',
    ]
    assert "display_type" in app.SELECT_WITHOUT_CUSTOM_OPTION_KEYS


def test_seismic_has_curated_values_and_no_custom_choice() -> None:
    class FakeOptions:
        def get(self, option_key: str) -> list[str]:
            return ["Нет", "6 баллов", "7 баллов", "8 баллов", "9 баллов"]

    assert app._select_values(FakeOptions(), "seismic") == [
        "НЕТ",
        "6 баллов",
        "7 баллов",
        "8 баллов",
        "9 баллов",
    ]
    assert "seismic" in app.SELECT_WITHOUT_CUSTOM_OPTION_KEYS
    assert "seismic" in app.STRICT_SELECT_OPTION_KEYS


def test_group_defaults_use_reinforced_concrete_shaft_material(monkeypatch) -> None:
    session_state = FakeSessionState({
        "prefill_groups": [{}],
        "group_drafts": [{}],
    })
    monkeypatch.setattr(app.st, "session_state", session_state)

    assert app._group_defaults(0)["shaft_material"] == "Железобетон"


def test_group_defaults_normalize_old_concrete_shaft_material(monkeypatch) -> None:
    session_state = FakeSessionState({
        "prefill_groups": [{"shaft_material": "Бетонная"}],
        "group_drafts": [{}],
    })
    monkeypatch.setattr(app.st, "session_state", session_state)

    assert app._group_defaults(0)["shaft_material"] == "Железобетон"


def test_image_option_label_uses_filename_article() -> None:
    assert app._image_option_label(app.Path("EX-JC99A_double.jpg")) == "EX-JC99A double"


def test_finish_image_option_label_uses_full_material_name() -> None:
    assert app._image_option_label(app.Path("EX-HS01.png"), "finish") == "Шлифованная нержавеющая сталь EX-HS01"
    assert app._image_option_label(app.Path("CG-00.png"), "finish") == "Прозрачное стекло CG-00"
    assert app._image_option_label(app.Path("CG-04.png"), "finish") == "Цветное стекло CG-04"
    assert app._image_option_label(app.Path("CG-23.png"), "finish") == "Цветное стекло CG-23"
    assert app._image_option_label(app.Path("E-121.png"), "finish") == "Покрытие под дерево E-121"
    assert app._image_option_label(app.Path("TF-01.png"), "finish") == "Покрытие под ткань TF-01"
    assert app._image_option_label(app.Path("LF-01.png"), "finish") == "Покрытие под кожу LF-01"
    assert app._image_option_label(app.Path("PM-01.png"), "finish") == "Натуральное дерево, шпон PM-01"


def test_floor_image_option_label_uses_full_floor_name() -> None:
    assert app._image_option_label(app.Path("EX-DB210.png"), "floor_finish") == "Прорезиненное покрытие, PVC EX-DB210"
    assert app._image_option_label(app.Path("EX-DM01.png"), "floor_finish") == "Керамогранит EX-DM01"
    assert app._image_option_label(app.Path("EX-DS01.png"), "floor_finish") == "Рифлёная сталь EX-DS01"
    assert app._image_option_label(app.Path("EX-DA01.png"), "floor_finish") == "Рифлёная сталь EX-DA01"
    assert app._image_option_label(app.Path("EX-DR01.png"), "floor_finish") == "Резиновое покрытие EX-DR01"


def test_mirror_image_option_label_uses_description() -> None:
    assert app._image_option_label(app.Path("MEX-1.png"), "mirror") == "MEX-1, в неполную ширину до поручня"
    assert app._image_option_label(app.Path("MEX_2.png"), "mirror") == "MEX-2, в неполную ширину и неполную высоту"
    assert app._image_option_label(app.Path("MEX-3.png"), "mirror") == "MEX-3, во всю ширину стены до поручня"
    assert app._image_option_label(app.Path("MEX-4.png"), "mirror") == "MEX-4, во всю ширину стены до пола"


def test_image_options_are_read_from_material_folder(tmp_path, monkeypatch) -> None:
    image_path = tmp_path / "EX-HS01.png"
    image_path.write_bytes(b"fake")

    monkeypatch.setitem(app.IMAGE_OPTION_DIRS, "finish", tmp_path)

    assert app._image_options_for_key("finish") == {"Шлифованная нержавеющая сталь EX-HS01": image_path}


def test_cop_image_options_exclude_hx99_and_ic_card(tmp_path, monkeypatch) -> None:
    included_path = tmp_path / "EX-AC99A.png"
    hx_path = tmp_path / "EX-HX99.png"
    ic_path = tmp_path / "IC-Card.png"
    for path in (included_path, hx_path, ic_path):
        path.write_bytes(b"fake")

    monkeypatch.setitem(app.IMAGE_OPTION_DIRS, "cop_type", tmp_path)

    options = app._image_options_for_key("cop_type")

    assert options == {"EX-AC99A": included_path}


def test_signal_steel_finish_options_include_only_hs_and_ms(tmp_path, monkeypatch) -> None:
    hs_path = tmp_path / "EX-HS01.png"
    ms_path = tmp_path / "EX-MS01.png"
    ignored_path = tmp_path / "EX-RS01.png"
    for path in (hs_path, ms_path, ignored_path):
        path.write_bytes(b"fake")

    monkeypatch.setitem(app.IMAGE_OPTION_DIRS, "signal_steel_finish", tmp_path)

    assert app._image_options_for_key("signal_steel_finish") == {
        "Шлифованная нержавеющая сталь EX-HS01": hs_path,
        "Зеркальная нержавеющая сталь EX-MS01": ms_path,
    }


def test_ceiling_steel_finish_options_include_hs_ms_and_painted_steel(tmp_path, monkeypatch) -> None:
    hs_path = tmp_path / "EX-HS01.png"
    ms_path = tmp_path / "EX-MS01.png"
    ys_path = tmp_path / "EX-YS01.png"
    ignored_path = tmp_path / "EX-RS01.png"
    for path in (hs_path, ms_path, ys_path, ignored_path):
        path.write_bytes(b"fake")

    monkeypatch.setitem(app.IMAGE_OPTION_DIRS, "ceiling_steel_finish", tmp_path)

    assert app._image_options_for_key("ceiling_steel_finish") == {
        "Шлифованная нержавеющая сталь EX-HS01": hs_path,
        "Зеркальная нержавеющая сталь EX-MS01": ms_path,
        "Окрашенная сталь EX-YS01": ys_path,
    }


def test_image_path_matches_article_inside_old_text_value(tmp_path, monkeypatch) -> None:
    image_path = tmp_path / "EX-HS01.png"
    image_path.write_bytes(b"fake")

    monkeypatch.setitem(app.IMAGE_OPTION_DIRS, "finish", tmp_path)

    assert app._image_path_for_value("finish", "Шлифованная нержавеющая сталь EX-HS01") == image_path
    assert app._image_path_for_value("finish", "EX-HS01") == image_path


def test_image_path_prefers_exact_article_over_longer_partial_match(tmp_path, monkeypatch) -> None:
    single_path = tmp_path / "EX-JC99A.png"
    double_path = tmp_path / "EX-JC99A_double.png"
    single_path.write_bytes(b"single")
    double_path.write_bytes(b"double")

    monkeypatch.setitem(app.IMAGE_OPTION_DIRS, "lop_type", tmp_path)

    assert app._image_path_for_value("lop_type", "EX-JC99A") == single_path
    assert app._image_path_for_value("lop_type", "EX-JC99A double") == double_path


def test_storage_value_expands_finish_article_to_full_name() -> None:
    assert app._storage_value_for_option("finish", "EX-HS01") == "Шлифованная нержавеющая сталь EX-HS01"
    assert app._storage_value_for_option("finish", "CG-00") == "Прозрачное стекло CG-00"
    assert app._storage_value_for_option("finish", "CG-04") == "Цветное стекло CG-04"
    assert app._storage_value_for_option("finish", "TF-01") == "Покрытие под ткань TF-01"
    assert app._storage_value_for_option("finish", "LF-01") == "Покрытие под кожу LF-01"
    assert app._storage_value_for_option("finish", "PM-01") == "Натуральное дерево, шпон PM-01"


def test_storage_value_expands_floor_article_to_full_name() -> None:
    assert app._storage_value_for_option("floor_finish", "EX-DB210") == "Прорезиненное покрытие, PVC EX-DB210"
    assert app._storage_value_for_option("floor_finish", "EX-DM01") == "Керамогранит EX-DM01"
    assert app._storage_value_for_option("floor_finish", "EX-DS01") == "Рифлёная сталь EX-DS01"
    assert app._storage_value_for_option("floor_finish", "EX-DA01") == "Рифлёная сталь EX-DA01"
    assert app._storage_value_for_option("floor_finish", "EX-DR01") == "Резиновое покрытие EX-DR01"
    assert app._storage_value_for_option("floor_finish", "Под отделку") == "Под отделку"


def test_storage_value_expands_signal_steel_finish_article_to_full_name() -> None:
    assert app._storage_value_for_option("signal_steel_finish", "EX-HS01") == "Шлифованная нержавеющая сталь EX-HS01"
    assert app._storage_value_for_option("signal_steel_finish", "EX-MS01") == "Зеркальная нержавеющая сталь EX-MS01"
    assert app._storage_value_for_option("ceiling_steel_finish", "EX-YS01") == "Окрашенная сталь EX-YS01"


def test_storage_value_expands_mirror_article_to_description() -> None:
    assert app._storage_value_for_option("mirror", "MEX-1") == "MEX-1, в неполную ширину до поручня"
    assert app._storage_value_for_option("mirror", "MEX-2, в неполную ширину и неполную высоту") == "MEX-2, в неполную ширину и неполную высоту"


def test_floor_manual_option_is_added_to_select_values(monkeypatch) -> None:
    class FakeOptions:
        def get(self, option_key: str) -> list[str]:
            return ["EX-DB210", "ПВХ", "Керамогранит", "Рифленый алюминий"]

    monkeypatch.setattr(app, "_image_options_for_key", lambda option_key: {})

    assert app._select_values(FakeOptions(), "floor_finish") == ["Под отделку"]
    assert "floor_finish" in app.SELECT_WITHOUT_CUSTOM_OPTION_KEYS


def test_door_opening_options_exclude_swing_and_custom_choice(monkeypatch) -> None:
    class FakeOptions:
        def get(self, option_key: str) -> list[str]:
            return ["Телескопическое", "Центральное", "Распашное"]

    monkeypatch.setattr(app, "_image_options_for_key", lambda option_key: {})

    assert app._select_values(FakeOptions(), "door_opening_type") == ["Телескопическое", "Центральное"]
    assert "door_opening_type" in app.SELECT_WITHOUT_CUSTOM_OPTION_KEYS


def test_group_operation_has_no_custom_choice(monkeypatch) -> None:
    class FakeOptions:
        def get(self, option_key: str) -> list[str]:
            return ["Одиночное", "Групповое", "DDS"]

    monkeypatch.setattr(app, "_image_options_for_key", lambda option_key: {})

    assert app._select_values(FakeOptions(), "group_operation") == ["Одиночное", "Групповое", "DDS"]
    assert "group_operation" in app.SELECT_WITHOUT_CUSTOM_OPTION_KEYS


def test_lift_type_options_exclude_hospital_and_custom_choice(monkeypatch) -> None:
    class FakeOptions:
        def get(self, option_key: str) -> list[str]:
            return ["Пассажирский", "Грузопассажирский", "Грузовой", "Больничный"]

    monkeypatch.setattr(app, "_image_options_for_key", lambda option_key: {})

    assert app._select_values(FakeOptions(), "lift_type") == ["Пассажирский", "Грузопассажирский", "Грузовой"]
    assert "lift_type" in app.SELECT_WITHOUT_CUSTOM_OPTION_KEYS


def test_cabin_type_has_no_custom_choice(monkeypatch) -> None:
    class FakeOptions:
        def get(self, option_key: str) -> list[str]:
            return ["Непроходная", "Проходная"]

    monkeypatch.setattr(app, "_image_options_for_key", lambda option_key: {})

    assert app._select_values(FakeOptions(), "cabin_type") == ["Непроходная", "Проходная"]
    assert "cabin_type" in app.SELECT_WITHOUT_CUSTOM_OPTION_KEYS


def test_handrail_type_has_no_custom_choice(monkeypatch) -> None:
    class FakeOptions:
        def get(self, option_key: str) -> list[str]:
            return ["EX-FS01", "EX-FS02", "Без поручня"]

    monkeypatch.setattr(app, "_image_options_for_key", lambda option_key: {})

    assert app._select_values(FakeOptions(), "handrail_type") == ["EX-FS01", "EX-FS02", "Без поручня"]
    assert "handrail_type" in app.SELECT_WITHOUT_CUSTOM_OPTION_KEYS


def test_ceiling_type_excludes_standard_and_custom_choice(monkeypatch) -> None:
    class FakeOptions:
        def get(self, option_key: str) -> list[str]:
            return ["EX-J135", "EX-J136", "Стандартный"]

    monkeypatch.setattr(app, "_image_options_for_key", lambda option_key: {})

    assert app._select_values(FakeOptions(), "ceiling_type") == ["EX-J135", "EX-J136"]
    assert "ceiling_type" in app.SELECT_WITHOUT_CUSTOM_OPTION_KEYS


def test_mirror_options_keep_photo_items_and_disable_custom_choice(monkeypatch, tmp_path) -> None:
    mex1_path = tmp_path / "MEX-1.png"
    mex2_path = tmp_path / "MEX-2.png"
    for path in (mex1_path, mex2_path):
        path.write_bytes(b"fake")

    class FakeOptions:
        def get(self, option_key: str) -> list[str]:
            return ["Нет"]

    monkeypatch.setitem(app.IMAGE_OPTION_DIRS, "mirror", tmp_path)

    assert app._select_values(FakeOptions(), "mirror") == [
        "MEX-1, в неполную ширину до поручня",
        "MEX-2, в неполную ширину и неполную высоту",
        "Нет",
    ]
    assert "mirror" in app.SELECT_WITHOUT_CUSTOM_OPTION_KEYS


def test_wall_finish_fields_exclude_generic_text_options_and_custom_choice(monkeypatch) -> None:
    class FakeOptions:
        def get(self, option_key: str) -> list[str]:
            return [
                "Шлифованная нержавеющая сталь EX-HS01",
                "Зеркальная нержавеющая сталь",
                "Окрашенная сталь",
                "Ламинированная панель",
            ]

    monkeypatch.setattr(app, "_image_options_for_key", lambda option_key: {})

    assert app._select_values(FakeOptions(), "finish", "side_wall_finish") == [
        "Шлифованная нержавеющая сталь EX-HS01",
    ]
    assert "side_wall_finish" in app.SELECT_WITHOUT_CUSTOM_FIELDS
    assert "rear_wall_finish" in app.SELECT_WITHOUT_CUSTOM_FIELDS
    assert "front_wall_finish" in app.SELECT_WITHOUT_CUSTOM_FIELDS
    assert "skirting_finish" in app.SELECT_WITHOUT_CUSTOM_FIELDS
    assert app._select_values(FakeOptions(), "finish", "skirting_finish") == [
        "Нет",
        "Шлифованная нержавеющая сталь EX-HS01",
    ]


def test_wall_finish_selection_fills_empty_wall_finishes(monkeypatch) -> None:
    session_state = FakeSessionState({
        "group_drafts": [{}],
    })
    monkeypatch.setattr(app.st, "session_state", session_state)

    app._sync_empty_wall_finish_fields(0, "side_wall_finish", "Шлифованная нержавеющая сталь EX-HS01")

    assert session_state["group_drafts"][0]["rear_wall_finish"] == "Шлифованная нержавеющая сталь EX-HS01"
    assert session_state["group_drafts"][0]["front_wall_finish"] == "Шлифованная нержавеющая сталь EX-HS01"
    assert session_state["group_drafts"][0]["handrail_finish"] == "Шлифованная нержавеющая сталь EX-HS01"
    assert session_state["group_drafts"][0]["ceiling_finish"] == "Шлифованная нержавеющая сталь EX-HS01"
    assert session_state["group_drafts"][0]["skirting_finish"] == "Шлифованная нержавеющая сталь EX-HS01"
    assert session_state["group_drafts"][0]["cabin_door_finish"] == "Шлифованная нержавеющая сталь EX-HS01"
    assert session_state["group_drafts"][0]["main_floor_landing_door_finish"] == "Шлифованная нержавеющая сталь EX-HS01"
    assert session_state["group_drafts"][0]["other_floors_landing_door_finish"] == "Шлифованная нержавеющая сталь EX-HS01"
    assert session_state["group_drafts"][0]["cop_finish"] == "Шлифованная нержавеющая сталь EX-HS01"
    assert session_state["group_drafts"][0]["main_floor_lop_finish"] == "Шлифованная нержавеющая сталь EX-HS01"
    assert session_state["group_drafts"][0]["other_floors_lop_finish"] == "Шлифованная нержавеющая сталь EX-HS01"
    assert session_state["group_0_rear_wall_finish"] == "Шлифованная нержавеющая сталь EX-HS01"
    assert session_state["group_0_front_wall_finish"] == "Шлифованная нержавеющая сталь EX-HS01"
    assert session_state["group_0_handrail_finish"] == "Шлифованная нержавеющая сталь EX-HS01"
    assert session_state["group_0_ceiling_finish"] == "Шлифованная нержавеющая сталь EX-HS01"
    assert session_state["group_0_skirting_finish"] == "Шлифованная нержавеющая сталь EX-HS01"
    assert session_state["group_0_cabin_door_finish"] == "Шлифованная нержавеющая сталь EX-HS01"
    assert session_state["group_0_main_floor_landing_door_finish"] == "Шлифованная нержавеющая сталь EX-HS01"
    assert session_state["group_0_other_floors_landing_door_finish"] == "Шлифованная нержавеющая сталь EX-HS01"
    assert session_state["group_0_cop_finish"] == "Шлифованная нержавеющая сталь EX-HS01"
    assert session_state["group_0_main_floor_lop_finish"] == "Шлифованная нержавеющая сталь EX-HS01"
    assert session_state["group_0_other_floors_lop_finish"] == "Шлифованная нержавеющая сталь EX-HS01"


def test_wall_finish_selection_keeps_existing_different_wall_finish(monkeypatch) -> None:
    session_state = FakeSessionState({
        "group_drafts": [{
            "rear_wall_finish": "Зеркальная нержавеющая сталь EX-MS01",
            "handrail_finish": "Зеркальная нержавеющая сталь EX-MS01",
            "ceiling_finish": "Зеркальная нержавеющая сталь EX-MS01",
            "cabin_door_finish": "Зеркальная нержавеющая сталь EX-MS01",
            "cop_finish": "Зеркальная нержавеющая сталь EX-MS01",
        }],
        "group_0_rear_wall_finish": "Зеркальная нержавеющая сталь EX-MS01",
        "group_0_handrail_finish": "Зеркальная нержавеющая сталь EX-MS01",
        "group_0_ceiling_finish": "Зеркальная нержавеющая сталь EX-MS01",
        "group_0_cabin_door_finish": "Зеркальная нержавеющая сталь EX-MS01",
        "group_0_cop_finish": "Зеркальная нержавеющая сталь EX-MS01",
    })
    monkeypatch.setattr(app.st, "session_state", session_state)

    app._sync_empty_wall_finish_fields(0, "side_wall_finish", "Шлифованная нержавеющая сталь EX-HS01")

    assert session_state["group_drafts"][0]["rear_wall_finish"] == "Зеркальная нержавеющая сталь EX-MS01"
    assert session_state["group_drafts"][0]["front_wall_finish"] == "Шлифованная нержавеющая сталь EX-HS01"
    assert session_state["group_drafts"][0]["handrail_finish"] == "Зеркальная нержавеющая сталь EX-MS01"
    assert session_state["group_drafts"][0]["ceiling_finish"] == "Зеркальная нержавеющая сталь EX-MS01"
    assert session_state["group_drafts"][0]["skirting_finish"] == "Шлифованная нержавеющая сталь EX-HS01"
    assert session_state["group_drafts"][0]["cabin_door_finish"] == "Зеркальная нержавеющая сталь EX-MS01"
    assert session_state["group_drafts"][0]["main_floor_landing_door_finish"] == "Шлифованная нержавеющая сталь EX-HS01"
    assert session_state["group_drafts"][0]["other_floors_landing_door_finish"] == "Шлифованная нержавеющая сталь EX-HS01"
    assert session_state["group_drafts"][0]["cop_finish"] == "Зеркальная нержавеющая сталь EX-MS01"
    assert session_state["group_drafts"][0]["main_floor_lop_finish"] == "Шлифованная нержавеющая сталь EX-HS01"
    assert session_state["group_drafts"][0]["other_floors_lop_finish"] == "Шлифованная нержавеющая сталь EX-HS01"


def test_wall_finish_selection_does_not_fill_absent_component_finishes(monkeypatch) -> None:
    session_state = FakeSessionState({
        "group_drafts": [{
            "handrail_type": "Без поручня",
            "skirting_finish": "Нет",
        }],
        "group_0_handrail_type": "Без поручня",
        "group_0_skirting_finish": "Нет",
    })
    monkeypatch.setattr(app.st, "session_state", session_state)

    app._sync_empty_wall_finish_fields(0, "side_wall_finish", "Шлифованная нержавеющая сталь EX-HS01")

    assert "handrail_finish" not in session_state["group_drafts"][0]
    assert session_state["group_drafts"][0]["skirting_finish"] == "Нет"


def test_group_display_label_uses_single_lift_name() -> None:
    assert app._format_group_display_label("Л1", 1) == "Л1"


def test_group_display_label_uses_lift_range_for_multiple_lifts() -> None:
    assert app._format_group_display_label("Л1", 3) == "Л1-Л3"


def test_group_display_label_keeps_existing_range() -> None:
    assert app._format_group_display_label("Л1-Л3", 3) == "Л1-Л3"


def test_group_display_label_preserves_number_padding() -> None:
    assert app._format_group_display_label("Л01", 3) == "Л01-Л03"


def test_clamp_active_group_selection_resets_old_text_label(monkeypatch) -> None:
    session_state = FakeSessionState({
        "group_count": 1,
        "active_group_index": "Группа 1",
    })

    monkeypatch.setattr(app.st, "session_state", session_state)

    app._clamp_active_group_selection()

    assert session_state["active_group_index"] == 0


def test_image_preview_html_uses_fixed_thumbnail_container(tmp_path) -> None:
    image_path = tmp_path / "EX-HS01.png"
    image_path.write_bytes(b"fake")

    preview = app._image_preview_html(image_path)

    assert 'class="image-picker-thumb"' in preview
    assert "data:image/png;base64," in preview


def test_inline_thumbnail_css_fits_full_image() -> None:
    assert "object-fit: contain;" in app._filled_field_styles_css()


def test_selected_image_card_html_contains_label_and_value(tmp_path) -> None:
    image_path = tmp_path / "EX-AC99A.png"
    image_path.write_bytes(b"fake")

    card = app._selected_image_card_html("Панель управления кабины", "EX-AC99A", image_path)

    assert 'class="selected-image-card"' in card
    assert "Панель управления кабины" in card
    assert "EX-AC99A" in card


def test_selected_image_preview_items_collects_visual_fields(monkeypatch, tmp_path) -> None:
    finish_image = tmp_path / "EX-HS01.png"
    cop_image = tmp_path / "EX-AC99A.png"

    def fake_image_path(option_key: str, value: object) -> app.Path | None:
        if value == "Шлифованная нержавеющая сталь EX-HS01":
            return finish_image
        if value == "EX-AC99A":
            return cop_image
        return None

    monkeypatch.setattr(app, "_image_path_for_value", fake_image_path)

    items = app._selected_image_preview_items(
        [
            ("section", "№ дома / № секции", "text", None),
            ("side_wall_finish", "Облицовка боковых стен", "select", "finish"),
            ("cop_type", "Панель управления кабины", "select", "cop_type"),
        ],
        {
            "section": "Секция 1",
            "side_wall_finish": "Шлифованная нержавеющая сталь EX-HS01",
            "cop_type": "EX-AC99A",
        },
    )

    assert items == [
        ("Облицовка боковых стен", "Шлифованная нержавеющая сталь EX-HS01", finish_image),
        ("Панель управления кабины", "EX-AC99A", cop_image),
    ]


def test_signalization_preview_columns_pair_devices_with_finishes(monkeypatch, tmp_path) -> None:
    device_image = tmp_path / "device.png"
    finish_image = tmp_path / "finish.png"

    def fake_image_path(option_key: str, value: object) -> app.Path | None:
        if option_key in {"cop_type", "lop_type"}:
            return device_image
        if option_key == "signal_steel_finish":
            return finish_image
        return None

    monkeypatch.setattr(app, "_image_path_for_value", fake_image_path)

    columns = app._signalization_image_preview_columns(
        app.FIELD_GROUPS["Сигнализация"],
        {
            "cop_type": "EX-AC105A",
            "cop_finish": "Зеркальная нержавеющая сталь EX-MS03 Bronze",
            "main_floor_lop_type": "HBP-HD1",
            "main_floor_lop_finish": "Зеркальная нержавеющая сталь EX-MS03 Bronze",
            "other_floors_lop_type": "EX-JC56",
            "other_floors_lop_finish": "Зеркальная нержавеющая сталь EX-MS03 Bronze",
        },
    )

    assert [[item[1] for item in column] for column in columns] == [
        ["EX-AC105A", "Зеркальная нержавеющая сталь EX-MS03 Bronze"],
        ["HBP-HD1", "Зеркальная нержавеющая сталь EX-MS03 Bronze"],
        ["EX-JC56", "Зеркальная нержавеющая сталь EX-MS03 Bronze"],
    ]


def test_dialog_image_tile_html_uses_fixed_tile_classes(tmp_path) -> None:
    image_path = tmp_path / "EX-HS01.png"
    image_path.write_bytes(b"fake")

    tile = app._dialog_image_tile_html("Шлифованная нержавеющая сталь EX-HS01", image_path)

    assert 'class="image-dialog-tile"' in tile
    assert 'class="image-dialog-image"' in tile
    assert 'class="image-dialog-label"' in tile
    assert "Шлифованная нержавеющая сталь EX-HS01" in tile


def test_group_defaults_use_freight_passenger_lift_type(monkeypatch) -> None:
    session_state = FakeSessionState({
        "prefill_groups": [{}],
        "group_drafts": [{}],
    })

    monkeypatch.setattr(app.st, "session_state", session_state)

    assert app._group_defaults(0)["lift_type"] == "Грузопассажирский"


def test_group_defaults_keep_existing_lift_type(monkeypatch) -> None:
    session_state = FakeSessionState({
        "prefill_groups": [{"lift_type": "Пассажирский"}],
        "group_drafts": [{}],
    })

    monkeypatch.setattr(app.st, "session_state", session_state)

    assert app._group_defaults(0)["lift_type"] == "Пассажирский"


def test_group_defaults_use_first_main_landing_floor(monkeypatch) -> None:
    session_state = FakeSessionState({
        "prefill_groups": [{}],
        "group_drafts": [{}],
    })

    monkeypatch.setattr(app.st, "session_state", session_state)

    assert app._group_defaults(0)["main_landing_floor"] == "1"


def test_group_defaults_keep_existing_main_landing_floor(monkeypatch) -> None:
    session_state = FakeSessionState({
        "prefill_groups": [{"main_landing_floor": "-1"}],
        "group_drafts": [{}],
    })

    monkeypatch.setattr(app.st, "session_state", session_state)

    assert app._group_defaults(0)["main_landing_floor"] == "-1"


def test_main_landing_floor_options_include_nearby_underground_and_main_floors() -> None:
    assert app._main_landing_floor_options(2, 12) == ["-2", "-1", "1", "2"]
    assert app._main_landing_floor_options(1, 12) == ["-1", "1", "2"]
    assert app._main_landing_floor_options(3, 4) == ["-2", "-1", "1"]
    assert app._main_landing_floor_options(0, 12) == []


def test_main_landing_floor_widget_accepts_custom_values_when_underground_exists(monkeypatch) -> None:
    session_state = FakeSessionState({
        "group_drafts": [{"underground_floors": 2, "stops": 12}],
    })
    captured = {}

    def fake_selectbox(label, values, index, key, on_change, args, accept_new_options=False):
        captured.update(
            {
                "label": label,
                "values": values,
                "index": index,
                "key": key,
                "accept_new_options": accept_new_options,
            }
        )
        return "B1"

    monkeypatch.setattr(app.st, "session_state", session_state)
    monkeypatch.setattr(app.st, "selectbox", fake_selectbox)

    result = app._main_landing_floor_widget("Основной посадочный этаж", "group_0_main_landing_floor", "1", 0, "main_landing_floor")

    assert result == "B1"
    assert captured["values"] == ["-2", "-1", "1", "2"]
    assert captured["index"] == 2
    assert captured["accept_new_options"] is True


def test_group_defaults_use_machine_roomless_elevator(monkeypatch) -> None:
    session_state = FakeSessionState({
        "prefill_groups": [{}],
        "group_drafts": [{}],
    })

    monkeypatch.setattr(app.st, "session_state", session_state)

    assert app._group_defaults(0)["machine_room"] == "Без машинного помещения"


def test_group_defaults_keep_existing_machine_room(monkeypatch) -> None:
    session_state = FakeSessionState({
        "prefill_groups": [{"machine_room": "С машинным помещением"}],
        "group_drafts": [{}],
    })

    monkeypatch.setattr(app.st, "session_state", session_state)

    assert app._group_defaults(0)["machine_room"] == "С машинным помещением"


def test_group_defaults_use_no_seismic(monkeypatch) -> None:
    session_state = FakeSessionState({
        "prefill_groups": [{}],
        "group_drafts": [{}],
    })

    monkeypatch.setattr(app.st, "session_state", session_state)

    assert app._group_defaults(0)["seismic"] == app.DEFAULT_SEISMIC


def test_group_defaults_use_ei60_fire_resistance(monkeypatch) -> None:
    session_state = FakeSessionState({
        "prefill_groups": [{}],
        "group_drafts": [{}],
    })

    monkeypatch.setattr(app.st, "session_state", session_state)

    assert app._group_defaults(0)["fire_resistance"] == app.DEFAULT_FIRE_RESISTANCE


def test_group_defaults_keep_existing_fire_resistance(monkeypatch) -> None:
    session_state = FakeSessionState({
        "prefill_groups": [{"fire_resistance": "EI-90"}],
        "group_drafts": [{}],
    })

    monkeypatch.setattr(app.st, "session_state", session_state)

    assert app._group_defaults(0)["fire_resistance"] == "EI-90"


def test_group_defaults_normalize_old_no_seismic(monkeypatch) -> None:
    session_state = FakeSessionState({
        "prefill_groups": [{"seismic": "Нет"}],
        "group_drafts": [{}],
    })

    monkeypatch.setattr(app.st, "session_state", session_state)

    assert app._group_defaults(0)["seismic"] == "НЕТ"


def test_group_defaults_replace_unknown_seismic_with_default(monkeypatch) -> None:
    session_state = FakeSessionState({
        "prefill_groups": [{"seismic": "custom"}],
        "group_drafts": [{}],
    })

    monkeypatch.setattr(app.st, "session_state", session_state)

    assert app._group_defaults(0)["seismic"] == app.DEFAULT_SEISMIC


def test_button_marking_from_stops() -> None:
    assert app._button_marking_from_stops(12) == "1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12"


def test_button_marking_from_stops_with_underground_floors() -> None:
    assert app._button_marking_from_stops(12, 2) == "-2, -1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10"


def test_stops_update_doors_and_button_marking(monkeypatch) -> None:
    session_state = FakeSessionState({
        "group_drafts": [{}],
    })

    monkeypatch.setattr(app.st, "session_state", session_state)

    app._apply_stops_derived_fields(0, "12")

    assert session_state["group_drafts"][0]["doors_count"] == 12
    assert session_state["group_drafts"][0]["button_marking"] == "1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12"
    assert session_state["group_0_doors_count"] == "12"
    assert session_state["group_0_button_marking"] == "1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12"


def test_stops_update_button_marking_with_underground_floors(monkeypatch) -> None:
    session_state = FakeSessionState({
        "group_drafts": [{"underground_floors": "2"}],
        "group_0_underground_floors": "2",
    })

    monkeypatch.setattr(app.st, "session_state", session_state)

    app._apply_stops_derived_fields(0, "12")

    assert session_state["group_drafts"][0]["doors_count"] == 12
    assert session_state["group_drafts"][0]["button_marking"] == "-2, -1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10"
    assert session_state["group_0_doors_count"] == "12"
    assert session_state["group_0_button_marking"] == "-2, -1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10"


def test_stops_do_not_overwrite_doors_for_through_cabin(monkeypatch) -> None:
    session_state = FakeSessionState({
        "group_drafts": [{
            "cabin_type": "Проходная",
            "doors_count": 18,
        }],
        "group_0_cabin_type": "Проходная",
        "group_0_doors_count": "18",
    })

    monkeypatch.setattr(app.st, "session_state", session_state)

    app._apply_stops_derived_fields(0, "12")

    assert session_state["group_drafts"][0]["doors_count"] == 18
    assert session_state["group_0_doors_count"] == "18"
    assert session_state["group_drafts"][0]["button_marking"] == "1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12"


def test_stops_update_doors_for_non_through_cabin(monkeypatch) -> None:
    session_state = FakeSessionState({
        "group_drafts": [{
            "cabin_type": "Непроходная",
            "doors_count": 18,
        }],
        "group_0_cabin_type": "Непроходная",
        "group_0_doors_count": "18",
    })

    monkeypatch.setattr(app.st, "session_state", session_state)

    app._apply_stops_derived_fields(0, "12")

    assert session_state["group_drafts"][0]["doors_count"] == 12
    assert session_state["group_0_doors_count"] == "12"


def test_group_helpers_are_removed_before_model_build() -> None:
    assert app._drop_group_helpers({
        "stops": 12,
        "underground_floors": 2,
        "cop_finish": "EX-HS01",
        "handrail_finish": "EX-HS01",
    }) == {
        "stops": 12,
        "cop_finish": "EX-HS01",
        "handrail_finish": "EX-HS01",
    }


def test_signal_finish_fields_are_added_to_export_values() -> None:
    group = app._prepare_group_for_model({
        "cop_type": "EX-AC99A",
        "cop_finish": "Шлифованная нержавеющая сталь EX-HS01",
        "main_floor_lop_type": "EX-JC99A",
        "main_floor_lop_finish": "Зеркальная нержавеющая сталь EX-MS01",
    })

    assert group["cop_type"] == "EX-AC99A, Шлифованная нержавеющая сталь EX-HS01"
    assert group["main_floor_lop_type"] == "EX-JC99A, Зеркальная нержавеющая сталь EX-MS01"
    assert group["cop_finish"] == "Шлифованная нержавеющая сталь EX-HS01"
    assert group["main_floor_lop_finish"] == "Зеркальная нержавеющая сталь EX-MS01"


def test_cabin_component_finish_fields_are_added_to_export_values() -> None:
    group = app._prepare_group_for_model({
        "handrail_type": "EX-FS01",
        "handrail_finish": "Шлифованная нержавеющая сталь EX-HS01",
        "ceiling_type": "EX-J135",
        "ceiling_finish": "Зеркальная нержавеющая сталь EX-MS01",
        "skirting_finish": "Шлифованная нержавеющая сталь EX-HS01",
    })

    assert group["handrail_type"] == "EX-FS01, Шлифованная нержавеющая сталь EX-HS01"
    assert group["ceiling_type"] == "EX-J135, Зеркальная нержавеющая сталь EX-MS01"
    assert group["skirting_finish"] == "Шлифованная нержавеющая сталь EX-HS01"
    assert group["handrail_finish"] == "Шлифованная нержавеющая сталь EX-HS01"
    assert group["ceiling_finish"] == "Зеркальная нержавеющая сталь EX-MS01"


def test_unselected_materials_are_not_exported_as_partial_values() -> None:
    group = app._prepare_group_for_model({
        "cop_type": "EX-AC99A",
        "handrail_type": "EX-FS01",
        "ceiling_type": "EX-J135",
    })

    assert "cop_type" not in group
    assert "handrail_type" not in group
    assert "ceiling_type" not in group

    group_without_handrail = app._prepare_group_for_model({"handrail_type": "Без поручня"})

    assert group_without_handrail["handrail_type"] == "Без поручня"


def test_section_completion_requires_all_section_fields() -> None:
    group = {field: "filled" for field, _, _, _ in app.FIELD_GROUPS["Сигнализация"]}

    assert app._section_is_complete("Сигнализация", group)

    group["display_type"] = ""

    assert not app._section_is_complete("Сигнализация", group)


def test_cabin_section_does_not_require_finish_when_component_is_absent() -> None:
    group = {field: "filled" for field, _, _, _ in app.FIELD_GROUPS["Кабина"]}
    group["handrail_type"] = "Без поручня"
    group["handrail_finish"] = ""
    group["skirting_finish"] = "Нет"

    assert app._section_is_complete("Кабина", group)


def test_cabin_fields_arrange_component_finish_pairs() -> None:
    cabin_fields = [field for field, _, _, _ in app.FIELD_GROUPS["Кабина"]]
    cabin_field_options = {field: option_key for field, _, _, option_key in app.FIELD_GROUPS["Кабина"]}

    assert cabin_fields[cabin_fields.index("handrail_type") + 1] == "handrail_finish"
    assert cabin_fields[cabin_fields.index("ceiling_type") + 1] == "ceiling_finish"
    assert "skirting_finish_material" not in cabin_fields
    assert cabin_field_options["handrail_finish"] == "signal_steel_finish"
    assert cabin_field_options["ceiling_finish"] == "ceiling_steel_finish"


def test_signalization_fields_are_arranged_as_device_finish_pairs() -> None:
    assert [field for field, _, _, _ in app.FIELD_GROUPS["Сигнализация"]] == [
        "cop_type",
        "cop_finish",
        "main_floor_lop_type",
        "main_floor_lop_finish",
        "other_floors_lop_type",
        "other_floors_lop_finish",
        "display_type",
    ]


def test_door_fire_resistance_is_above_door_width() -> None:
    door_fields = [field for field, _, _, _ in app.FIELD_GROUPS["Двери"]]

    assert door_fields.index("fire_resistance") < door_fields.index("landing_door_width_mm")


def test_additional_options_textarea_is_removed_from_additional_section() -> None:
    additional_fields = [field for field, _, _, _ in app.FIELD_GROUPS["Дополнительные опции"]]
    additional_field_kinds = {field: kind for field, _, kind, _ in app.FIELD_GROUPS["Дополнительные опции"]}

    assert "additional_options" not in additional_fields
    assert additional_fields == ["mgn_accessibility", *app.ADDITIONAL_OPTION_TRANSLATIONS.keys()]
    assert additional_field_kinds["mgn_accessibility"] == "checkbox_yes_no"
    assert all(additional_field_kinds[field] == "checkbox_yes_no" for field in app.ADDITIONAL_OPTION_TRANSLATIONS)


def test_additional_option_fields_have_chinese_translations() -> None:
    assert len(app.ADDITIONAL_OPTION_TRANSLATIONS) == 19
    assert app.ADDITIONAL_OPTION_TRANSLATIONS["option_cctv_preparation"] == "预留视频监控接口"
    assert app.ADDITIONAL_OPTION_TRANSLATIONS["option_bypass"] == "Bypass（轿厢载荷超过80%时屏蔽外呼）"
    assert app.ADDITIONAL_OPTION_TRANSLATIONS["option_gesture_call"] == "手势呼梯"


def test_selected_additional_options_are_exported_in_chinese() -> None:
    group = app._prepare_group_for_model({
        "option_cctv_preparation": "ДА",
        "option_ado": "НЕТ",
        "option_bypass": "ДА",
    })

    assert group["additional_options"] == "预留视频监控接口\nBypass（轿厢载荷超过80%时屏蔽外呼）"
    assert "option_cctv_preparation" not in group
    assert "option_ado" not in group
    assert "option_bypass" not in group


def test_additional_section_is_renamed_to_additional_options() -> None:
    assert "Дополнительно" not in app.FIELD_GROUPS
    assert "Дополнительные опции" in app.FIELD_GROUPS


def test_collect_group_converts_mgn_checkbox_to_string(monkeypatch) -> None:
    session_state = FakeSessionState({
        "prefill_groups": [{}],
        "group_drafts": [{}],
        "group_0_mgn_accessibility": True,
    })
    monkeypatch.setattr(app.st, "session_state", session_state)

    group = app._collect_group_from_state(0, app._group_defaults(0))

    assert group["mgn_accessibility"] == "ДА"
    assert session_state["group_drafts"][0]["mgn_accessibility"] == "ДА"


def test_checkbox_yes_no_widget_state_is_boolean() -> None:
    assert app._widget_state_value("checkbox_yes_no", "ДА") is True
    assert app._widget_state_value("checkbox_yes_no", "НЕТ") is False


def test_truthy_yes_no_values() -> None:
    assert app._truthy_yes_no("ДА")
    assert app._truthy_yes_no(True)
    assert app._truthy_yes_no("YES")
    assert not app._truthy_yes_no("НЕТ")
    assert not app._truthy_yes_no(False)
    assert not app._truthy_yes_no(None)


def test_section_display_label_adds_checkmark_for_completed_section() -> None:
    assert app._section_display_label("Кабина", {"Кабина"}) == "Кабина ✅"
    assert app._section_display_label("Двери", {"Кабина"}) == "Двери"


def test_group_navigation_items_show_all_groups() -> None:
    filled_group = {
        field: "filled"
        for fields in app.FIELD_GROUPS.values()
        for field, _, _, _ in fields
    }
    filled_group.update({"lift_name": "Л1", "quantity": 3})
    empty_group = {}

    assert app._group_navigation_items([filled_group, empty_group]) == [(0, "Л1-Л3"), (1, "Группа 2")]


def test_add_group_makes_new_group_active(monkeypatch) -> None:
    session_state = FakeSessionState({
        "group_count": 1,
        "prefill_groups": [{}],
        "group_drafts": [{}],
        "active_group_index": 0,
    })
    monkeypatch.setattr(app.st, "session_state", session_state)

    app._add_group()

    assert session_state["group_count"] == 2
    assert session_state["prefill_groups"] == [{}, {}]
    assert session_state["group_drafts"] == [{}, {}]
    assert session_state["active_group_index"] == 1


def test_mgn_attention_warnings_are_grouped_by_lift_labels() -> None:
    questionnaire = Questionnaire(
        lift_groups=[
            LiftGroup(lift_name="Л1", quantity=3),
            LiftGroup(lift_name="Л4", quantity=1),
        ]
    )
    warnings = [
        ValidationMessage("warning", "Группа 1", app.MGN_ACCESSIBILITY_WARNING),
        ValidationMessage("warning", "Группа 2", app.MGN_ACCESSIBILITY_WARNING),
    ]

    labels, other_warnings = app._split_mgn_attention_warnings(warnings, questionnaire)

    assert labels == ["Л1-Л3", "Л4"]
    assert other_warnings == []


def test_non_mgn_warnings_remain_regular_warnings() -> None:
    questionnaire = Questionnaire(lift_groups=[LiftGroup(lift_name="Л1", quantity=1)])
    warning = ValidationMessage("warning", "Группа 1", "Проверьте количество дверей.")

    labels, other_warnings = app._split_mgn_attention_warnings([warning], questionnaire)

    assert labels == []
    assert other_warnings == [warning]


def test_clamp_active_group_selection(monkeypatch) -> None:
    session_state = FakeSessionState({
        "group_count": 2,
        "active_group_index": "Группа 7",
    })
    monkeypatch.setattr(app.st, "session_state", session_state)

    app._clamp_active_group_selection()

    assert session_state["active_group_index"] == 0

    session_state["active_group_index"] = 5
    app._clamp_active_group_selection()

    assert session_state["active_group_index"] == 1


def test_delete_group_reindexes_remaining_groups(monkeypatch) -> None:
    session_state = FakeSessionState({
        "group_count": 3,
        "prefill_groups": [{"section": "A"}, {"section": "B"}, {"section": "C"}],
        "group_drafts": [{"section": "A"}, {"section": "B"}, {"section": "C"}],
        "extracted_group_fields": [set(), set(), set()],
        "group_0_section": "A",
        "group_1_section": "B",
        "group_2_section": "C",
    })

    monkeypatch.setattr(app.st, "session_state", session_state)

    app._delete_group(1)

    assert session_state["group_count"] == 2
    assert session_state["prefill_groups"] == [{"section": "A"}, {"section": "C"}]
    assert session_state["group_drafts"] == [
        {
            "section": "A",
            "lift_type": "Грузопассажирский",
            "main_landing_floor": "1",
            "machine_room": "Без машинного помещения",
            "shaft_material": "Железобетон",
            "seismic": app.DEFAULT_SEISMIC,
            "fire_resistance": app.DEFAULT_FIRE_RESISTANCE,
            "mgn_accessibility": "НЕТ",
        },
        {
            "section": "C",
            "lift_type": "Грузопассажирский",
            "main_landing_floor": "1",
            "machine_room": "Без машинного помещения",
            "shaft_material": "Железобетон",
            "seismic": app.DEFAULT_SEISMIC,
            "fire_resistance": app.DEFAULT_FIRE_RESISTANCE,
            "mgn_accessibility": "НЕТ",
        },
    ]
    assert session_state["group_0_section"] == "A"
    assert session_state["group_1_section"] == "C"
    assert session_state["group_0_lift_type"] == "Грузопассажирский"
    assert session_state["group_1_lift_type"] == "Грузопассажирский"
    assert session_state["group_0_main_landing_floor"] == "1"
    assert session_state["group_1_main_landing_floor"] == "1"
    assert session_state["group_0_machine_room"] == "Без машинного помещения"
    assert session_state["group_1_machine_room"] == "Без машинного помещения"
    assert session_state["group_0_seismic"] == app.DEFAULT_SEISMIC
    assert session_state["group_1_seismic"] == app.DEFAULT_SEISMIC
    assert session_state["group_0_fire_resistance"] == app.DEFAULT_FIRE_RESISTANCE
    assert session_state["group_1_fire_resistance"] == app.DEFAULT_FIRE_RESISTANCE
    assert session_state["group_0_mgn_accessibility"] is False
    assert session_state["group_1_mgn_accessibility"] is False
    assert "group_2_section" not in session_state


def test_delete_only_group_clears_it(monkeypatch) -> None:
    session_state = FakeSessionState({
        "group_count": 1,
        "prefill_groups": [{"section": "A", "capacity_kg": 1000}],
        "group_drafts": [{"section": "A", "capacity_kg": 1000}],
        "extracted_group_fields": [{"section", "capacity_kg"}],
        "group_0_section": "A",
        "group_0_capacity_kg": "1000",
    })

    monkeypatch.setattr(app.st, "session_state", session_state)

    app._delete_group(0)

    assert session_state["group_count"] == 1
    assert session_state["prefill_groups"] == [{}]
    assert session_state["group_drafts"] == [{}]
    assert session_state["extracted_group_fields"] == [set()]
    assert "group_0_section" not in session_state
    assert "group_0_capacity_kg" not in session_state
