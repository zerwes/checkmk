#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

import pytest

from cmk.checkengine.legacy import LegacyCheckParameters
from cmk.checkengine.parameters import Parameters, TimespecificParameters, TimespecificParameterSet


def _default() -> LegacyCheckParameters:
    return {"default": 42}


def _tp_values() -> list[tuple[str, LegacyCheckParameters]]:
    return [("tp1", {"value": "from tp1"}), ("tp2", {"value": "from tp2"})]


class TestTimespecificParameterSet:
    def test_from_parameters_ts_dict(self) -> None:
        tsp = TimespecificParameterSet.from_parameters(
            {
                "tp_default_value": _default(),
                "tp_values": _tp_values(),
            }
        )
        assert tsp.default == _default()
        assert tsp.timeperiod_values == tuple(_tp_values())

    def test_from_paramters_legacy_tuple(self) -> None:
        tsp = TimespecificParameterSet.from_parameters((1, 2))
        assert tsp.default == (1, 2)
        assert not tsp.timeperiod_values

    def test_from_parameters_constant_dict(self) -> None:
        tsp = TimespecificParameterSet.from_parameters(_default())
        assert tsp.default == _default()
        assert not tsp.timeperiod_values

    def test_evaluate_constant_reevaluates_to_itself(self) -> None:
        assert TimespecificParameterSet(_default(), ()).evaluate(lambda x: True) == _default()

    def test_evaluate_no_period_active(self) -> None:
        assert (
            TimespecificParameterSet(_default(), _tp_values()).evaluate(lambda x: False)
            == _default()
        )

    def test_evaluate_first_period_wins(self) -> None:
        assert TimespecificParameterSet(_default(), _tp_values()).evaluate(lambda x: True) == {
            "default": 42,
            "value": "from tp1",
        }

    def test_evaluate_tp_filtering(self) -> None:
        assert TimespecificParameterSet(_default(), _tp_values()).evaluate(
            lambda x: x == "tp2"
        ) == {"default": 42, "value": "from tp2"}


class TestTimespecificParameters:
    def test_first_key_wins(self) -> None:
        assert TimespecificParameters(
            (
                TimespecificParameterSet(
                    {"key": "I am only default, but the most specific rule!"}, ()
                ),
                TimespecificParameterSet(
                    {"key": "default"},
                    [
                        (
                            "active_tp",
                            {
                                "key": "I am a specificly time-matching value, but from a more general rule!"
                            },
                        )
                    ],
                ),
            )
        ).evaluate(lambda x: True) == {"key": "I am only default, but the most specific rule!"}

    def test_first_tuple_wins(self) -> None:
        tuple_1: list[tuple[str, LegacyCheckParameters]] = [("tp3", (1, 1))]
        tuple_2: list[tuple[str, LegacyCheckParameters]] = [("tp3", (2, 2))]
        assert TimespecificParameters(
            (
                TimespecificParameterSet(_default(), _tp_values()),
                TimespecificParameterSet(_default(), _tp_values() + tuple_1),
                TimespecificParameterSet(_default(), tuple_2 + _tp_values()),
            )
        ).evaluate(lambda x: True) == (1, 1)


def test_parameters_features() -> None:
    par0 = Parameters({})
    par1 = Parameters({"olaf": "schneemann"})

    assert repr(par1) == "Parameters({'olaf': 'schneemann'})"

    assert len(par0) == 0
    assert len(par1) == 1

    assert not par0
    assert par1

    assert "olaf" not in par0
    assert "olaf" in par1

    assert par0.get("olaf") is None
    assert par1.get("olaf") == "schneemann"

    with pytest.raises(KeyError):
        _ = par0["olaf"]
    assert par1["olaf"] == "schneemann"

    assert not list(par0)
    assert not list(par0.keys())
    assert not list(par0.values())
    assert not list(par0.items())

    assert list(par1) == list(par1.keys()) == ["olaf"]
    assert list(par1.values()) == ["schneemann"]
    assert list(par1.items()) == [("olaf", "schneemann")]
