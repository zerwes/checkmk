#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.


from cmk.base.check_api import LegacyCheckDefinition
from cmk.base.check_legacy_includes.cpu_util import check_cpu_util
from cmk.base.config import check_info
from cmk.base.plugins.agent_based.agent_based_api.v1 import SNMPTree

from cmk.agent_based.v2.type_defs import StringTable
from cmk.plugins.lib.datapower import DETECT


def inventory_datapower_cpu(info):
    if info:
        yield None, {}


def check_datapower_cpu(_no_item, params, info):
    util = int(info[0][0])
    return check_cpu_util(util, params)


def parse_datapower_cpu(string_table: StringTable) -> StringTable:
    return string_table


check_info["datapower_cpu"] = LegacyCheckDefinition(
    parse_function=parse_datapower_cpu,
    detect=DETECT,
    fetch=SNMPTree(
        base=".1.3.6.1.4.1.14685.3.1.14",
        oids=["2"],
    ),
    service_name="CPU Utilization",
    discovery_function=inventory_datapower_cpu,
    check_function=check_datapower_cpu,
    check_ruleset_name="cpu_utilization",
    check_default_parameters={"util": (80.0, 90.0)},
)
