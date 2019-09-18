# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""Handles for benchmarks. The benachmark handle contains all the information
about benchmarks that is maintained in addition to the underlying workflow
template. Each benchmark has a unique identifier (inherited from the template),
a descriptive name, a short description, and an optional set of instructions.
"""

import robapi.error as err


"""Each benchmark defines an individual schema for the results of benchmark
runs. The results are stored in separate result tables for each benchmark. The
tables are created in the underlying database when the benchmark is added to
the repository. The name of the result table is the identifier of the benchmark
with a constant prefix. The prefix is necessary since benchmark identifier may
start with a digit instaed of a letter which would lead to invalid table names.
"""
def RESULT_TABLE(identifier):
    """Get default result table name for the benchmark with the given
    identifier. It is assumed that the identifier is a UUID that only contains
    letters and digits and no white space or special characters.

    Parameters
    ----------
    identifier: string
        Unique benchmark identifier

    Returns
    -------
    string
    """
    return 'res_{}'.format(identifier)


def validate_name(name, con=None, sql=None):
    """Validate the given name. Raises an error if the given name violates the
    current constraints for names. The constraints are:

    - no empty or missing names
    - names can be at most 512 characters long
    - names are unique (if sql statement is given)

    To test name uniqueness a database connection and SQL statement is expected.
    The SQL statement should be parameterized with the name as the only
    parameter.

    Raises
    ------
    robapi.error.ConstraintViolationError
    """
    if name is None:
        raise err.ConstraintViolationError('missing name')
    name = name.strip()
    if name == '' or len(name) > 512:
        raise err.ConstraintViolationError('invalid name')
    # Validate uniqueness if a database connection and SQL statement are given
    if con is None or sql is None:
        return
    if not con.execute(sql, (name,)).fetchone() is None:
        raise err.ConstraintViolationError('name \'{}\' exists'.format(name))
