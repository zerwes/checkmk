#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

# pylint: disable=redefined-outer-name

from collections.abc import Callable, Sequence

import pytest

from cmk.special_agents.agent_aws import (
    AWSConfig,
    ELB,
    ELBHealth,
    ELBLabelsGeneric,
    ELBLimits,
    ELBSummaryGeneric,
    NamingConvention,
    OverallTags,
    ResultDistributor,
)

from .agent_aws_fake_clients import (
    ELBDescribeAccountLimitsIB,
    ELBDescribeInstanceHealthIB,
    ELBDescribeLoadBalancersIB,
    ELBDescribeTagsIB,
    FakeCloudwatchClient,
)


class Paginator:
    def paginate(self, LoadBalancerNames=None):
        load_balancers = ELBDescribeLoadBalancersIB.create_instances(amount=3)
        if LoadBalancerNames is not None:
            load_balancers = [
                load_balancer
                for load_balancer in load_balancers
                if load_balancer["LoadBalancerName"] in LoadBalancerNames
            ]
        yield {
            "LoadBalancerDescriptions": load_balancers,
            "NextMarker": "string",
        }


class FakeELBClient:
    def describe_account_limits(self):
        return {
            "Limits": ELBDescribeAccountLimitsIB.create_instances(amount=1)[0]["Limits"],
            "NextMarker": "string",
        }

    def describe_tags(self, LoadBalancerNames=None):
        tag_descrs = []
        for lb_name in LoadBalancerNames:
            if lb_name not in ["LoadBalancerName-0", "LoadBalancerName-1"]:
                continue
            tag_descrs.extend(ELBDescribeTagsIB.create_instances(amount=1))
        return {"TagDescriptions": tag_descrs}

    def describe_instance_health(self, LoadBalancerName=None):
        return {"InstanceStates": ELBDescribeInstanceHealthIB.create_instances(amount=1)}

    def get_paginator(self, operation_name):
        if operation_name == "describe_load_balancers":
            return Paginator()
        raise NotImplementedError


ELBSections = Callable[
    [object | None, OverallTags],
    tuple[ELBLimits, ELBSummaryGeneric, ELBLabelsGeneric, ELBHealth, ELB],
]


@pytest.fixture()
def get_elb_sections() -> ELBSections:
    def _create_elb_sections(
        names: object | None, tags: OverallTags
    ) -> tuple[ELBLimits, ELBSummaryGeneric, ELBLabelsGeneric, ELBHealth, ELB]:
        region = "region"
        config = AWSConfig("hostname", [], ([], []), NamingConvention.ip_region_instance)
        config.add_single_service_config("elb_names", names)
        config.add_service_tags("elb_tags", tags)

        fake_elb_client = FakeELBClient()
        fake_cloudwatch_client = FakeCloudwatchClient()

        distributor = ResultDistributor()

        # TODO: FakeELBClient shoud actually subclass ELBClient.
        elb_limits = ELBLimits(fake_elb_client, region, config, distributor)  # type: ignore[arg-type]
        elb_summary = ELBSummaryGeneric(
            fake_elb_client, region, config, distributor, resource="elb"  # type: ignore[arg-type]
        )
        elb_labels = ELBLabelsGeneric(fake_elb_client, region, config, resource="elb")  # type: ignore[arg-type]
        elb_health = ELBHealth(fake_elb_client, region, config)  # type: ignore[arg-type]
        elb = ELB(fake_cloudwatch_client, region, config)  # type: ignore[arg-type]

        distributor.add(elb_limits.name, elb_summary)
        distributor.add(elb_summary.name, elb_labels)
        distributor.add(elb_summary.name, elb_health)
        distributor.add(elb_summary.name, elb)
        return elb_limits, elb_summary, elb_labels, elb_health, elb

    return _create_elb_sections


