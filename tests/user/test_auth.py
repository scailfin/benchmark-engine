"""Test functionality to authenticate a user."""

import os
import shutil
import time

from passlib.hash import pbkdf2_sha256
from unittest import TestCase

from benchengine.db import DatabaseDriver
from benchengine.user.auth import Auth

import benchengine.error as err
import benchtmpl.util.core as util


TMP_DIR = './tests/files/.tmp'
CONNECT = 'sqlite:{}/auth.db'.format(TMP_DIR)

USER_1 = util.get_unique_identifier()
USER_2 = util.get_unique_identifier()
USER_3 = util.get_unique_identifier()


class TestUserAuthentication(TestCase):
    """Test login and logout functionality."""
    def setUp(self):
        if os.path.isdir(TMP_DIR):
            shutil.rmtree(TMP_DIR)
        os.makedirs(TMP_DIR)
        """Create a fresh database and insert two default users."""
        DatabaseDriver.init_db(connect_string=CONNECT)
        con = DatabaseDriver.connect(connect_string=CONNECT)
        sql = 'INSERT INTO registered_user(id, email, secret, active) VALUES(?, ?, ?, ?)'
        con.execute(sql, (USER_1, USER_1, pbkdf2_sha256.hash(USER_1), 1))
        con.execute(sql, (USER_2, USER_2, pbkdf2_sha256.hash(USER_2), 1))
        con.execute(sql, (USER_3, USER_3, pbkdf2_sha256.hash(USER_3), 0))
        con.commit()
        self.con = con

    def tearDown(self):
        """Close connection and remove database file."""
        self.con.close()
        if os.path.isdir(TMP_DIR):
            shutil.rmtree(TMP_DIR)

    def test_authenticate(self):
        """Test user login and logout."""
        auth = Auth(self.con)
        # Login user 1 and 2
        api_key_1 = auth.login(USER_1, USER_1)
        api_key_2 = auth.login(USER_2, USER_2)
        # Authenticate user 1
        user = auth.authenticate(api_key_1)
        self.assertEqual(user.identifier, USER_1)
        self.assertEqual(user.email, USER_1)
        # Authenticate user 2
        user = auth.authenticate(api_key_2)
        self.assertEqual(user.identifier, USER_2)
        self.assertEqual(user.email, USER_2)
        # Logout user 1
        auth.logout(api_key_1)
        # Authenticating user 1 will raise exception
        with self.assertRaises(err.UnauthenticatedAccessError):
            auth.authenticate(api_key_1)
        # User 2 can still authenticate
        user = auth.authenticate(api_key_2)
        self.assertEqual(user.identifier, USER_2)
        self.assertEqual(user.email, USER_2)
        # Re-login user 1 and authenticate
        api_key_1 = auth.login(USER_1, USER_1)
        user = auth.authenticate(api_key_1)
        self.assertEqual(user.identifier, USER_1)
        self.assertEqual(user.email, USER_1)
        # If a user logs in again all previous keys become invalid
        api_key_3 = auth.login(USER_1, USER_1)
        with self.assertRaises(err.UnauthenticatedAccessError):
            auth.authenticate(api_key_1)
        # Attempt to authenticate unknown user raises error
        with self.assertRaises(err.UnknownUserError):
            auth.login('unknown', USER_1)
        # Attempt to authenticate wilt invalid password will raises error
        with self.assertRaises(err.UnknownUserError):
            auth.login(USER_1, USER_2)
        # Attempting to login for inactive user raises error
        with self.assertRaises(err.UnknownUserError):
            auth.login(USER_3, USER_3)

    def test_login_timeout(self):
        """Test login after key expired."""
        # Set login timeout to one second
        auth = Auth(self.con, login_timeout=1)
        api_key = auth.login(USER_1, USER_1)
        # Wait for two seconds
        time.sleep(2)
        # Authenticating after timeout will raise error
        with self.assertRaises(err.UnauthenticatedAccessError):
            auth.authenticate(api_key)

    def test_team_membership(self):
        """Ensure that the team owner and membership functions return True if
        the team does not exist.
        """
        auth = Auth(self.con)
        self.assertTrue(auth.is_team_owner(team_id='unknown', user_id=USER_1))
        self.assertTrue(auth.is_team_member(team_id='unknown', user_id=USER_1))


if __name__ == '__main__':
    import unittest
    unittest.main()
