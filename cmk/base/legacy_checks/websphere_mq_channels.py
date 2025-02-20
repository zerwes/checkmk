#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

# Anzahl_Message Channelname MaxMessages_Moeglich Status"
# <<<websphere_mq_channels>>>
# 0   CHANNEL(C000052.C000051)  5000  Unknown
# 0   CHANNEL(C000052.CATSOS.03)  5000  RUNNING
# 0   CHANNEL(C000052.DXUZ001)  5000  RUNNING
# 0   CHANNEL(C000052.N000011)  5000  RUNNING
# 0   CHANNEL(C000052.SI0227450.T1)  10000  RUNNING
# 0   CHANNEL(C000052.SOX10.T1)  10000  STOPPED
# 0   CHANNEL(C000052.SV1348520.T1)  5000  RUNNING
# 0   CHANNEL(C000052.SV2098742.T1)  5000  Unknown


# mypy: disable-error-code="var-annotated"

from cmk.base.check_api import LegacyCheckDefinition
from cmk.base.config import check_info
from cmk.base.plugins.agent_based.agent_based_api.v1 import render


def parse_websphere_mq_channels(string_table):
    parsed = {}
    for line in string_table:
        if len(line) == 2:
            messages, max_messages = 0, 0
            channel_name = line[0]
            channel_status = line[1]
        elif len(line) == 4:
            messages = int(line[0])
            channel_name = line[1]
            max_messages = int(line[2])
            channel_status = line[3]
        else:
            continue

        parsed.setdefault(
            channel_name,
            {
                "messages": messages,
                "max_messages": max_messages,
                "channel_status": channel_status,
            },
        )
    return parsed


def inventory_websphere_mq_channels(parsed):
    for channel_name in parsed:
        yield channel_name, {}


def check_websphere_mq_channels(item, params, parsed):
    if isinstance(params, tuple):
        params = {
            "message_count": params,
            "status": {
                "RUNNING": 0,
                "STOPPED": 1,
            },
        }

    if item in parsed:
        data = parsed[item]
        messages = data["messages"]
        max_messages = data["max_messages"]
        channel_status = data["channel_status"]

        state = params["status"].get(channel_status, params["status"].get("other", 2))
        yield state, "Channel status: %s" % channel_status, []

        infotext = "%d/%d messages" % (messages, max_messages)
        state = 0
        if params["message_count"]:
            warn, crit = params["message_count"]
            if messages >= crit:
                state = 2
            elif messages >= warn:
                state = 1
            if state > 0:
                infotext += " (warn crit at %d/%d messages)" % (warn, crit)
        else:
            warn, crit = None, None

        yield state, infotext, [("messages", messages, warn, crit, 0, max_messages)]

        if params.get("message_count_perc") and max_messages > 0:
            warn, crit = params["message_count_perc"]
            messages_perc = 1.0 * messages / max_messages
            infotext = render.percent(messages_perc)
            state = 0

            if messages_perc >= crit:
                state = 2
            elif messages_perc >= warn:
                state = 1
            if state > 0:
                infotext += " (warn/crit at {}/{})".format(
                    render.percent(warn),
                    render.percent(crit),
                )

            yield state, infotext


check_info["websphere_mq_channels"] = LegacyCheckDefinition(
    parse_function=parse_websphere_mq_channels,
    service_name="MQ Channel %s",
    discovery_function=inventory_websphere_mq_channels,
    check_function=check_websphere_mq_channels,
    check_ruleset_name="websphere_mq_channels",
    check_default_parameters={
        "message_count": (900, 1000),
        "status": {"RUNNING": 0, "STOPPED": 1},
    },
)
