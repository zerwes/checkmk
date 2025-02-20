#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.


from cmk.base.check_api import LegacyCheckDefinition
from cmk.base.config import check_info

from cmk.agent_based.v2.type_defs import StringTable


def inventory_sap_state(info):
    for line in info:
        if len(line) == 2:
            yield line[0], None


def check_sap_state(item, _no_parameters, info):
    def value_to_status(value):
        if value == "OK":
            return 0
        return 2

    for line in info:
        if line[0] == item:
            value = line[1]
            return value_to_status(value), "Status: %s" % value


def parse_sap_state(string_table: StringTable) -> StringTable:
    return string_table


check_info["sap_state"] = LegacyCheckDefinition(
    parse_function=parse_sap_state,
    service_name="SAP State %s",
    discovery_function=inventory_sap_state,
    check_function=check_sap_state,
)
