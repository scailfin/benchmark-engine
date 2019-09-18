# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""Defines environment variables and their default values that are used to
control the configurtion of the API. Also provides methods to access the
configuration values.
"""

import robapi.config.base as config


"""Names of environment variables that are used to configure the authentication
module.
"""
# Timeperiod for which an API key is valid
ROB_API_URL = 'ROB_APIURL'
# Base directory to store uploaded files and submission results
ENV_BASEDIR = 'BENCHENGINE_BASEDIR'
# Connect string for the underlying database
ENV_DATABASE = 'BENCHENGINE_DATABASE'
# Timeperiod for which an API key is valid
ENV_LOGIN_TIMEOUT = 'BENCHENGINE_LOGIN_TIMEOUT'
# Path to file containing the database schema (for db_init)
ENV_SCHEMA_FILE = 'BENCHENGINE_SCHEMA_FILE'
# Name of the API instance
ENV_SERVICE_NAME = 'BENCHENGINE_SERVICE_NAME'


"""Default values for environment variables."""
DEFAULT_URL = 'http://localhost:5000/rob/api/v1'
DEFAULT_SERVICE_NAME = 'Reproducible Benchmarks for Data Analysis (Development API)'


# -- Public helper methods to access configuration values ----------------------

def API_URL(default_value=None, raise_error=False):
    """Get the base URL for the API from the respective environment variable
    'ROB_API_URL'. Raises a MissingConfigurationError if thr raise_error flag
    is True and 'ROB_API_URL' is not set. If the raise_error flag is False and
    'ROB_API_URL' is not set the default value is returned.

    Parameters
    ----------
    default_value: string, optional
        Default value if 'ROB_API_URL' is not set and raise_error flag is
        False
    raise_error: bool, optional
        Flag indicating whether an error is raised if the environment variable
        is not set (i.e., None or and empty string '')

    Returns
    -------
    string

    Raises
    ------
    robapi.error.MissingConfigurationError
    """
    val = config.get_variable(
        name=ROB_API_URL,
        default_value=default_value,
        raise_error=raise_error
    )
    # If the environment variable is not set and no default value was given
    # return the defined default value
    if val is None:
        val = DEFAULT_URL
    return val
