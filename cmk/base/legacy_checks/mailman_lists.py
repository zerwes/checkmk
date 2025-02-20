#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.


from cmk.base.check_api import LegacyCheckDefinition, saveint
from cmk.base.config import check_info

from cmk.agent_based.v2.type_defs import StringTable


def inventory_mailman_lists(info):
    return [(i[0], None) for i in info]


def check_mailman_lists(item, params, info):
    for line in info:
        name, num_members = line[0], saveint(line[1])
        if name == item:
            return (0, "%d members subscribed" % (num_members), [("count", num_members)])
    return (3, "List could not be found in agent output")


def parse_mailman_lists(string_table: StringTable) -> StringTable:
    return string_table


check_info["mailman_lists"] = LegacyCheckDefinition(
    parse_function=parse_mailman_lists,
    service_name="Mailinglist %s",
    discovery_function=inventory_mailman_lists,
    check_function=check_mailman_lists,
)
