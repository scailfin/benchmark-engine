"""Defines environment variables and their default values that are used to
control the configurtion of the competition engine. Provides methods to access
the configuration values.
"""

import os


"""Names of environment variables that are used to configure different parts of
the application.
"""
# Base Url for the engine API
ENV_APIURL = 'BENCHENGINE_API_BASEURL'
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
DEFAULT_APIURL = 'http://localhost:5000/benchmark-engine/api/v1'
DEFAULT_BASEDIR = '.rob'
# By default an API key is valid for 4 hours
DEFAULT_LOGIN_TIMEOUT = 4 * 60 * 60
# Path to the default schema file. CAUTION! At this point it is assumed that the
# schema file is in a sub-tree that is rooted at a directory (i.e., 'resources')
# that is a sibling of the benchengine package directory.
DEFAULT_SCHEMA_FILE = 'resources/db/schema.sql'
DEFAULT_SERVICE_NAME = 'Reproducible Benchmarks for Data Analysis (Development API)'

"""Default sub-folders of the base directory to maintain workflow templates,
workflow run results, and uploaded files.
"""
TEMPLATE_DIR = 'templates'
UPLOAD_DIR = 'files'


# ------------------------------------------------------------------------------
# Helper methofd to access configuration values
# ------------------------------------------------------------------------------

def get_apiurl():
    """Get base Url for API resources. If the environment variable
    'benchengine_API_BASEURL' is not set or empty the result will be None.

    Returns
    -------
    string
    """
    return os.environ.get(ENV_APIURL, DEFAULT_APIURL)


def get_base_dir():
    """Get base directory for uploaded and downloaded files from the environment
    variable 'benchengine_BASEDIR'. If the variable is not set the default
    value is returned.

    Returns
    -------
    string
    """
    return os.environ.get(ENV_BASEDIR, DEFAULT_BASEDIR)


def get_database():
    """Get database connections tring from the application configuration.

    Returns
    -------
    string
    """
    return os.environ.get(
        ENV_DATABASE,
        'sqlite:{}'.format(os.path.join(os.path.abspath(get_base_dir()), 'engine.db'))
    )


def get_login_timeout():
    """Get the period (in seconds) for which an API key is valid after it has
    been assigned to a user at login.

    If the value of the respective environment variable benchengine_LOGIN_TIMEOUT
    is not set or cannot be converted to an integer the default value is
    returned.

    Returns
    -------
    int
    """
    login_timeout = os.environ.get(ENV_LOGIN_TIMEOUT, DEFAULT_LOGIN_TIMEOUT)
    try:
        return int(login_timeout)
    except ValueError:
        return DEFAULT_LOGIN_TIMEOUT


def get_schema_file():
    """Get path to file that contains the database schema.

    Returns
    -------
    string
    """
    # The schema file is included in the benchengine package resource
    # directory. Use __path__ to get the directory of the package. The file
    # is expected to be in a directory that is a sibling to the package
    # directory.
    import benchengine
    schema_file = os.path.join(benchengine.__path__[0], '..', DEFAULT_SCHEMA_FILE)
    return os.environ.get(ENV_SCHEMA_FILE, schema_file)


def get_service_name():
    """Get the descriptive name for an API instance.

    Returns
    -------
    string
    """
    return os.environ.get(ENV_SERVICE_NAME, DEFAULT_SERVICE_NAME)


def get_template_dir():
    """Get directory that is used by the template repository to maintain the
    workflow templates for benchmarks. This directory is a sub-folder of the
    base directory that is referenced by the environment variable
    'benchengine_BASEDIR'.

    Returns
    -------
    string
    """
    return os.path.join(get_base_dir(), TEMPLATE_DIR)


def get_upload_dir():
    """Get directory that is used by the API to maintain files that are uploaded
    by users as input to benchmark runs. This directory is a sub-folder of the
    base directory that is referenced by the environment variable
    'benchengine_BASEDIR'.

    Returns
    -------
    string
    """
    return os.path.join(get_base_dir(), UPLOAD_DIR)
