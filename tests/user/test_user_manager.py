# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""Test functionality of the user manager."""

import os
import pytest
import time

from benchengine.db import DatabaseDriver
from benchengine.user.manager import UserManager

import benchengine.error as err
import benchtmpl.util.core as util


class TestUserManager(object):
    """Test user registration and password reset."""
    def connect(self, base_dir):
        """Create a fresh database and return connected user manager."""
        connect_string = 'sqlite:{}/auth.db'.format(str(base_dir))
        DatabaseDriver.init_db(connect_string=connect_string)
        con = DatabaseDriver.connect(connect_string=connect_string)
        return UserManager(con)

    def test_activate_user(self, tmpdir):
        """Test creating inactive users and activating them."""
        # Create an inactive user.
        umanager = self.connect(tmpdir)
        user_id = umanager.register_user('nouser@me.com', 'pwd1', verify=True)
        # Attempt to login will raise error
        with pytest.raises(err.UnknownUserError):
            umanager.login('nouser@me.com', 'pwd1')
        # After activating the user login should succeed
        umanager.activate_user(user_id)
        api_key = umanager.login('nouser@me.com', 'pwd1')
        user = umanager.authenticate(api_key)
        assert user.email == 'nouser@me.com'

    def test_get_user(self, tmpdir):
        """Test getting user information."""
        umanager = self.connect(tmpdir)
        user_id = umanager.register_user('first.user@me.com', 'pwd1')
        user = umanager.get_user('first.user@me.com')
        assert user.identifier == user_id
        assert user.username == 'first.user@me.com'
        with pytest.raises(err.UnknownUserError):
            umanager.get_user('second.user@me.com')

    def test_list_user(self, tmpdir):
        """Test listing user."""
        umanager = self.connect(tmpdir)
        umanager.register_user('first.user@me.com', 'pwd1')
        umanager.register_user('second.user@me.com', 'pwd2')
        users = [u.username for u in umanager.list_user()]
        assert len(users) == 2
        assert 'first.user@me.com' in users
        assert 'second.user@me.com' in users
        for user in umanager.list_user():
            assert not user.is_logged_in()
        umanager.login('first.user@me.com', 'pwd1')
        umanager.login('second.user@me.com', 'pwd2')
        assert len(users) == 2
        for user in umanager.list_user():
            assert user.is_logged_in()

    def test_register_user(self, tmpdir):
        """Test registering a new user."""
        umanager = self.connect(tmpdir)
        umanager.register_user('first.user@me.com', 'pwd1')
        api_key_1 = umanager.login('first.user@me.com', 'pwd1')
        user = umanager.authenticate(api_key_1)
        assert user.email == 'first.user@me.com'
        assert user.email == user.username
        umanager.register_user('second.user@me.com', 'pwd2')
        api_key_2 = umanager.login('second.user@me.com', 'pwd2')
        user = umanager.authenticate(api_key_2)
        assert user.email == 'second.user@me.com'
        users = [u.username for u in umanager.list_user()]
        assert len(users) == 2
        assert 'first.user@me.com' in users
        assert 'second.user@me.com' in users
        # Register user with existing email address raises error
        with pytest.raises(err.DuplicateUserError):
            umanager.register_user('first.user@me.com', 'pwd1')
        # Providing invalid email or passowrd will raise error
        with pytest.raises(err.ConstraintViolationError):
            umanager.register_user('a' * 256, 'pwd1')
        with pytest.raises(err.ConstraintViolationError):
            umanager.register_user('valid.email@me.com', ' ')

    def test_reset_password(self, tmpdir):
        """Test resetting a user password."""
        umanager = self.connect(tmpdir)
        umanager.register_user('first.user@me.com', 'pwd1')
        api_key = umanager.login('first.user@me.com', 'pwd1')
        user = umanager.authenticate(api_key)
        assert user.email == 'first.user@me.com'
        request_id_1 = umanager.request_password_reset('first.user@me.com')
        assert not request_id_1 is None
        # Request reset for unknown user will return a reset request id
        request_id_2 = umanager.request_password_reset('unknown@me.com')
        assert not request_id_2 is None
        assert request_id_1 != request_id_2
        # Reset password for existing user
        umanager.reset_password(request_id=request_id_1, password='mypwd')
        # After resetting the password the previous API key for the user is
        # invalid
        with pytest.raises(err.UnauthenticatedAccessError):
            umanager.authenticate(api_key)
        api_key = umanager.login('first.user@me.com', 'mypwd')
        user = umanager.authenticate(api_key)
        assert user.email == 'first.user@me.com'
        # An error is raised when (i) trying to use a request for an unknown
        # user, (ii) a previously completed reset request, or (iii) an unknown
        # request identifier to reset a user password
        with pytest.raises(err.UnknownResourceError):
            umanager.reset_password(request_id=request_id_1, password='mypwd')
        with pytest.raises(err.UnknownResourceError):
            umanager.reset_password(request_id=request_id_2, password='mypwd')
        with pytest.raises(err.UnknownResourceError):
            umanager.reset_password(request_id='unknown', password='mypwd')

    def test_reset_request_timeout(self, tmpdir):
        """Test resetting a user password using a request identifier that has
        timed out.
        """
        umanager = self.connect(tmpdir)
        umanager.register_user('first.user@me.com', 'pwd1')
        api_key = umanager.login('first.user@me.com', 'pwd1')
        user = umanager.authenticate(api_key)
        assert user.email == 'first.user@me.com'
        # Hack: Manipulate the login_timeout value to similate timeout
        umanager.login_timeout = 1
        # Request reset and sleep for two seconds. This should allow the request
        # to timeout
        request_id = umanager.request_password_reset('first.user@me.com')
        time.sleep(2)
        with pytest.raises(err.UnknownResourceError):
            umanager.reset_password(request_id=request_id, password='mypwd')
