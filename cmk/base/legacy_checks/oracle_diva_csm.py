#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

# .1.3.6.1.4.1.110901.1.2.1.1.1.2.1       lib status
# .1.3.6.1.4.1.110901.1.2.2.1.1.8.1.1.x   drive x status
# .1.3.6.1.4.1.110901.1.3.1.1.4.1         actor status

# .1.3.6.1.4.1.110901.1.4.1.0             archive status
# .1.3.6.1.4.1.110901.1.4.2.0             archive objects count
# .1.3.6.1.4.1.110901.1.4.3.0             blank tapes count
# .1.3.6.1.4.1.110901.1.4.4.0             remaining size on tapes
# .1.3.6.1.4.1.110901.1.4.5.0             total size on tapes

#
# Note: These checks was designed a bit atypically (for no good reason):
#   The drive, actor, archive, tapes and library checks are subchecks of the status
#   check although none of these checks share the same oids.
#   As a result, "info" is always a list of 6 sublists and each check only
#   accesses exactly one of the sublists.
#

# .
#   .--Status--------------------------------------------------------------.
#   |                    ____  _        _                                  |
#   |                   / ___|| |_ __ _| |_ _   _ ___                      |
#   |                   \___ \| __/ _` | __| | | / __|                     |
#   |                    ___) | || (_| | |_| |_| \__ \                     |
#   |                   |____/ \__\__,_|\__|\__,_|___/                     |
#   |                                                                      |
#   '----------------------------------------------------------------------'


from collections.abc import Sequence

from cmk.base.check_api import check_levels, LegacyCheckDefinition
from cmk.base.config import check_info
from cmk.base.plugins.agent_based.agent_based_api.v1 import equals, SNMPTree

from cmk.agent_based.v2.type_defs import StringTable


def item_name_oracle_diva_csm(name, element_id):
    return (f"{name} {element_id}").strip()


def inventory_oracle_diva_csm_status(name, idx, info):
    for line in info[idx]:
        if len(line) == 2:
            element_id, _reading = line
        else:
            element_id = ""

        yield item_name_oracle_diva_csm(name, element_id), None


def status_result_oracle_diva_csm(reading):
    if reading == "1":
        return 0, "online"
    if reading == "2":
        return 2, "offline"
    if reading == "3":
        return 1, "unknown"
    return 3, "unexpected state"


def check_oracle_diva_csm_status(name, idx, item, params, info):
    for line in info[idx]:
        if len(line) == 2:
            element_id, reading = line
        else:
            element_id = ""
            reading = line[0]

        if item_name_oracle_diva_csm(name, element_id) == item:
            return status_result_oracle_diva_csm(reading)
    return None


def parse_oracle_diva_csm(string_table: Sequence[StringTable]) -> Sequence[StringTable]:
    return string_table


check_info["oracle_diva_csm"] = LegacyCheckDefinition(
    parse_function=parse_oracle_diva_csm,
    detect=equals(".1.3.6.1.2.1.1.2.0", ".1.3.6.1.4.1.311.1.1.3.1.2"),
    fetch=[
        SNMPTree(
            base=".1.3.6.1.4.1.110901.1.2.1.1.1",
            oids=["1", "2"],
        ),
        SNMPTree(
            base=".1.3.6.1.4.1.110901.1.2.2.1.1",
            oids=["3", "8"],
        ),
        SNMPTree(
            base=".1.3.6.1.4.1.110901.1.3.1.1",
            oids=["2", "4"],
        ),
        SNMPTree(
            base=".1.3.6.1.4.1.110901.1.4",
            oids=["1"],
        ),
        SNMPTree(
            base=".1.3.6.1.4.1.110901.1.4",
            oids=["2", "4", "5"],
        ),
        SNMPTree(
            base=".1.3.6.1.4.1.110901.1.4",
            oids=["3"],
        ),
    ],
    service_name="DIVA Status %s",
    discovery_function=lambda info: inventory_oracle_diva_csm_status("Library", 0, info),
    check_function=lambda item, params, info: check_oracle_diva_csm_status(
        "Library", 0, item, params, info
    ),
)

check_info["oracle_diva_csm.drive"] = LegacyCheckDefinition(
    service_name="DIVA Status %s",
    sections=["oracle_diva_csm"],
    discovery_function=lambda info: inventory_oracle_diva_csm_status("Drive", 1, info),
    check_function=lambda item, params, info: check_oracle_diva_csm_status(
        "Drive", 1, item, params, info
    ),
)

