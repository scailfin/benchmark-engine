# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""Defines environment variables and default values that are used to control
the configuration of the authentication modules.

The name of methods that provide access to values from environment variables
are in upper case to emphasize that they access configuration values that are
expected to remain constant throughout the lifespan of a running application.
"""

import robapi.config.base as config


"""Names of environment variables that are used to configure the authentication
module.
"""
# Timeperiod for which an API key is valid
ROB_AUTH_LOGINTTL = 'ROB_AUTHTTL'

"""Default values for environment variables."""
DEFAULT_LOGINTTL = 4 * 60 * 60

# -- Public helper methods to access configuration values ----------------------

def AUTH_LOGINTTL(default_value=None, raise_error=False):
    """Get the connect string for the database from the respective environment
    variable 'ROB_AUTH_LOGINTTL'. Raises a MissingConfigurationError if the
    raise_error flag is True and 'ROB_AUTH_LOGINTTL' is not set. If the
    raise_error flag is False and 'ROB_AUTH_LOGINTTL' is not set the default
    value is returned.

    Parameters
    ----------
    default_value: string, optional
        Default value if 'ROB_AUTH_LOGINTTL' is not set and raise_error flag is
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
        name=ROB_AUTH_LOGINTTL,
        default_value=default_value,
        raise_error=raise_error
    )
    # If the environment variable is not set and no default value was given
    # return the defined default value
    if val is None:
        val = DEFAULT_LOGINTTL
    return val
