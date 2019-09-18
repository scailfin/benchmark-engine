# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""Test API methods for user resources and login/logout."""

import pytest

from robapi.model.user import UserManager
from robapi.service.user import UserService

import robapi.serialize.hateoas as hateoas
import robapi.serialize.labels as labels
import robapi.tests.db as db
import robtmpl.util as util


"""Mandatory labels in a user handle for users that are currently logged in or
logged out.
"""
USER_LOGIN = [labels.ID, labels.USERNAME, labels.ACCESS_TOKEN, labels.LINKS]
USER_LOGOUT = [labels.ID, labels.USERNAME, labels.LINKS]


class TestUserApi(object):
    """Test API methods that access and manipulate users."""
    def test_authenticate_user(self, tmpdir):
        """Test login and logout via API."""
        users = UserService(UserManager(db.init_db(str(tmpdir)).connect()))
        # Register a new user that is automatically activated
        users.register_user(username='myuser', password='mypwd', verify=False)
        # Login
        r = users.login_user(username='myuser', password='mypwd')
        util.validate_doc(doc=r, mandatory_labels=USER_LOGIN)
        links = hateoas.deserialize(r[labels.LINKS])
        util.validate_doc(
            doc=links,
            mandatory_labels=[
                hateoas.user(hateoas.WHOAMI),
                hateoas.user(hateoas.LOGOUT)
            ]
        )
        access_token = r[labels.ACCESS_TOKEN]
        r = users.whoami_user(access_token)
        util.validate_doc(doc=r, mandatory_labels=USER_LOGIN)
        links = hateoas.deserialize(r[labels.LINKS])
        util.validate_doc(
            doc=links,
            mandatory_labels=[
                hateoas.user(hateoas.WHOAMI),
                hateoas.user(hateoas.LOGOUT)
            ]
        )
        # Logout
        r = users.logout_user(access_token)
        util.validate_doc(doc=r, mandatory_labels=USER_LOGOUT)
        links = hateoas.deserialize(r[labels.LINKS])
        util.validate_doc(
            doc=links,
            mandatory_labels=[
                hateoas.user(hateoas.WHOAMI),
                hateoas.user(hateoas.LOGIN)
            ]
        )

    def test_register_user(self, tmpdir):
        """Test new user registration via API."""
        users = UserService(UserManager(db.init_db(str(tmpdir)).connect()))
        # Register a new user without activating the user
        r = users.register_user(username='myuser', password='mypwd', verify=True)
        util.validate_doc(doc=r, mandatory_labels=USER_LOGOUT)
        links = hateoas.deserialize(r[labels.LINKS])
        util.validate_doc(
            doc=links,
            mandatory_labels=[
                hateoas.user(hateoas.WHOAMI),
                hateoas.user(hateoas.LOGIN),
                hateoas.user(hateoas.ACTIVATE)
            ]
        )
        # Activate the user
        r = users.activate_user(r[labels.ID])
        util.validate_doc(doc=r, mandatory_labels=USER_LOGOUT)
        links = hateoas.deserialize(r[labels.LINKS])
        util.validate_doc(
            doc=links,
            mandatory_labels=[
                hateoas.user(hateoas.WHOAMI),
                hateoas.user(hateoas.LOGIN)
            ]
        )
        # Register a new user that is automatically activated
        r = users.register_user(username='myuser2', password='mypwd', verify=False)
        util.validate_doc(doc=r, mandatory_labels=USER_LOGOUT)
        links = hateoas.deserialize(r[labels.LINKS])
        util.validate_doc(
            doc=links,
            mandatory_labels=[
                hateoas.user(hateoas.WHOAMI),
                hateoas.user(hateoas.LOGIN)
            ]
        )
