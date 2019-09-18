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

from benchengine.db import DatabaseDriver
from benchengine.user.auth import Auth

import benchengine.error as err
import benchtmpl.util.core as util


USER_1 = util.get_unique_identifier()
USER_2 = util.get_unique_identifier()
USER_3 = util.get_unique_identifier()


class TestUserAuthentication(object):
    """Test login and logout functionality."""
    def connect(self, base_dir):
        """Create empty database and open connection."""
        connect_string = 'sqlite:{}/auth.db'.format(str(base_dir))
        DatabaseDriver.init_db(connect_string=connect_string)
        con = DatabaseDriver.connect(connect_string=connect_string)
        sql = 'INSERT INTO registered_user(id, email, secret, active) VALUES(?, ?, ?, ?)'
        con.execute(sql, (USER_1, USER_1, pbkdf2_sha256.hash(USER_1), 1))
        con.execute(sql, (USER_2, USER_2, pbkdf2_sha256.hash(USER_2), 1))
        con.execute(sql, (USER_3, USER_3, pbkdf2_sha256.hash(USER_3), 0))
        con.commit()
        return con

    def test_authenticate(self, tmpdir):
        """Test user login and logout."""
        auth = Auth(self.connect(tmpdir))
        # Login user 1 and 2
        api_key_1 = auth.login(USER_1, USER_1)
        api_key_2 = auth.login(USER_2, USER_2)
        # Authenticate user 1
        user = auth.authenticate(api_key_1)
        assert user.identifier == USER_1
        assert user.email == USER_1
        # Authenticate user 2
        user = auth.authenticate(api_key_2)
        assert user.identifier == USER_2
        assert user.email == USER_2
        # Logout user 1
        auth.logout(api_key_1)
        # Authenticating user 1 will raise exception
        with pytest.raises(err.UnauthenticatedAccessError):
            auth.authenticate(api_key_1)
        # User 2 can still authenticate
        user = auth.authenticate(api_key_2)
        assert user.identifier == USER_2
        assert user.email == USER_2
        # Re-login user 1 and authenticate
        api_key_1 = auth.login(USER_1, USER_1)
        user = auth.authenticate(api_key_1)
        assert user.identifier == USER_1
        assert user.email == USER_1
        # If a user logs in again all previous keys become invalid
        api_key_3 = auth.login(USER_1, USER_1)
        with pytest.raises(err.UnauthenticatedAccessError):
            auth.authenticate(api_key_1)
        # Attempt to authenticate unknown user raises error
        with pytest.raises(err.UnknownUserError):
            auth.login('unknown', USER_1)
        # Attempt to authenticate wilt invalid password will raises error
        with pytest.raises(err.UnknownUserError):
            auth.login(USER_1, USER_2)
        # Attempting to login for inactive user raises error
        with pytest.raises(err.UnknownUserError):
            auth.login(USER_3, USER_3)

    def test_login_timeout(self, tmpdir):
        """Test login after key expired."""
        # Set login timeout to one second
        auth = Auth(self.connect(tmpdir), login_timeout=1)
        api_key = auth.login(USER_1, USER_1)
        # Wait for two seconds
        time.sleep(2)
        # Authenticating after timeout will raise error
        with pytest.raises(err.UnauthenticatedAccessError):
            auth.authenticate(api_key)

    def test_team_membership(self, tmpdir):
        """Ensure that the team owner and membership functions return True if
        the team does not exist.
        """
        auth = Auth(self.connect(tmpdir))
        assert auth.is_team_owner(team_id='unknown', user_id=USER_1)
        assert auth.is_team_member(team_id='unknown', user_id=USER_1)
