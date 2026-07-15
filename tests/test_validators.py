# -*- coding: utf-8 -*-
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.models import LiftGroup
from src.validators import validate_lift_group


def test_quantity_cannot_be_zero():
    with pytest.raises(ValidationError):
        LiftGroup(quantity=0)


def test_speed_cannot_be_negative():
    with pytest.raises(ValidationError):
        LiftGroup(speed_ms=-1)


def test_stops_cannot_be_zero():
    with pytest.raises(ValidationError):
        LiftGroup(stops=0)


def test_warning_when_doors_less_than_stops():
    group = LiftGroup(quantity=1, capacity_kg=1000, speed_ms=1.0, stops=10, doors_count=8)
    messages = validate_lift_group(group)
    assert any(message.level == "warning" and "дверей меньше" in message.message for message in messages)