elb_params = [
    (
        None,
        (None, None),
        ["LoadBalancerName-0", "LoadBalancerName-1", "LoadBalancerName-2"],
        ["LoadBalancerName-0", "LoadBalancerName-1"],
    ),
    (None, ([["FOO"]], [["BAR"]]), [], []),
    (
        None,
        ([["Key-0"]], [["Value-0"]]),
        ["LoadBalancerName-0", "LoadBalancerName-1"],
        ["LoadBalancerName-0", "LoadBalancerName-1"],
    ),
    (
        None,
        ([["Key-0", "Foo"]], [["Value-0", "Bar"]]),
        ["LoadBalancerName-0", "LoadBalancerName-1"],
        ["LoadBalancerName-0", "LoadBalancerName-1"],
    ),
    (["LoadBalancerName-0"], (None, None), ["LoadBalancerName-0"], ["LoadBalancerName-0"]),
    (
        ["LoadBalancerName-0", "Foobar"],
        (None, None),
        ["LoadBalancerName-0"],
        ["LoadBalancerName-0"],
    ),
    (
        ["LoadBalancerName-0", "LoadBalancerName-1"],
        (None, None),
        ["LoadBalancerName-0", "LoadBalancerName-1"],
        ["LoadBalancerName-0", "LoadBalancerName-1"],
    ),
    (
        ["LoadBalancerName-0", "LoadBalancerName-2"],
        (None, None),
        ["LoadBalancerName-0", "LoadBalancerName-2"],
        ["LoadBalancerName-0"],
    ),
    (["LoadBalancerName-2"], ([["FOO"]], [["BAR"]]), ["LoadBalancerName-2"], []),
]


@pytest.mark.parametrize("names,tags,found_instances,found_instances_with_labels", elb_params)
def test_agent_aws_elb_limits(
    get_elb_sections: ELBSections,
    names: Sequence[str] | None,
    tags: OverallTags,
    found_instances: Sequence[str],
    found_instances_with_labels: Sequence[str],
) -> None:
    elb_limits, _elb_summary, _elb_labels, _elb_health, _elb = get_elb_sections(names, tags)
    elb_limits_results = elb_limits.run().results

    assert elb_limits.cache_interval == 300
    assert elb_limits.period == 600
    assert elb_limits.name == "elb_limits"
    assert len(elb_limits_results) == 4
    for result in elb_limits_results:
        if result.piggyback_hostname == "":
            assert len(result.content) == 1
        else:
            assert len(result.content) == 2


@pytest.mark.parametrize("names,tags,found_instances,found_instances_with_labels", elb_params)
def test_agent_aws_elb_summary(
    get_elb_sections, names, tags, found_instances, found_instances_with_labels
):
    elb_limits, elb_summary, _elb_labels, _elb_health, _elb = get_elb_sections(names, tags)
    _elb_limits_results = elb_limits.run().results
    elb_summary_results = elb_summary.run().results

    assert elb_summary.cache_interval == 300
    assert elb_summary.period == 600
    assert elb_summary.name == "elb_summary"

    if found_instances:
        assert len(elb_summary_results) == 1
        elb_summary_result = elb_summary_results[0]
        assert elb_summary_result.piggyback_hostname == ""
        assert len(elb_summary_result.content) == len(found_instances)

    else:
        assert len(elb_summary_results) == 0


@pytest.mark.parametrize("names,tags,found_instances,found_instances_with_labels", elb_params)
def test_agent_aws_elb_labels(
    get_elb_sections, names, tags, found_instances, found_instances_with_labels
):
    elb_limits, elb_summary, elb_labels, _elb_health, _elb = get_elb_sections(names, tags)
    _elb_limits_results = elb_limits.run().results
    _elb_summary_results = elb_summary.run().results
    elb_labels_results = elb_labels.run().results

    assert elb_labels.cache_interval == 300
    assert elb_labels.period == 600
    assert elb_labels.name == "elb_generic_labels"
    assert len(elb_labels_results) == len(found_instances_with_labels)
    for result in elb_labels_results:
        assert result.piggyback_hostname != ""


