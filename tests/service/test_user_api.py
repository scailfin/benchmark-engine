# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""Test API methods for user resources and login/logout."""

import pytest

from robapi.model.auth import OpenAccessAuth
from robapi.model.user import UserManager
from robapi.service.user import UserService

import robapi.serialize.hateoas as hateoas
import robapi.serialize.labels as labels
import robapi.tests.db as db
import robapi.tests.serialize as serialize
import robtmpl.util as util


"""Mandatory labels in a user handle for users that are currently logged in or
logged out.
"""
USER_LOGIN = [labels.ID, labels.USERNAME, labels.ACCESS_TOKEN, labels.LINKS]
USER_LOGOUT = [labels.ID, labels.USERNAME, labels.LINKS]


class TestUserApi(object):
    """Test API methods that access and manipulate users."""
    def init(self, base_dir):
        """Initialize the dabase and the user manager. Returns the user manager
        instance.
        """
        con = db.init_db(base_dir).connect()
        return UserService(manager=UserManager(con), auth=OpenAccessAuth(con))

    def test_authenticate_user(self, tmpdir):
        """Test login and logout via API."""
        users = self.init(str(tmpdir))
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
        r = users.logout_user(users.auth.authenticate(access_token))
        util.validate_doc(doc=r, mandatory_labels=USER_LOGOUT)
        links = hateoas.deserialize(r[labels.LINKS])
        util.validate_doc(
            doc=links,
            mandatory_labels=[
                hateoas.user(hateoas.WHOAMI),
                hateoas.user(hateoas.LOGIN)
            ]
        )

    def test_list_users(self, tmpdir):
        """Test user listings and queries."""
        users = self.init(str(tmpdir))
        # Register three active users
        users.register_user(username='a@user', password='mypwd', verify=False)
        users.register_user(username='me@user', password='mypwd', verify=False)
        users.register_user(username='my@user', password='mypwd', verify=False)
        r = users.list_users()
        util.validate_doc(doc=r, mandatory_labels=[labels.USERS, labels.LINKS])
        serialize.validate_links(doc=r, keys=[hateoas.SELF])
        assert len(r[labels.USERS]) == 3
        for u in r[labels.USERS]:
            util.validate_doc(
                doc=u,
                mandatory_labels=[labels.ID, labels.USERNAME]
            )
        r = users.list_users(query='m')
        util.validate_doc(doc=r, mandatory_labels=[labels.USERS, labels.LINKS])
        assert len(r[labels.USERS]) == 2
        r = users.list_users(query='a')
        util.validate_doc(doc=r, mandatory_labels=[labels.USERS, labels.LINKS])
        assert len(r[labels.USERS]) == 1

    def test_register_user(self, tmpdir):
        """Test new user registration via API."""
        users = self.init(str(tmpdir))
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
