#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

from cmk.base.check_api import LegacyCheckDefinition
from cmk.base.config import check_info
from cmk.base.plugins.agent_based.agent_based_api.v1 import SNMPTree

from cmk.agent_based.v2.type_defs import StringTable
from cmk.plugins.lib.blade import DETECT_BLADE

# .1.3.6.1.4.1.2.3.51.2.22.1.5.1.1.2.1 1
# .1.3.6.1.4.1.2.3.51.2.22.1.5.1.1.2.2 2
# .1.3.6.1.4.1.2.3.51.2.22.1.5.1.1.2.3 3
# .1.3.6.1.4.1.2.3.51.2.22.1.5.1.1.2.4 4
# .1.3.6.1.4.1.2.3.51.2.22.1.5.1.1.2.5 5
# .1.3.6.1.4.1.2.3.51.2.22.1.5.1.1.3.1 1
# .1.3.6.1.4.1.2.3.51.2.22.1.5.1.1.3.2 1
# .1.3.6.1.4.1.2.3.51.2.22.1.5.1.1.3.3 1
# .1.3.6.1.4.1.2.3.51.2.22.1.5.1.1.3.4 1
# .1.3.6.1.4.1.2.3.51.2.22.1.5.1.1.3.5 1
# .1.3.6.1.4.1.2.3.51.2.22.1.5.1.1.4.1 1
# .1.3.6.1.4.1.2.3.51.2.22.1.5.1.1.4.2 3
# .1.3.6.1.4.1.2.3.51.2.22.1.5.1.1.4.3 255
# .1.3.6.1.4.1.2.3.51.2.22.1.5.1.1.4.4 0
# .1.3.6.1.4.1.2.3.51.2.22.1.5.1.1.4.5 1
# .1.3.6.1.4.1.2.3.51.2.22.1.5.1.1.5.1 1
# .1.3.6.1.4.1.2.3.51.2.22.1.5.1.1.5.2 12
# .1.3.6.1.4.1.2.3.51.2.22.1.5.1.1.5.3 9
# .1.3.6.1.4.1.2.3.51.2.22.1.5.1.1.5.4 1
# .1.3.6.1.4.1.2.3.51.2.22.1.5.1.1.5.5 1
# .1.3.6.1.4.1.2.3.51.2.22.1.5.1.1.6.1 ESX1
# .1.3.6.1.4.1.2.3.51.2.22.1.5.1.1.6.2 ESX109
# .1.3.6.1.4.1.2.3.51.2.22.1.5.1.1.6.3 ESX110
# .1.3.6.1.4.1.2.3.51.2.22.1.5.1.1.6.4 ESX137
# .1.3.6.1.4.1.2.3.51.2.22.1.5.1.1.6.5 ESX138


def inventory_blade_blades(info):
    for line in info:
        if line[2] == "1":
            yield (line[0], None)


def check_blade_blades(item, _no_params, info):
    map_exists = {"0": (2, "false"), "1": (0, "true")}

    map_power = {
        "0": (2, "off"),
        "1": (0, "on"),
        "3": (1, "standby"),
        "4": (1, "hibernate"),
        "255": (3, "unknown"),
    }

    map_health = {
        "0": (3, "unknown"),
        "1": (0, "good"),
        "2": (1, "warning"),
        "3": (2, "critical"),
        "4": (1, "kernel mode"),
        "5": (0, "discovering"),
        "6": (2, "communications error"),
        "7": (2, "no power"),
        "8": (1, "flashing"),
        "9": (2, "initialization Failure"),
        "10": (2, "insuffiecient power"),
        "11": (2, "power denied"),
        "12": (1, "maintenance mode"),
        "13": (1, "firehose dump"),
    }

    for line in info:
        if line[0] == item:
            # name
            yield 0, line[4]
            # exist_state
            state, state_readable = map_exists[line[1]]
            yield state, "Exists: %s" % state_readable
            # power_state
            state, state_readable = map_power[line[2]]
            yield state, "Power: %s" % state_readable
            # health_state
            state, state_readable = map_health[line[3]]
            yield state, "Health: %s" % state_readable


def parse_blade_blades(string_table: StringTable) -> StringTable:
    return string_table


check_info["blade_blades"] = LegacyCheckDefinition(
    parse_function=parse_blade_blades,
    detect=DETECT_BLADE,
    fetch=SNMPTree(
        base=".1.3.6.1.4.1.2.3.51.2.22.1.5.1.1",
        oids=["2", "3", "4", "5", "6"],
    ),
    service_name="Blade %s",
    discovery_function=inventory_blade_blades,
    check_function=check_blade_blades,
)
