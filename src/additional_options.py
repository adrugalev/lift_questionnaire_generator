# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdditionalOption:
    field: str
    russian: str
    chinese: str


ADDITIONAL_OPTIONS = [
    AdditionalOption("option_cctv_preparation", "Подготовка под видеонаблюдение", "预留视频监控接口"),
    AdditionalOption("option_ado", "ADO — Advanced Door Opening", "ADO高级开门功能"),
    AdditionalOption("option_warranty_5_years", "Гарантия 5 лет", "5年质保"),
    AdditionalOption("option_video_camera", "Видеокамера", "视频摄像头"),
    AdditionalOption("option_ard", "ARD — Automatic Rescue Device", "ARD自动救援装置"),
    AdditionalOption(
        "option_parking_floor",
        "Возврат лифта на основной посадочный этаж (Parking Floor)",
        "电梯返回主停靠层（Parking Floor）",
    ),
    AdditionalOption("option_customer_logo", "Логотип заказчика", "客户标识"),
    AdditionalOption(
        "option_extra_lop_line",
        "Дополнительная нитка вызывных постов (вывод из группы)",
        "额外一组外呼按钮（群控分离）",
    ),
    AdditionalOption("option_ic_card", "IC-Card (блокировка приказной панели)", "IC卡（轿厢操纵盘权限控制）"),
    AdditionalOption(
        "option_remote_control_cabinet",
        "Удалённое расположение шкафа управления (до 5 метров от шахты)",
        "控制柜远程布置（距井道不超过5米）",
    ),
    AdditionalOption("option_auto_fan", "Автоматический вентилятор", "自动通风风扇"),
    AdditionalOption("option_russian_voice", "Голосовой информатор на русском языке", "俄语语音报站器"),
    AdditionalOption("option_guide_rails_2_5m", "Направляющие 2,5 м.", "2.5米导轨"),
    AdditionalOption("option_u_bracket", "Тип кронштейна: П-образный", "支架类型：U型"),
    AdditionalOption("option_controller_cabinet_finish", "Отделка шкафа контроллера", "控制柜装饰"),
    AdditionalOption("option_roller_shoes", "Тип башмаков: роликовые", "导靴类型：滚轮导靴"),
    AdditionalOption("option_extra_noise_insulation", "Шумоизоляция дополнительная", "附加隔音"),
    AdditionalOption(
        "option_bypass",
        "Bypass (блокировка вызовов при загрузке кабины более 80%)",
        "Bypass（轿厢载荷超过80%时屏蔽外呼）",
    ),
    AdditionalOption("option_gesture_call", "Gesture Call", "手势呼梯"),
]

ADDITIONAL_OPTION_FIELDS = [(option.field, option.russian) for option in ADDITIONAL_OPTIONS]
ADDITIONAL_OPTION_TRANSLATIONS = {option.field: option.chinese for option in ADDITIONAL_OPTIONS}
