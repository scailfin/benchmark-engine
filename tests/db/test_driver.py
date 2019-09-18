# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""Test functionality of the database driver."""

import os
import pytest

from benchengine.config import ENV_DATABASE
from benchengine.db import DatabaseDriver

import benchengine.config as config


class TestDatabaseDriver(object):
    """Test functionality of the database driver to establish database
    connections.
    """
    def test_connect_invalid_string(self):
        """Ensure that an exception is thrown if an invalid connections tring is
        provided to the driver.
        """
        with pytest.raises(ValueError):
            DatabaseDriver.connect('not a valid connect string')

    def test_connect_sqlite(self, tmpdir):
        """Test connecting to SQLite3 database."""
        # Set the connect string
        filename = '{}/my.db'.format(str(tmpdir))
        connect_string = 'sqlite:{}'.format(filename)
        # Connect by passing the connect sting (clear environment first)
        if ENV_DATABASE in os.environ:
            del os.environ[ENV_DATABASE]
        con = DatabaseDriver.connect(connect_string=connect_string)
        self.validate_database(con, filename)
        # Make sure that database file has been deleted
        assert not os.path.isfile(filename)
        # Repeat with the environment variable set
        os.environ[ENV_DATABASE] = connect_string
        con.close()
        con = DatabaseDriver.connect()
        self.validate_database(con, filename)
        connect_info = DatabaseDriver.info()
        assert connect_info.startswith('sqlite3 @ ')
        os.environ[ENV_DATABASE] = 'unknown'
        with pytest.raises(ValueError):
            DatabaseDriver.info()
        con.close()

    def test_init_db(self, tmpdir):
        """Test initializing the database using the default database."""
        if ENV_DATABASE in os.environ:
            del os.environ[ENV_DATABASE]
        filename = '{}/my.db'.format(str(tmpdir))
        connect_string = 'sqlite:{}'.format(filename)
        os.environ[ENV_DATABASE] = connect_string
        # Call the init_db method to create all database tables
        DatabaseDriver.init_db()
        # Connect to the database and ensure we can run a simple query without
        # and SQL error
        con = DatabaseDriver.connect()
        assert con.execute('SELECT * from team').fetchone() is None
        con.close()

    def validate_database(self, con, filename):
        """Validate that the connection is valid and the database file exists.
        Clean-up afterwards.
        """
        # Ensure that we have avalid connection
        con.execute('CREATE TABLE t(id INTEGER NOT NULL)')
        con.close()
        # Make sure that the default database file was created (and clean up)
        assert os.path.isfile(filename)
        os.remove(filename)
