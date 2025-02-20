#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.


from cmk.base.check_api import LegacyCheckDefinition
from cmk.base.check_legacy_includes.hitachi_hus import check_hitachi_hus, inventory_hitachi_hus
from cmk.base.config import check_info
from cmk.base.plugins.agent_based.agent_based_api.v1 import any_of, contains, SNMPTree

from cmk.agent_based.v2.type_defs import StringTable


def parse_hitachi_hus_dkc(string_table: StringTable) -> StringTable:
    return string_table


check_info["hitachi_hus_dkc"] = LegacyCheckDefinition(
    parse_function=parse_hitachi_hus_dkc,
    detect=any_of(
        contains(".1.3.6.1.2.1.1.1.0", "hm700"),
        contains(".1.3.6.1.2.1.1.1.0", "hm800"),
        contains(".1.3.6.1.2.1.1.1.0", "hm850"),
    ),
    fetch=SNMPTree(
        base=".1.3.6.1.4.1.116.5.11.4.1.1.6.1",
        oids=["1", "2", "3", "4", "5", "6", "7", "8", "9"],
    ),
    service_name="HUS DKC Chassis %s",
    discovery_function=inventory_hitachi_hus,
    check_function=check_hitachi_hus,
)
