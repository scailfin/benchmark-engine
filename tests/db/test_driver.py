"""Test functionality of the database driver."""

import os
import shutil

from unittest import TestCase

from benchengine.config import ENV_DATABASE
from benchengine.db import DatabaseDriver

import benchengine.config as config


DEFAULT_DATABASE_FILE = './benchengine.db'
TMP_DIR = './tests/files/.tmp'


class TestDatabaseDriver(TestCase):
    """Test functionality of the database driver to establish database
    connections.
    """
    def setUp(self):
        """Remove default database file and temporary directory if they exist.
        """
        self.tearDown()

    def tearDown(self):
        """Remove default database file and temporary directory if they exist.
        """
        if os.path.isdir(TMP_DIR):
            shutil.rmtree(TMP_DIR)
        if os.path.isfile(DEFAULT_DATABASE_FILE):
            os.remove(DEFAULT_DATABASE_FILE)

    def test_connect_invalid_string(self):
        """Ensure that an exception is thrown if an invalid connections tring is
        provided to the driver.
        """
        with self.assertRaises(ValueError):
            DatabaseDriver.connect('not a valid connect string')

    def test_connect_sqlite(self):
        """Test connecting to SQLite3 database."""
        # Create new subfolder for database file
        if os.path.isdir(TMP_DIR):
            shutil.rmtree(TMP_DIR)
        os.makedirs(TMP_DIR)
        # Set the connect string
        filename = '{}/my.db'.format(TMP_DIR)
        connect_string = 'sqlite:{}'.format(filename)
        # Connect by passing the connect sting (clear environment first)
        if ENV_DATABASE in os.environ:
            del os.environ[ENV_DATABASE]
        con = DatabaseDriver.connect(connect_string=connect_string)
        self.validate_database(con, filename)
        # Make sure that database file has been deleted
        self.assertFalse(os.path.isfile(filename))
        # Repeat with the environment variable set
        os.environ[ENV_DATABASE] = connect_string
        con.close()
        con = DatabaseDriver.connect()
        self.validate_database(con, filename)
        connect_info = DatabaseDriver.info()
        self.assertTrue(connect_info.startswith('sqlite3 @ '))
        os.environ[ENV_DATABASE] = 'unknown'
        with self.assertRaises(ValueError):
            DatabaseDriver.info()
        # Clean-up temp directory
        shutil.rmtree(TMP_DIR)
        con.close()

    def test_init_db(self):
        """Test initializing the database using the default database."""
        if ENV_DATABASE in os.environ:
            del os.environ[ENV_DATABASE]
        filename = '{}/my.db'.format(TMP_DIR)
        connect_string = 'sqlite:{}'.format(filename)
        os.environ[ENV_DATABASE] = connect_string
        # Call the init_db method to create all database tables
        DatabaseDriver.init_db()
        # Connect to the database and ensure we can run a simple query without
        # and SQL error
        con = DatabaseDriver.connect()
        self.assertIsNone(con.execute('SELECT * from team').fetchone())
        con.close()

    def validate_database(self, con, filename):
        """Validate that the connection is valid and the database file exists.
        Clean-up afterwards.
        """
        # Ensure that we have avalid connection
        con.execute('CREATE TABLE t(id INTEGER NOT NULL)')
        con.close()
        # Make sure that the default database file was created (and clean up)
        self.assertTrue(os.path.isfile(filename))
        os.remove(filename)


if __name__ == '__main__':
    import unittest
    unittest.main()
