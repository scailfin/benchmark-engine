# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""Test methods of the configuration module that access values for environment
variables that are used to configure the connection to the underlying database.
"""

import os
import pytest

import robapi.config.db as config
import robapi.error as err


class TestConfigDatabase(object):
    """Test methods that get values from environment variables that are used to
    configure the database.
    """
    def test_config_database(self):
        """Test public methods to get database configuration."""
        # Clear environment variable values if set
        if config.ROB_DB_ID in os.environ:
            del os.environ[config.ROB_DB_ID]
        if config.ROB_DB_CONNECT in os.environ:
            del os.environ[config.ROB_DB_CONNECT]
        assert config.DB_IDENTIFIER() is None
        assert config.DB_CONNECT() is None
        assert config.DB_IDENTIFIER(default_value='ABC') == 'ABC'
        assert config.DB_CONNECT(default_value='XYZ') == 'XYZ'
        with pytest.raises(err.MissingConfigurationError):
            assert config.DB_IDENTIFIER(raise_error=True)
        with pytest.raises(err.MissingConfigurationError):
            assert config.DB_CONNECT(raise_error=True)
        os.environ[config.ROB_DB_ID] = 'ABC'
        os.environ[config.ROB_DB_CONNECT] = 'XYZ'
        assert config.DB_IDENTIFIER(default_value='XYZ') == 'ABC'
        assert config.DB_CONNECT(default_value='ABC') == 'XYZ'
