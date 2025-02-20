#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.


# mypy: disable-error-code="no-untyped-def"

from typing import NamedTuple

from cmk.base.check_api import LegacyCheckDefinition
from cmk.base.check_legacy_includes.cisco_ucs import DETECT, map_operability
from cmk.base.config import check_info
from cmk.base.plugins.agent_based.agent_based_api.v1 import SNMPTree

# comNET GmbH, Fabian Binder - 2018-05-07


class Section(NamedTuple):
    model: str
    state: int
    operability: str
    serial: str
    vendor: str


def parse_cisco_ucs_raid(string_table) -> Section:
    return Section(
        string_table[0][0],
        *map_operability[string_table[0][1]],
        string_table[0][2],
        string_table[0][3],
    )


def discover_cisco_ucs_raid(section):
    yield None, {}


def check_cisco_ucs_raid(_no_item, _no_params, section):
    yield section.state, f"Status: {section.operability}"
    yield 0, f"Model: {section.model}"
    yield 0, f"Vendor: {section.vendor}"
    yield 0, f"Serial number: {section.serial}"


check_info["cisco_ucs_raid"] = LegacyCheckDefinition(
    detect=DETECT,
    fetch=SNMPTree(
        base=".1.3.6.1.4.1.9.9.719.1.45.1.1",
        oids=["5", "7", "14", "17"],
    ),
    parse_function=parse_cisco_ucs_raid,
    service_name="RAID Controller",
    discovery_function=discover_cisco_ucs_raid,
    check_function=check_cisco_ucs_raid,
)