@pytest.mark.parametrize("names,tags,found_instances,found_instances_with_labels", elb_params)
def test_agent_aws_elb_health(
    get_elb_sections, names, tags, found_instances, found_instances_with_labels
):
    elb_limits, elb_summary, _elb_labels, elb_health, _elb = get_elb_sections(names, tags)
    _elb_limits_results = elb_limits.run().results
    _elb_summary_results = elb_summary.run().results
    elb_health_results = elb_health.run().results

    assert elb_health.cache_interval == 300
    assert elb_health.period == 600
    assert elb_health.name == "elb_health"
    assert len(elb_health_results) == len(found_instances)
    for result in elb_health_results:
        assert result.piggyback_hostname != ""


@pytest.mark.parametrize("names,tags,found_instances,found_instances_with_labels", elb_params)
def test_agent_aws_elb(
    get_elb_sections: ELBSections,
    names: Sequence[str] | None,
    tags: OverallTags,
    found_instances: Sequence[str],
    found_instances_with_labels: Sequence[str],
) -> None:
    elb_limits, elb_summary, _elb_labels, _elb_health, elb = get_elb_sections(names, tags)
    _elb_limits_results = elb_limits.run().results
    _elb_summary_results = elb_summary.run().results
    elb_results = elb.run().results

    assert elb.cache_interval == 300
    assert elb.period == 600
    assert elb.name == "elb"
    assert len(elb_results) == len(found_instances)
    for result in elb_results:
        assert result.piggyback_hostname != ""
        # 13 metrics
        assert len(result.content) == 13


@pytest.mark.parametrize("names,tags,found_instances,found_instances_with_labels", elb_params)
def test_agent_aws_elb_summary_without_limits(
    get_elb_sections, names, tags, found_instances, found_instances_with_labels
):
    _elb_limits, elb_summary, _elb_labels, _elb_health, _elb = get_elb_sections(names, tags)
    elb_summary_results = elb_summary.run().results

    assert elb_summary.cache_interval == 300
    assert elb_summary.period == 600
    assert elb_summary.name == "elb_summary"

    if found_instances:
        assert len(elb_summary_results) == 1
        elb_summary_result = elb_summary_results[0]
        assert elb_summary_result.piggyback_hostname == ""
        assert len(elb_summary_result.content) == len(found_instances)

    else:
        assert len(elb_summary_results) == 0


@pytest.mark.parametrize("names,tags,found_instances,found_instances_with_labels", elb_params)
def test_agent_aws_elb_labels_without_limits(
    get_elb_sections, names, tags, found_instances, found_instances_with_labels
):
    _elb_limits, elb_summary, elb_labels, _elb_health, _elb = get_elb_sections(names, tags)
    _elb_summary_results = elb_summary.run().results
    elb_labels_results = elb_labels.run().results

    assert elb_labels.cache_interval == 300
    assert elb_labels.period == 600
    assert elb_labels.name == "elb_generic_labels"
    assert len(elb_labels_results) == len(found_instances_with_labels)
    for result in elb_labels_results:
        assert result.piggyback_hostname != ""


@pytest.mark.parametrize("names,tags,found_instances,found_instances_with_labels", elb_params)
def test_agent_aws_elb_health_without_limits(
    get_elb_sections, names, tags, found_instances, found_instances_with_labels
):
    _elb_limits, elb_summary, _elb_labels, elb_health, _elb = get_elb_sections(names, tags)
    _elb_summary_results = elb_summary.run().results
    elb_health_results = elb_health.run().results

    assert elb_health.cache_interval == 300
    assert elb_health.period == 600
    assert elb_health.name == "elb_health"
    assert len(elb_health_results) == len(found_instances)
    for result in elb_health_results:
        assert result.piggyback_hostname != ""


@pytest.mark.parametrize("names,tags,found_instances,found_instances_with_labels", elb_params)
def test_agent_aws_elb_without_limits(
    get_elb_sections, names, tags, found_instances, found_instances_with_labels
):
    _elb_limits, elb_summary, _elb_labels, _elb_health, elb = get_elb_sections(names, tags)
    _elb_summary_results = elb_summary.run().results
    elb_results = elb.run().results

    assert elb.cache_interval == 300
    assert elb.period == 600
    assert elb.name == "elb"
    assert len(elb_results) == len(found_instances)
    for result in elb_results:
        assert result.piggyback_hostname != ""
        # 13 metrics
        assert len(result.content) == 13
