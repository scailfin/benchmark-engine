"""Test functionality of helper methods in the config module."""

import os

from unittest import TestCase

import benchengine.config as config


class TestConfigHelpers(TestCase):
    """Test helper methods that get configuration parameters from environment
    variables.
    """
    def test_login_timeout(self):
        """Test getting the login timeout."""
        # Make sure an integer value is returned
        os.environ[config.ENV_LOGIN_TIMEOUT] = '10'
        self.assertEqual(config.get_login_timeout(), 10)
        # If variable is not set the default is returned
        del os.environ[config.ENV_LOGIN_TIMEOUT]
        self.assertEqual(config.get_login_timeout(), config.DEFAULT_LOGIN_TIMEOUT)
        # If the variable is not an integer the default is returned
        os.environ[config.ENV_LOGIN_TIMEOUT] = 'this is not a number'
        self.assertEqual(config.get_login_timeout(), config.DEFAULT_LOGIN_TIMEOUT)

    def test_schema_file(self):
        """Test getting the databse schema file path."""
        # The system does not check if the file exists
        os.environ[config.ENV_SCHEMA_FILE] = 'ABC'
        self.assertEqual(config.get_schema_file(), 'ABC')
        # If variable is not set the default is returned
        del os.environ[config.ENV_SCHEMA_FILE]
        self.assertEqual(
            os.path.basename(config.get_schema_file()),
            os.path.basename(config.DEFAULT_SCHEMA_FILE)
        )


if __name__ == '__main__':
    import unittest
    unittest.main()
