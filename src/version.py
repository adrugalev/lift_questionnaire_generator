from __future__ import annotations

APP_VERSION_DATE = "16.07.2026"
# Дневной счетчик версии: при смене APP_VERSION_DATE начинается с 1.
APP_VERSION_REVISION = 8


def app_version_label() -> str:
    return f"Версия {APP_VERSION_REVISION} от {APP_VERSION_DATE}"
