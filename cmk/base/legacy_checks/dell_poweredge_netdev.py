#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.


from cmk.base.check_api import LegacyCheckDefinition
from cmk.base.check_legacy_includes.dell_poweredge import check_dell_poweredge_netdev
from cmk.base.config import check_info
from cmk.base.plugins.agent_based.agent_based_api.v1 import SNMPTree

from cmk.agent_based.v2.type_defs import StringTable
from cmk.plugins.lib.dell import DETECT_IDRAC_POWEREDGE


def inventory_dell_poweredge_netdev(info):
    inventory = []
    for line in info:
        if line[1] != "2" and line[4] != "":
            inventory.append((line[4], None))
    return inventory


def parse_dell_poweredge_netdev(string_table: StringTable) -> StringTable:
    return string_table


check_info["dell_poweredge_netdev"] = LegacyCheckDefinition(
    parse_function=parse_dell_poweredge_netdev,
    detect=DETECT_IDRAC_POWEREDGE,
    fetch=SNMPTree(
        base=".1.3.6.1.4.1.674.10892.5.4.1100.90.1",
        oids=["3", "4", "6", "15", "30"],
    ),
    service_name="%s",
    discovery_function=inventory_dell_poweredge_netdev,
    check_function=check_dell_poweredge_netdev,
)
