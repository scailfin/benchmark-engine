# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""Test functionality of helper methods in the config module."""

import os

import benchengine.config as config


class TestConfigHelpers(object):
    """Test helper methods that get configuration parameters from environment
    variables.
    """
    def test_login_timeout(self):
        """Test getting the login timeout."""
        # Make sure an integer value is returned
        os.environ[config.ENV_LOGIN_TIMEOUT] = '10'
        assert config.get_login_timeout() == 10
        # If variable is not set the default is returned
        del os.environ[config.ENV_LOGIN_TIMEOUT]
        assert config.get_login_timeout() == config.DEFAULT_LOGIN_TIMEOUT
        # If the variable is not an integer the default is returned
        os.environ[config.ENV_LOGIN_TIMEOUT] = 'this is not a number'
        assert config.get_login_timeout() == config.DEFAULT_LOGIN_TIMEOUT

    def test_schema_file(self):
        """Test getting the databse schema file path."""
        # The system does not check if the file exists
        os.environ[config.ENV_SCHEMA_FILE] = 'ABC'
        assert config.get_schema_file() == 'ABC'
        # If variable is not set the default is returned
        del os.environ[config.ENV_SCHEMA_FILE]
        fname = os.path.basename(config.get_schema_file())
        defname = os.path.basename(config.DEFAULT_SCHEMA_FILE)
        assert fname == defname
