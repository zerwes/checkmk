#!/usr/bin/env python3
# Copyright (C) 2023 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

from collections.abc import Sequence
from pathlib import Path
from time import time
from typing import assert_never, Literal, TypedDict

from cmk.utils.paths import robotmk_html_log_dir  # pylint: disable=cmk-module-layer-violation

from cmk.base.plugin_contexts import (  # pylint: disable=cmk-module-layer-violation
    host_name,
    service_description,
)

from cmk.plugins.lib.robotmk_rebot_xml import Keyword, Outcome, RFTest
from cmk.plugins.lib.robotmk_suite_and_test_checking import message_if_rebot_is_too_old
from cmk.plugins.lib.robotmk_suite_execution_report import Section

from .agent_based_api.v1 import (
    check_levels,
    IgnoreResults,
    Metric,
    regex,
    register,
    render,
    Result,
    Service,
    ServiceLabel,
    State,
)
from .agent_based_api.v1.type_defs import CheckResult, DiscoveryResult


class Params(TypedDict):
    test_runtime: tuple[int, int] | None
    runtime_thresholds_keywords: Sequence[tuple[str, tuple[int, int] | None]]


def discover(section: Section) -> DiscoveryResult:
    yield from (
        Service(
            item=test_name,
            labels=[
                ServiceLabel("robotmk/html_last_error_log", "yes"),
                ServiceLabel("robotmk/html_last_log", "yes"),
            ],
        )
        for test_name in section.tests
    )


def check(
    item: str,
    params: Params,
    section: Section,
) -> CheckResult:
    if not (test_report := section.tests.get(item)):
        return

    _transmit_to_livestatus(test_report.html, "suite_last_log.html")
    if test_report.test.status.status is Outcome.FAIL:
        _transmit_to_livestatus(test_report.html, "suite_last_error_log.html")

    yield from _check_test_and_keywords(
        params,
        test_report.test,
        rebot_timestamp=test_report.rebot_timestamp,
        execution_interval=test_report.attempts_config.interval,
        now=time(),
    )


def _check_test_and_keywords(
    params: Params,
    test: RFTest,
    *,
    rebot_timestamp: int,
    execution_interval: int,
    now: float,
) -> CheckResult:
    if (
        rebot_too_old_message := message_if_rebot_is_too_old(
            rebot_timestamp=rebot_timestamp,
            execution_interval=execution_interval,
            now=now,
        )
    ) is not None:
        yield IgnoreResults(rebot_too_old_message)
        return

    if test.robot_exit:
        yield IgnoreResults("Test has `robot:exit` tag")
        return

    yield Result(state=State.OK, summary=test.name)
    yield Result(state=_remap_state(test.status.status), summary=f"{test.status.status.value}")
    if test.status.status is Outcome.PASS and test.status.runtime is not None:
        yield from check_levels(
            test.status.runtime,
            label="Test runtime",
            levels_upper=params["test_runtime"],
            metric_name="robotmk_test_runtime",
            render_func=render.timespan,
        )

    for keyword in test.keywords:
        if (
            keyword.status.status.status is Outcome.PASS
            and (runtime := keyword.status.status.runtime) is not None
        ):
            yield from _check_keyword(
                runtime_thresholds=params["runtime_thresholds_keywords"],
                keyword=keyword,
                runtime=runtime,
            )


def _check_keyword(
    *,
    runtime_thresholds: Sequence[tuple[str, tuple[int, int] | None]],
    keyword: Keyword,
    runtime: float,
) -> CheckResult:
    for pattern, thresholds in runtime_thresholds:
        if regex(pattern).match(keyword.name):
            if thresholds:
                yield from check_levels(
                    runtime,
                    label=f"Keyword {keyword.name} runtime",
                    levels_upper=thresholds,
                    metric_name=f"robotmk_{keyword.metric_name}_runtime",
                    render_func=render.timespan,
                )
                return

            yield Metric(f"robotmk_{keyword.metric_name}_runtime", runtime)
            return


def _transmit_to_livestatus(
    content: bytes,
    filename: Literal["suite_last_log.html", "suite_last_error_log.html"],
) -> None:
    file_path = Path(robotmk_html_log_dir) / host_name() / service_description() / filename
    file_path.parent.absolute().mkdir(exist_ok=True, parents=True)
    # I'm sure there are no race conditions between livestatus and the checkengine here.
    file_path.write_bytes(content)


def _remap_state(status: Outcome) -> State:
    match status:
        case Outcome.PASS:
            return State.OK
        case Outcome.FAIL:
            return State.CRIT
        case Outcome.NOT_RUN | Outcome.SKIP:
            return State.WARN
        case _:
            assert_never(status)


register.check_plugin(
    name="robotmk_test",
    sections=["robotmk_suite_execution_report"],
    service_name="RMK Test %s",
    discovery_function=discover,
    check_function=check,
    check_ruleset_name="robotmk",
    check_default_parameters=Params(test_runtime=None, runtime_thresholds_keywords=[]),
)