check_info["oracle_diva_csm.actor"] = LegacyCheckDefinition(
    service_name="DIVA Status %s",
    sections=["oracle_diva_csm"],
    discovery_function=lambda info: inventory_oracle_diva_csm_status("Actor", 2, info),
    check_function=lambda item, params, info: check_oracle_diva_csm_status(
        "Actor", 2, item, params, info
    ),
)

check_info["oracle_diva_csm.archive"] = LegacyCheckDefinition(
    service_name="DIVA Status %s",
    sections=["oracle_diva_csm"],
    discovery_function=lambda info: inventory_oracle_diva_csm_status("Manager", 3, info),
    check_function=lambda item, params, info: check_oracle_diva_csm_status(
        "Manager", 3, item, params, info
    ),
)

# .
#   .--Managed Objects-----------------------------------------------------.
#   |              __  __                                  _               |
#   |             |  \/  | __ _ _ __   __ _  __ _  ___  __| |              |
#   |             | |\/| |/ _` | '_ \ / _` |/ _` |/ _ \/ _` |              |
#   |             | |  | | (_| | | | | (_| | (_| |  __/ (_| |              |
#   |             |_|  |_|\__,_|_| |_|\__,_|\__, |\___|\__,_|              |
#   |                                       |___/                          |
#   |                    ___  _     _           _                          |
#   |                   / _ \| |__ (_) ___  ___| |_ ___                    |
#   |                  | | | | '_ \| |/ _ \/ __| __/ __|                   |
#   |                  | |_| | |_) | |  __/ (__| |_\__ \                   |
#   |                   \___/|_.__// |\___|\___|\__|___/                   |
#   |                            |__/                                      |
#   '----------------------------------------------------------------------'


def inventory_oracle_diva_csm_objects(info):
    if len(info) > 4 and len(info[4]) > 0:
        yield None, None


def check_oracle_diva_csm_objects(item, params, info):
    GB = 1024 * 1024 * 1024
    if len(info) > 4 and len(info[4]) > 0:
        object_count, remaining_size, total_size = map(int, info[4][0])

        infotext = "managed objects: {}, remaining size: {} GB of {} GB".format(
            object_count,
            remaining_size,
            total_size,
        )

        return (
            0,
            infotext,
            [
                ("managed_object_count", object_count),
                (
                    "storage_used",
                    (total_size - remaining_size) * GB,
                    None,
                    None,
                    0,
                    total_size * GB,
                ),
            ],
        )
    return None


check_info["oracle_diva_csm.objects"] = LegacyCheckDefinition(
    service_name="DIVA Managed Objects",
    sections=["oracle_diva_csm"],
    discovery_function=inventory_oracle_diva_csm_objects,
    check_function=check_oracle_diva_csm_objects,
)

# .
#   .--Tapes---------------------------------------------------------------.
#   |                      _____                                           |
#   |                     |_   _|_ _ _ __   ___  ___                       |
#   |                       | |/ _` | '_ \ / _ \/ __|                      |
#   |                       | | (_| | |_) |  __/\__ \                      |
#   |                       |_|\__,_| .__/ \___||___/                      |
#   |                               |_|                                    |
#   '----------------------------------------------------------------------'


def inventory_oracle_diva_csm_tapes(info):
    if len(info) > 5 and len(info[5]) > 0 and len(info[5][0]) > 0:
        yield None, {}


def check_oracle_diva_csm_tapes(item, params, info):
    try:
        blank_tapes = int(info[5][0][0])
    except IndexError:
        return

    yield check_levels(
        blank_tapes,
        "tapes_free",
        (None, None) + (params["levels_lower"] or (None, None)),
        human_readable_func=str,
        infoname="Blank tapes",
    )


check_info["oracle_diva_csm.tapes"] = LegacyCheckDefinition(
    service_name="DIVA Blank Tapes",
    sections=["oracle_diva_csm"],
    discovery_function=inventory_oracle_diva_csm_tapes,
    check_function=check_oracle_diva_csm_tapes,
    check_ruleset_name="blank_tapes",
    check_default_parameters={"levels_lower": (5, 1)},
)
