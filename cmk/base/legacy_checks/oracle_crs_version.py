#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.


from cmk.base.check_api import LegacyCheckDefinition
from cmk.base.config import check_info
from cmk.base.plugins.agent_based.agent_based_api.v1 import IgnoreResultsError

from cmk.agent_based.v2.type_defs import StringTable


def inventory_oracle_crs_version(info):
    for _line in info:
        return [(None, {})]


def check_oracle_crs_version(_no_item, _no_params, info):
    for line in info:
        return (0, line[0])

    # In case of missing information we assume that the clusterware
    # is not running and we simple skip the result
    raise IgnoreResultsError("No version details found. Maybe the cssd is not running")


def parse_oracle_crs_version(string_table: StringTable) -> StringTable:
    return string_table


check_info["oracle_crs_version"] = LegacyCheckDefinition(
    parse_function=parse_oracle_crs_version,
    service_name="ORA-GI Version",
    discovery_function=inventory_oracle_crs_version,
    check_function=check_oracle_crs_version,
)
