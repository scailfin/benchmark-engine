# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""Test functionality to authenticate a user."""

import os
import pytest
import time

from passlib.hash import pbkdf2_sha256

from robapi.model.user import UserManager

import robapi.error as err
import robapi.tests.db as db
import robapi.model.user as auth
import robtmpl.util as util


"""Unique identifier for test users."""
USER_1 = util.get_unique_identifier()
USER_2 = util.get_unique_identifier()
USER_3 = util.get_unique_identifier()


class TestUserAuthentication(object):
    """Unit tests for login and logout functionality."""
    def init_db(self, base_dir):
        """Create new database with three users. Returns an open connection to
        the database.
        """
        con = db.init_db(str(base_dir)).connect()
        sql = 'INSERT INTO api_user(user_id, name, secret, active) VALUES(?, ?, ?, ?)'
        con.execute(sql, (USER_1, USER_1, pbkdf2_sha256.hash(USER_1), 1))
        con.execute(sql, (USER_2, USER_2, pbkdf2_sha256.hash(USER_2), 1))
        con.execute(sql, (USER_3, USER_3, pbkdf2_sha256.hash(USER_3), 0))
        con.commit()
        return con

    def test_authenticate_user(self, tmpdir):
        """Test user login and logout."""
        con = self.init_db(str(tmpdir))
        users = UserManager(con)
        # Login user 1 and 2
        user_1 = users.login_user(USER_1, USER_1)
        user_2 = users.login_user(USER_2, USER_2)
        # Authenticate user 1
        assert auth.authenticate_user(con, user_1.api_key).identifier == USER_1
        # Authenticate user 2
        assert auth.authenticate_user(con, user_2.api_key).identifier == USER_2
        # Logout user 1
        loggedout_user = users.logout_user(user_1.api_key)
        assert loggedout_user.identifier == user_1.identifier
        assert loggedout_user.api_key is None
        # Authenticating user 1 will raise exception
        with pytest.raises(err.UnauthenticatedAccessError):
            auth.authenticate_user(con, user_1.api_key)
        # Logging out a user that is not logged in will raise error
        with pytest.raises(err.UnauthenticatedAccessError):
            users.logout_user(user_1.api_key)
        # User 2 can still authenticate
        assert auth.authenticate_user(con, user_2.api_key).identifier == USER_2
        # Re-login user 1 and authenticate
        user_1 = users.login_user(USER_1, USER_1)
        assert auth.authenticate_user(con, user_1.api_key).identifier == USER_1
        # If a user logs in again all previous keys become invalid
        user_3 = users.login_user(USER_1, USER_1)
        with pytest.raises(err.UnauthenticatedAccessError):
            auth.authenticate_user(con, user_1.api_key)
        # Attempt to authenticate unknown user raises error
        with pytest.raises(err.UnknownUserError):
            users.login_user('unknown', USER_1)
        # Attempt to authenticate wilt invalid password will raises error
        with pytest.raises(err.UnknownUserError):
            users.login_user(USER_1, USER_2)
        # Attempting to login for inactive user raises error
        with pytest.raises(err.UnknownUserError):
            users.login_user(USER_3, USER_3)

    def test_login_timeout(self, tmpdir):
        """Test login after key expired."""
        # Set login timeout to one second
        con = self.init_db(str(tmpdir))
        users = UserManager(con, login_timeout=1)
        api_key = users.login_user(USER_1, USER_1).api_key
        # Wait for two seconds
        time.sleep(2)
        # Authenticating after timeout will raise error
        with pytest.raises(err.UnauthenticatedAccessError):
            auth.authenticate_user(con, api_key)
