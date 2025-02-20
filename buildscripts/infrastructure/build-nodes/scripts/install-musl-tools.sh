#!/bin/bash
# Copyright (C) 2021 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

set -e -o pipefail

case "$DISTRO" in
    ubuntu-*)
        # installable on all Ubuntu versions to be potentially usable by developers
        echo "Installing for Ubuntu"

        apt-get update
        apt-get install -y musl-tools
        rm -rf /var/lib/apt/lists/*

        # Test the installation
        musl-gcc --version || exit $?
        ;;
    *)
        # We need musl to build a static binary of the agent controller. The agent controller is only
        # built in the Ubuntu 20.04 image, hence, we only need musl there.
        echo "ERROR: Unhandled DISTRO: $DISTRO - musl-tools should only be available in Ubuntu!"
        exit 1
        ;;
esac
