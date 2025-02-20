#!/usr/bin/env python3
# Copyright (C) 2022 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.
"""This module implements password hashing and validation of password hashes.

The password hashing functions return hashes in the Modular Crypto Format
(https://passlib.readthedocs.io/en/stable/modular_crypt_format.html#modular-crypt-format).

The format contains an identifier for the hash algorithm that was used, the number of rounds,
a salt, and the actual checksum -- which is all the information needed to verify the hash with a
given password (see `verify`).
"""
import logging
import re
import sys

import bcrypt

from cmk.utils.crypto.password import Password, PasswordHash
from cmk.utils.exceptions import MKException

logger = logging.getLogger(__name__)

# Using code should not be able to change the number of rounds (to unsafe values), but test code
# has to run with reduced rounds. They can be monkeypatched here.
BCRYPT_ROUNDS = 12


class PasswordTooLongError(MKException):
    """Indicates that the provided password is too long to be used

    Currently this will happen when trying to hash a password longer than 72 bytes due to
    restrictions of bcrypt.
    """


class PasswordInvalidError(MKException):
    """Indicates that the provided password could not be verified"""


def hash_password(password: Password, *, allow_truncation: bool = False) -> PasswordHash:
    """Hash a password using the preferred algorithm

    Uses bcrypt with 12 rounds to hash a password.

    :param password: The password to hash. The password must not be longer than 72 bytes (except if
                     allow_truncation is set).
    :param allow_truncation: Allow passwords longer than 72 bytes and silently truncate them.
                             This should be avoided but is required for some use cases.

    :return: The hashed password Modular Crypto Format (see module docstring). The identifier used
             for bcrypt is "2y" for compatibility with htpasswd.

    :raise: PasswordTooLongError if the provided password is longer than 72 bytes.
    :raise: ValueError if the input password contains null bytes.
    """

    if len(password.raw_bytes) <= 72 or allow_truncation:
        hash_pass = bcrypt.hashpw(password.raw_bytes, bcrypt.gensalt(BCRYPT_ROUNDS)).decode("utf-8")
        assert hash_pass.startswith("$2b$")
        return PasswordHash(
            "$2y$" + hash_pass.removeprefix("$2b$")
        )  # Forcing 2y for htpasswd, bcrypt will still verify 2y hashes but not generate them.
    raise PasswordTooLongError("Password too long")


def verify(password: Password, password_hash: PasswordHash) -> None:
    """Verify if a password matches a password hash.

    :param password: The password to check.
    :param password_hash: The password hash to check.

    :return: None if the password is valid; raises an exception otherwise (see below).

    :raise: PasswordInvalidError if the password does not match the hash.
    """
    if not bcrypt.checkpw(password.raw_bytes, password_hash.encode("utf-8")):
        logger.warning(
            "Invalid hash. Only bcrypt is supported.",
            exc_info=sys.exc_info(),
        )
        if "\0" in password_hash:
            raise ValueError("Null character identified in password hash.")
        raise PasswordInvalidError("Checkmk failed to validate the provided password")


def is_unsupported_legacy_hash(password_hash: PasswordHash) -> bool:
    """Was the hash algorithm used for this hash once supported but isn't anymore?"""
    regex_list = [
        r"^\$5\$(rounds=[0-9]+\$)?[a-zA-Z0-9\/.]{0,16}\$[a-zA-Z0-9\/.]{43}$",  # SHA256 crypt
        r"^\$1\$[a-zA-Z0-9\/.]{0,8}\$[a-zA-Z0-9\/.]{22}",  # MD5 crypt
        r"^\$apr1\$[a-zA-Z0-9\/.]{0,8}\$[a-zA-Z0-9\/.]{22}$",  # Apache MD5
        r"^[a-zA-Z0-9\/.]{13}$",  # DES crypt
    ]
    for regex in regex_list:
        if re.match(regex, password_hash):
            return True
    return False
