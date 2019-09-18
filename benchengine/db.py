# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""The database driver is a static class that is used to establish a connection
to the database management system that is being used by the application for
data management. The driver contains implementation to connect to different
database systems.
"""

import os

import benchengine.config as config
import benchtmpl.util.core as util


class DatabaseDriver(object):
    """The database driver establishes a connection to the database system that
    is used by the application. The static connect method is a wrapper around
    the different implementations used by supported database systems for
    establishing a connection.
    """
    @staticmethod
    def connect(connect_string=None):
        """Connect to the database management system. The connect string has two
        parts: dbms-identifier:connect-info

        The dbms-identifier is used to identify the database management system
        that is being used by the application. The driver currently supports two
        different systems: sqlite and postgres

        The connect-info is a database system specific string containing
        information that is used by tje respective system's connect method to
        establish the connection.

        Parameters
        ----------
        connect_string: string
            Specify the database system and the information required by the
            system to establish a connection

        Returns
        -------
        DB-API 2.0 database connection

        Raises
        ------
        ValueError
        """
        # If the connection string is not given we try to get the value from the
        # application configuration
        if connect_string is None:
            connect_string = config.get_database()
        if connect_string.startswith('sqlite:'):
            import sqlite3
            f_name = connect_string[7:]
            # Ensure that the directory for the database file exists
            util.create_dir(os.path.dirname(f_name))
            con = sqlite3.connect(f_name, detect_types=sqlite3.PARSE_DECLTYPES)
            con.row_factory = sqlite3.Row
            return con
        else:
            raise ValueError('invalid connect string \'{}\''.format(connect_string))

    @staticmethod
    def info(indent=''):
        """Get information about the database that is referenced by the
        environment variable 'benchengine_DATABASE'.

        Parameters
        ----------
        indent: string, optional
             Optional indent when printing connect string

        Returns
        -------
        string

        Raises
        ------
        ValueError
        """
        connect_string = config.get_database()
        if connect_string.startswith('sqlite:'):
            return indent + 'sqlite3 @ ' + os.path.abspath(connect_string[7:])
        else:
            raise ValueError('invalid connect string \'{}\''.format(connect_string))

    @staticmethod
    def init_db(connect_string=None, schema_file=None):
        """Initialize the database by executing the schema.sql script to create
        a clean initial version of the database tables and views.

        Parameters
        ----------
        connect_string: string
            Specify the database system and the information required by the
            system to establish a connection
        schema_file: string, optional
            Path to the file containing the statements to create database tables

        Raises
        ------
        ValueError
        """
        # If the connection string is not given we try to get the value from the
        # application configuration
        if connect_string is None:
            connect_string = config.get_database()
        if schema_file is None:
            schema_file = config.get_schema_file()
        con = DatabaseDriver.connect(connect_string=connect_string)
        with open(schema_file) as f:
            if connect_string.startswith('sqlite:'):
                con.executescript(f.read())
