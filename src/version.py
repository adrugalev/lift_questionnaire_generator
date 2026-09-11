from __future__ import annotations

from dataclasses import dataclass


APP_VERSION_DATE = "11.09.2026"
# Дневной счетчик версии: при смене APP_VERSION_DATE начинается с 1.
APP_VERSION_REVISION = 14


@dataclass(frozen=True)
class VersionHistoryEntry:
    revision: int
    date: str
    changes: tuple[str, ...]


APP_VERSION_HISTORY = (
    VersionHistoryEntry(
        revision=14,
        date="11.09.2026",
        changes=(
            "Материал поручня исключается из опросника, если поручень не выбран.",
        ),
    ),
    VersionHistoryEntry(
        revision=13,
        date="11.09.2026",
        changes=(
            "AFP ограничено материалами из нержавеющей стали.",
            "Галочка AFP недоступна, если в разделе нет подходящего материала.",
        ),
    ),
    VersionHistoryEntry(
        revision=12,
        date="11.09.2026",
        changes=(
            "Исправлено дублирование материала сигнализационных устройств при включённом AFP.",
        ),
    ),
    VersionHistoryEntry(
        revision=11,
        date="11.09.2026",
        changes=(
            "На вкладке сигнализационного оборудования галочка AFP перенесена над блоком изображений.",
        ),
    ),
    VersionHistoryEntry(
        revision=10,
        date="11.09.2026",
        changes=(
            "Галочки AFP аккуратно выровнены слева внизу соответствующих разделов.",
        ),
    ),
    VersionHistoryEntry(
        revision=9,
        date="11.09.2026",
        changes=(
            "В разделы кабины, дверей и сигнализации добавлены отдельные флажки покрытия AFP.",
            "При включённом AFP соответствующие материалы выводятся в опроснике с суффиксом AFP.",
        ),
    ),
    VersionHistoryEntry(
        revision=8,
        date="11.09.2026",
        changes=(
            "Высота строки «Прочее» в опроснике теперь учитывает все введённые строки текста.",
        ),
    ),
    VersionHistoryEntry(
        revision=7,
        date="11.09.2026",
        changes=(
            "Строка «Прочее» перенесена в конец раздела «Дополнительные опции» в опроснике.",
        ),
    ),
    VersionHistoryEntry(
        revision=6,
        date="11.09.2026",
        changes=(
            "В «Дополнительные опции» добавлено необязательное поле «Прочее» с выводом в Excel.",
        ),
    ),
    VersionHistoryEntry(
        revision=5,
        date="11.09.2026",
        changes=(
            "В раздел «Сигнализация» добавлены этажная индикация и материал индикации.",
            "EX-HD09, EX-HX99 и EX-HX201 перенесены в отдельный каталог этажной индикации.",
        ),
    ),
    VersionHistoryEntry(
        revision=4,
        date="11.09.2026",
        changes=(
            "К имени сформированного Excel добавлен префикс «Опросный лист».",
        ),
    ),
    VersionHistoryEntry(
        revision=3,
        date="11.09.2026",
        changes=(
            "Ускорено переключение разделов при заполнении больших проектов.",
            "Облегчены изображения в окнах выбора материалов и оборудования.",
            "Сохранение черновика переведено на сборку актуальных данных в момент скачивания.",
        ),
    ),
    VersionHistoryEntry(
        revision=2,
        date="11.09.2026",
        changes=(
            "В разделе «Шахта» у выбора машинного помещения убран вариант «Другое».",
            "Для лифтов с машинным помещением добавлена необязательная высота с выводом в опросник.",
        ),
    ),
    VersionHistoryEntry(
        revision=1,
        date="11.09.2026",
        changes=(
            "Добавлено окно с историей версий по нажатию на номер версии.",
            "Демо-заполнение перенесено на четыре клика по слову «Генератор» в заголовке.",
        ),
    ),
    VersionHistoryEntry(
        revision=2,
        date="10.09.2026",
        changes=(
            "Кнопки управления и пустые навигационные плашки переименованы с групп на лифты.",
            "Добавлена поддержка номеров лифтов с точкой, например Л11.1 и 1.3.",
        ),
    ),
    VersionHistoryEntry(
        revision=2,
        date="10.08.2026",
        changes=(
            "Грузоподъёмность можно вводить вручную после выбора стандартного значения.",
            "Из дополнительных опций удалены автоматический вентилятор и Gesture Call.",
        ),
    ),
    VersionHistoryEntry(
        revision=10,
        date="21.07.2026",
        changes=(
            "Добавлена перестановка лифтов перетаскиванием с автоматической перенумерацией.",
            "Расширена и визуально выделена зона вставки при перетаскивании.",
        ),
    ),
    VersionHistoryEntry(
        revision=26,
        date="17.07.2026",
        changes=(
            "Добавлено сохранение и восстановление черновика заполнения.",
            "Улучшены формирование Excel-опросника и саммэри с изображениями.",
        ),
    ),
    VersionHistoryEntry(
        revision=1,
        date="15.07.2026",
        changes=(
            "Создан генератор опросных листов EPSS с ручным заполнением и распознаванием ТЗ.",
        ),
    ),
)


def app_version_label() -> str:
    return f"Версия {APP_VERSION_REVISION} от {APP_VERSION_DATE}"


def app_version_history() -> tuple[VersionHistoryEntry, ...]:
    return APP_VERSION_HISTORY
