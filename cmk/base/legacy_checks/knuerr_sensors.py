#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.


from cmk.base.check_api import LegacyCheckDefinition
from cmk.base.config import check_info
from cmk.base.plugins.agent_based.agent_based_api.v1 import SNMPTree

from cmk.agent_based.v2.type_defs import StringTable
from cmk.plugins.lib.knuerr import DETECT_KNUERR


def inventory_knuerr_sensors(info):
    for sensor, _state in info:
        if sensor:
            yield sensor, None


def check_knuerr_sensors(item, _no_params, info):
    for sensor, state in info:
        if sensor == item:
            if state != "0":
                return 2, "Sensor triggered"
            return 0, "Sensor not triggered"
    return 3, "Sensor no longer found"


def parse_knuerr_sensors(string_table: StringTable) -> StringTable:
    return string_table


check_info["knuerr_sensors"] = LegacyCheckDefinition(
    parse_function=parse_knuerr_sensors,
    detect=DETECT_KNUERR,
    fetch=SNMPTree(
        base=".1.3.6.1.4.1.3711.15.1.1.2",
        oids=["1", "5"],
    ),
    service_name="Sensor %s",
    discovery_function=inventory_knuerr_sensors,
    check_function=check_knuerr_sensors,
)
