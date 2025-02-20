#!/usr/bin/env python3
# Copyright (C) 2021 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

from collections.abc import Sequence

import pytest

from tests.testlib.utils import is_cloud_repo, is_enterprise_repo

from tests.unit.cmk.conftest import import_plugins

from cmk.post_rename_site import main
from cmk.post_rename_site.registry import rename_action_registry


@pytest.fixture(name="expected_plugins")
def fixture_expected_plugins() -> list[str]:
    expected = [
        "sites",
        "hosts_and_folders",
        "update_core_config",
        "warn_remote_site",
        "warn_about_network_ports",
        "warn_about_configs_to_review",
    ]

    # ATTENTION. The edition related code below is confusing and incorrect. The reason we need it
    # because our test environments do not reflect our Checkmk editions properly.
    # We cannot fix that in the short (or even mid) term because the
    # precondition is a more cleanly separated structure.
    if is_enterprise_repo():
        # The CEE plugins are loaded when the CEE plugins are available, i.e.
        # when the "enterprise/" path is present.
        expected.append("dcd_connections")

    if is_cloud_repo():
        # The CCE plugins are loaded when the CCE plugins are available
        expected.append("agent_controller_connections")

    return expected


@import_plugins(["cmk.post_rename_site"])
def test_load_plugins(expected_plugins: Sequence[str]) -> None:
    """The test changes a global variable `rename_action_registry`.
    We can't reliably monkey patch this variable - must use separate module for testing"""
    main.load_plugins()
    assert sorted(rename_action_registry.keys()) == sorted(expected_plugins)
