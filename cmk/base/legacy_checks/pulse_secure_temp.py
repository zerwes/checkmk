#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

from collections.abc import Mapping

from cmk.base.check_api import LegacyCheckDefinition
from cmk.base.check_legacy_includes.temperature import check_temperature
from cmk.base.config import check_info
from cmk.base.plugins.agent_based.agent_based_api.v1 import SNMPTree

import cmk.plugins.lib.pulse_secure as pulse_secure
from cmk.agent_based.v2.type_defs import StringTable


def parse_pulse_secure_temp(string_table: StringTable) -> Mapping[str, int]:
    return pulse_secure.parse_pulse_secure(string_table, "IVE")


# no get_parsed_item_data because the temperature can be exactly 0 for some devices, which would
# result in "UNKN - Item not found in SNMP data", because parsed[item] evaluates to False
def check_pulse_secure_temp(item, params, parsed):
    if not parsed:
        return None

    return check_temperature(parsed[item], params, "pulse_secure_ive_temperature")


def discover_pulse_secure_temp(section):
    yield from ((item, {}) for item in section)


check_info["pulse_secure_temp"] = LegacyCheckDefinition(
    detect=pulse_secure.DETECT_PULSE_SECURE,
    fetch=SNMPTree(
        base=".1.3.6.1.4.1.12532",
        oids=["42"],
    ),
    parse_function=parse_pulse_secure_temp,
    service_name="Pulse Secure %s Temperature",
    discovery_function=discover_pulse_secure_temp,
    check_function=check_pulse_secure_temp,
    check_ruleset_name="temperature",
    check_default_parameters={"levels": (70.0, 75.0)},
)
