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

from robapi.model.user import UserManager

import robapi.db.driver as driver
import robapi.error as err
import robapi.tests.db as db
import robapi.model.user as auth


class TestUserManager(object):
    """Test user registration and password reset."""
    def test_activate_user(self, tmpdir):
        """Test creating inactive users and activating them."""
        # Create an inactive user.
        con = db.init_db(str(tmpdir)).connect()
        umanager = UserManager(con)
        user = umanager.register_user('nouser@me.com', 'pwd1', verify=True)
        # Attempt to login will raise error
        with pytest.raises(err.UnknownUserError):
            umanager.login('nouser@me.com', 'pwd1')
        # After activating the user login should succeed
        active_user = umanager.activate_user(user.identifier)
        assert active_user.identifier == user.identifier
        assert active_user.name == user.name
        assert active_user.api_key is None
        user = umanager.login('nouser@me.com', 'pwd1')
        assert user.name == 'nouser@me.com'
        assert not user.api_key is None
        user_id = auth.authenticate(con, user.api_key).identifier
        assert user.identifier == user_id
        # Activate the same user twice should not raise an error
        active_user = umanager.activate_user(user.identifier)
        assert active_user.identifier == user.identifier
        assert active_user.name == user.name
        assert active_user.api_key is None
        # Activate an unknown user will raise an error
        with pytest.raises(err.UnknownUserError):
            umanager.activate_user('UNK')

    def test_register_user(self, tmpdir):
        """Test registering a new user."""
        con = db.init_db(str(tmpdir)).connect()
        umanager = UserManager(con)
        reg_user = umanager.register_user('first.user@me.com', 'pwd1')
        assert reg_user.api_key is None
        user_1 = umanager.login('first.user@me.com', 'pwd1')
        assert user_1.name == 'first.user@me.com'
        user_id_1 = auth.authenticate(con, user_1.api_key).identifier
        assert user_1.identifier == user_id_1
        umanager.register_user('second.user@me.com', 'pwd2')
        user_2 = umanager.login('second.user@me.com', 'pwd2')
        assert user_2.name == 'second.user@me.com'
        user_id_2 = auth.authenticate(con, user_2.api_key).identifier
        assert user_2.identifier == user_id_2
        # Register user with existing email address raises error
        with pytest.raises(err.DuplicateUserError):
            umanager.register_user('first.user@me.com', 'pwd1')
        # Providing invalid email or passowrd will raise error
        with pytest.raises(err.ConstraintViolationError):
            umanager.register_user(None, 'pwd1')
        with pytest.raises(err.ConstraintViolationError):
            umanager.register_user(' \t', 'pwd1')
        with pytest.raises(err.ConstraintViolationError):
            umanager.register_user('a' * 513, 'pwd1')
        with pytest.raises(err.ConstraintViolationError):
            umanager.register_user('valid.name@me.com', ' ')

    def test_reset_password(self, tmpdir):
        """Test resetting a user password."""
        con = db.init_db(str(tmpdir)).connect()
        umanager = UserManager(con)
        umanager.register_user('first.user@me.com', 'pwd1')
        user = umanager.login('first.user@me.com', 'pwd1')
        assert user.name == 'first.user@me.com'
        user_id = auth.authenticate(con, user.api_key).identifier
        assert user.identifier == user_id
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
            auth.authenticate(con, user.api_key)
        user = umanager.login('first.user@me.com', 'mypwd')
        assert user.name == 'first.user@me.com'
        user_id = auth.authenticate(con, user.api_key).identifier
        assert user.identifier == user_id
        # An error is raised when (i) trying to use a request for an unknown
        # user, (ii) a previously completed reset request, or (iii) an unknown
        # request identifier to reset a user password
        with pytest.raises(err.UnknownRequestError):
            umanager.reset_password(request_id=request_id_1, password='mypwd')
        with pytest.raises(err.UnknownRequestError):
            umanager.reset_password(request_id=request_id_2, password='mypwd')
        with pytest.raises(err.UnknownRequestError):
            umanager.reset_password(request_id='unknown', password='mypwd')

    def test_reset_request_timeout(self, tmpdir):
        """Test resetting a user password using a request identifier that has
        timed out.
        """
        con = db.init_db(str(tmpdir)).connect()
        umanager = UserManager(con, login_timeout=1)
        umanager.register_user('first.user@me.com', 'pwd1')
        user = umanager.login('first.user@me.com', 'pwd1')
        assert user.name == 'first.user@me.com'
        user_id = auth.authenticate(con, user.api_key).identifier
        assert user.identifier == user_id
        # Hack: Manipulate the login_timeout value to similate timeout
        umanager.login_timeout = 1
        # Request reset and sleep for two seconds. This should allow the request
        # to timeout
        request_id = umanager.request_password_reset('first.user@me.com')
        time.sleep(2)
        with pytest.raises(err.UnknownRequestError):
            umanager.reset_password(request_id=request_id, password='mypwd')
