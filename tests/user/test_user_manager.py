"""Test functionality of the user manager."""

import os
import shutil
import time

from unittest import TestCase

from benchengine.db import DatabaseDriver
from benchengine.user.manager import UserManager

import benchengine.error as err
import benchtmpl.util.core as util


TMP_DIR = './tests/files/.tmp'
CONNECT = 'sqlite:{}/app.db'.format(TMP_DIR)


class TestUserManager(TestCase):
    """Test user registration and password reset."""
    def setUp(self):
        if os.path.isdir(TMP_DIR):
            shutil.rmtree(TMP_DIR)
        os.makedirs(TMP_DIR)
        """Create a fresh database and insert two default users."""
        DatabaseDriver.init_db(connect_string=CONNECT)
        con = DatabaseDriver.connect(connect_string=CONNECT)
        self.users = UserManager(con)

    def tearDown(self):
        """Close connection and remove database file."""
        self.users.close()
        if os.path.isdir(TMP_DIR):
            shutil.rmtree(TMP_DIR)

    def test_activate_user(self):
        """Test creating inactive users and activating them."""
        # Create an inactive user.
        user_id = self.users.register_user('nouser@me.com', 'pwd1', verify=True)
        # Attempt to login will raise error
        with self.assertRaises(err.UnknownUserError):
            self.users.login('nouser@me.com', 'pwd1')
        # After activating the user login should succeed
        self.users.activate_user(user_id)
        api_key = self.users.login('nouser@me.com', 'pwd1')
        user = self.users.authenticate(api_key)
        self.assertEqual(user.email, 'nouser@me.com')

    def test_get_user(self):
        """Test getting user information."""
        user_id = self.users.register_user('first.user@me.com', 'pwd1')
        user = self.users.get_user('first.user@me.com')
        self.assertEqual(user.identifier, user_id)
        self.assertEqual(user.username, 'first.user@me.com')
        with self.assertRaises(err.UnknownUserError):
            self.users.get_user('second.user@me.com')

    def test_list_user(self):
        """Test listing user."""
        self.users.register_user('first.user@me.com', 'pwd1')
        self.users.register_user('second.user@me.com', 'pwd2')
        users = [u.username for u in self.users.list_user()]
        self.assertEqual(len(users), 2)
        self.assertTrue('first.user@me.com' in users)
        self.assertTrue('second.user@me.com' in users)
        for user in self.users.list_user():
            self.assertFalse(user.is_logged_in())
        self.users.login('first.user@me.com', 'pwd1')
        self.users.login('second.user@me.com', 'pwd2')
        self.assertEqual(len(users), 2)
        for user in self.users.list_user():
            self.assertTrue(user.is_logged_in())

    def test_register_user(self):
        """Test registering a new user."""
        self.users.register_user('first.user@me.com', 'pwd1')
        api_key_1 = self.users.login('first.user@me.com', 'pwd1')
        user = self.users.authenticate(api_key_1)
        self.assertEqual(user.email, 'first.user@me.com')
        self.assertEqual(user.email, user.username)
        self.users.register_user('second.user@me.com', 'pwd2')
        api_key_2 = self.users.login('second.user@me.com', 'pwd2')
        user = self.users.authenticate(api_key_2)
        self.assertEqual(user.email, 'second.user@me.com')
        users = [u.username for u in self.users.list_user()]
        self.assertEqual(len(users), 2)
        self.assertTrue('first.user@me.com' in users)
        self.assertTrue('second.user@me.com' in users)
        # Register user with existing email address raises error
        with self.assertRaises(err.DuplicateUserError):
            self.users.register_user('first.user@me.com', 'pwd1')
        # Providing invalid email or passowrd will raise error
        with self.assertRaises(err.ConstraintViolationError):
            self.users.register_user('a' * 256, 'pwd1')
        with self.assertRaises(err.ConstraintViolationError):
            self.users.register_user('valid.email@me.com', ' ')

    def test_reset_password(self):
        """Test resetting a user password."""
        self.users.register_user('first.user@me.com', 'pwd1')
        api_key = self.users.login('first.user@me.com', 'pwd1')
        user = self.users.authenticate(api_key)
        self.assertEqual(user.email, 'first.user@me.com')
        request_id_1 = self.users.request_password_reset('first.user@me.com')
        self.assertIsNotNone(request_id_1)
        # Request reset for unknown user will return a reset request id
        request_id_2 = self.users.request_password_reset('unknown@me.com')
        self.assertIsNotNone(request_id_2)
        self.assertNotEqual(request_id_1, request_id_2)
        # Reset password for existing user
        self.users.reset_password(request_id=request_id_1, password='mypwd')
        # After resetting the password the previous API key for the user is
        # invalid
        with self.assertRaises(err.UnauthenticatedAccessError):
            self.users.authenticate(api_key)
        api_key = self.users.login('first.user@me.com', 'mypwd')
        user = self.users.authenticate(api_key)
        self.assertEqual(user.email, 'first.user@me.com')
        # An error is raised when (i) trying to use a request for an unknown
        # user, (ii) a previously completed reset request, or (iii) an unknown
        # request identifier to reset a user password
        with self.assertRaises(err.UnknownResourceError):
            self.users.reset_password(request_id=request_id_1, password='mypwd')
        with self.assertRaises(err.UnknownResourceError):
            self.users.reset_password(request_id=request_id_2, password='mypwd')
        with self.assertRaises(err.UnknownResourceError):
            self.users.reset_password(request_id='unknown', password='mypwd')

    def test_reset_request_timeout(self):
        """Test resetting a user password using a request identifier that has
        timed out.
        """
        self.users.register_user('first.user@me.com', 'pwd1')
        api_key = self.users.login('first.user@me.com', 'pwd1')
        user = self.users.authenticate(api_key)
        self.assertEqual(user.email, 'first.user@me.com')
        # Hack: Manipulate the login_timeout value to similate timeout
        self.users.login_timeout = 1
        # Request reset and sleep for two seconds. This should allow the request
        # to timeout
        request_id = self.users.request_password_reset('first.user@me.com')
        time.sleep(2)
        with self.assertRaises(err.UnknownResourceError):
            self.users.reset_password(request_id=request_id, password='mypwd')


if __name__ == '__main__':
    import unittest
    unittest.main()
