"""Test API methods for user resources and login/logout."""

import os
import shutil

from unittest import TestCase

from benchengine.api.base import EngineApi
from benchengine.db import DatabaseDriver

import benchengine.api.serialize.hateoas as hateoas
import benchengine.api.serialize.labels as labels
import benchengine.config as config
import benchengine.error as err


TMP_DIR = 'tests/files/.tmp'
CONNECT = 'sqlite:{}/test.db'.format(TMP_DIR)


class TestUserApi(TestCase):
    """Test API methods that access and manipulate users."""
    def setUp(self):
        """Create empty directory."""
        if os.path.isdir(TMP_DIR):
            shutil.rmtree(TMP_DIR)
        os.mkdir(TMP_DIR)
        os.environ[config.ENV_DATABASE] = CONNECT
        DatabaseDriver.init_db()
        os.environ[config.ENV_BASEDIR] = os.path.join(TMP_DIR)
        self.engine = EngineApi()

    def tearDown(self):
        """Remove temporary directory."""
        self.engine.close()
        if os.path.isdir(TMP_DIR):
            shutil.rmtree(TMP_DIR)

    def test_login_user(self):
        """Test logging in and logging out."""
        users = self.engine.users()
        users.register(username='myuser', password='mypwd')
        response = users.login(username='myuser', password='mypwd')
        self.assertEqual(len(response), 2)
        self.assertTrue(labels.ACCESS_TOKEN in response)
        self.assertTrue(labels.LINKS in response)
        links = hateoas.deserialize(response[labels.LINKS])
        self.assertEqual(len(links), 2)
        self.assertTrue(hateoas.SERVICE in links)
        self.assertTrue(hateoas.user(hateoas.LOGOUT) in links)
        response = users.logout(response[labels.ACCESS_TOKEN])
        self.assertEqual(len(response), 2)
        self.assertTrue(labels.STATE in response)
        self.assertTrue(labels.LINKS in response)
        links = hateoas.deserialize(response[labels.LINKS])
        self.assertEqual(len(links), 1)
        self.assertTrue(hateoas.user(hateoas.LOGIN) in links)
        response = users.logout('unknown')
        self.assertEqual(len(response), 2)
        self.assertTrue(labels.STATE in response)
        self.assertTrue(labels.LINKS in response)
        links = hateoas.deserialize(response[labels.LINKS])
        self.assertEqual(len(links), 1)
        self.assertTrue(hateoas.user(hateoas.LOGIN) in links)

    def test_register_user(self):
        """Test new user registration via API."""
        users = self.engine.users()
        response = users.register(username='myuser', password='mypwd')
        self.assertEqual(len(response), 3)
        self.assertTrue(labels.ID in response)
        self.assertTrue(labels.USERNAME in response)
        self.assertTrue(labels.LINKS in response)
        links = hateoas.deserialize(response[labels.LINKS])
        self.assertEqual(len(links), 2)
        self.assertTrue(hateoas.user(hateoas.LOGIN) in links)
        self.assertTrue(hateoas.user(hateoas.LOGOUT) in links)
        # Errors when registering users with existing or invalid user names
        with self.assertRaises(err.DuplicateUserError):
            users.register(username='myuser', password='mypwd')
        with self.assertRaises(err.ConstraintViolationError):
            users.register(username='a'*256, password='mypwd')

    def test_whoami(self):
        """Test retrieving information for current user."""
        users = self.engine.users()
        users.register(username='myuser', password='mypwd')
        response = users.login(username='myuser', password='mypwd')
        response = users.whoami(response[labels.ACCESS_TOKEN])
        self.assertEqual(len(response), 3)
        self.assertTrue(labels.ID in response)
        self.assertTrue(labels.USERNAME in response)
        self.assertTrue(labels.LINKS in response)

    def test_whoarethey(self):
        """Test retrieving information for current user."""
        users = self.engine.users()
        response = users.register(username='myuser', password='mypwd')
        user_id = response[labels.ID]
        response = users.whoarethey('myuser')
        self.assertEqual(len(response), 3)
        self.assertTrue(labels.ID in response)
        self.assertTrue(labels.USERNAME in response)
        self.assertTrue(labels.LINKS in response)
        self.assertEqual(response[labels.ID], user_id)
        self.assertEqual(response[labels.USERNAME], 'myuser')


if __name__ == '__main__':
    import unittest
    unittest.main()
