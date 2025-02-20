#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

from base64 import b32decode
from datetime import datetime

from tests.testlib.playwright.helpers import PPage

from cmk.utils.totp import TOTP


def test_totp(
    logged_in_page: PPage,
) -> None:
    # first go to dashboard to ensure we're reloading the page in case we're already there
    logged_in_page.goto_main_dashboard()
    # On two factor registration page
    logged_in_page.main_menu.user.click()
    logged_in_page.main_menu.locator("text=Two-factor authentication").click()
    # On the App Authenticator page
    logged_in_page.main_area.check_page_title("Two-factor authentication")
    logged_in_page.main_area.get_suggestion("Add Authenticator App").click()
    # Now extract TOTP secret from text and submit
    logged_in_page.main_area.check_page_title("Register Authenticator App")
    text_list = logged_in_page.main_area.locator(
        "text=Alternatively you can enter your secret manually: "
    ).all_text_contents()
    assert len(text_list) == 1
    secret = text_list[0].split(" ")[-1]
    authenticator = TOTP(b32decode(secret))
    current_time = authenticator.calculate_generation(datetime.now())
    otp_value = authenticator.generate_totp(current_time)
    logged_in_page.main_area.get_input("profile_p_ValidateOTP").fill(otp_value)
    logged_in_page.main_area.get_suggestion("Save").click()
    # Removing the two factor mechanism
    logged_in_page.main_area.locator("a[title='Delete two-factor credential']").click()
    logged_in_page.main_area.locator("button:has-text('Delete')").click()
