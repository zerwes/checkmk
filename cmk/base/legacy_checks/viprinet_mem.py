#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.


from cmk.base.check_api import get_bytes_human_readable, LegacyCheckDefinition, saveint
from cmk.base.config import check_info
from cmk.base.plugins.agent_based.agent_based_api.v1 import SNMPTree

from cmk.agent_based.v2.type_defs import StringTable
from cmk.plugins.lib.viprinet import DETECT_VIPRINET


def parse_viprinet_mem(string_table: StringTable) -> StringTable:
    return string_table


check_info["viprinet_mem"] = LegacyCheckDefinition(
    parse_function=parse_viprinet_mem,
    detect=DETECT_VIPRINET,
    fetch=SNMPTree(
        base=".1.3.6.1.4.1.35424.1.2",
        oids=["2"],
    ),
    service_name="Memory",
    discovery_function=lambda info: len(info) > 0 and [(None, None)] or [],
    check_function=lambda _no_item, _no_params, info: (
        0,
        "Memory used: %s" % get_bytes_human_readable(saveint(info[0][0])),
    ),
)
