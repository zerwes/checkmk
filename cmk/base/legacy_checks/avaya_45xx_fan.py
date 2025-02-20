#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.


from cmk.base.check_api import LegacyCheckDefinition
from cmk.base.config import check_info
from cmk.base.plugins.agent_based.agent_based_api.v1 import contains, SNMPTree

from cmk.agent_based.v2.type_defs import StringTable


def inventory_avaya_45xx_fan(info):
    for idx, _line in enumerate(info):
        yield str(idx), {}


def check_avaya_45xx_fan(item, params, info):
    state_map = {
        "1": ("Other", 3),
        "2": ("Not available", 3),
        "3": ("Removed", 0),
        "4": ("Disabled", 0),
        "5": ("Normal", 0),
        "6": ("Reset in Progress", 1),
        "7": ("Testing", 1),
        "8": ("Warning", 1),
        "9": ("Non fatal error", 1),
        "10": ("Fatal error", 2),
        "11": ("Not configured", 1),
        "12": ("Obsoleted", 0),
    }

    for idx, fan_status in enumerate(info):
        if str(idx) == item:
            text, state = state_map.get(fan_status[0], ("Unknown", 3))
            return state, text
    return None


def parse_avaya_45xx_fan(string_table: StringTable) -> StringTable:
    return string_table


check_info["avaya_45xx_fan"] = LegacyCheckDefinition(
    parse_function=parse_avaya_45xx_fan,
    detect=contains(".1.3.6.1.2.1.1.2.0", ".1.3.6.1.4.1.45.3"),
    # S5-CHASSIS-MIB,
    fetch=SNMPTree(
        base=".1.3.6.1.4.1.45.1.6.3.3.1.1.10",
        oids=["6"],
    ),
    service_name="Fan Chassis %s",
    discovery_function=inventory_avaya_45xx_fan,
    check_function=check_avaya_45xx_fan,
)
