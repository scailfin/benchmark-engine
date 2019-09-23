# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""Exceptions that are raised by the various components of the benchmark
engine.
"""

from robtmpl.error import (
    ROBError, InvalidTemplateError, UnknownObjectError, UnknownParameterError,
    UnknownRunError
)


# -- Configuration -------------------------------------------------------------

class MissingConfigurationError(ROBError):
    """Error indicating that the value for an environment variable is not set.
    """
    def __init__(self, var_name):
        """Initialize error message.

        Parameters
        ----------
        var_name: string
            Environment variable name
        """
        super(MissingConfigurationError, self).__init__(
            message='variable \'{}\' not set'.format(var_name)
        )


# -- Constraints on argument values --------------------------------------------

class ConstraintViolationError(ROBError):
    """Exception raised when an (implicit) constraint is violated by a requested
    operation. Example constraints are (i) names that are expected to be
    unique, (ii) names that cannot have more than n characters long, etc.
    """
    def __init__(self, message):
        """Initialize error message.

        Parameters
        ----------
        message : string
            Error message
        """
        super(ConstraintViolationError, self).__init__(message=message)


class DuplicateUserError(ROBError):
    """Exception indicating that a given user already exists."""
    def __init__(self, user_id):
        """Initialize error message.

        Parameters
        ----------
        user_id : string
            Unique user identifier
        """
        super(DuplicateUserError, self).__init__(
            message='duplicate user \'{}\''.format(user_id)
        )


# -- Authentication and Authorization errors -----------------------------------

class UnauthenticatedAccessError(ROBError):
    """This exception is raised if an unauthenticated user attempts to access
    or manipulate application resources.
    """
    def __init__(self):
        """Initialize the default error message."""
        super(UnauthenticatedAccessError, self).__init__(
            message='not logged in'
        )


class UnauthorizedAccessError(ROBError):
    """This exception is raised if an authenticated user attempts to access
    or manipulate application resources that they have not authorization to.
    """
    def __init__(self):
        """Initialize the default error message."""
        super(UnauthorizedAccessError, self).__init__(
            message='not authorized'
        )


# -- Unknown resources ---------------------------------------------------------

class UnknownBenchmarkError(UnknownObjectError):
    """Exception indicating that a given benchmark identifier is unknown."""
    def __init__(self, benchmark_id):
        """Initialize error message.

        Parameters
        ----------
        benchmark_id : string
            Unique benchmark identifier
        """
        super(UnknownBenchmarkError, self).__init__(
            obj_id=benchmark_id,
            type_name='benchmark'
        )


class UnknownFileError(UnknownObjectError):
    """Exception indicating that a given file identifier is unknown."""
    def __init__(self, file_id):
        """Initialize error message.

        Parameters
        ----------
        file_id : string
            Unique file identifier
        """
        super(UnknownFileError, self).__init__(
            obj_id=file_id,
            type_name='file'
        )


class UnknownSubmissionError(UnknownObjectError):
    """Exception indicating that a given submission identifier is unknown."""
    def __init__(self, user_id):
        """Initialize error message.

        Parameters
        ----------
        user_id : string
            Unique user identifier
        """
        super(UnknownSubmissionError, self).__init__(
            obj_id=user_id,
            type_name='submission'
        )


class UnknownRequestError(UnknownObjectError):
    """Exception indicating that a given password reset request identifier is
    unknown.
    """
    def __init__(self, request_id):
        """Initialize error message.

        Parameters
        ----------
        request_id : string
            Unique reset request identifier
        """
        super(UnknownRequestError, self).__init__(
            obj_id=request_id,
            type_name='request'
        )


class UnknownUserError(UnknownObjectError):
    """Exception indicating that a given user identifier is unknown."""
    def __init__(self, user_id):
        """Initialize error message.

        Parameters
        ----------
        user_id : string
            Unique user identifier
        """
        super(UnknownUserError, self).__init__(
            obj_id=user_id,
            type_name='user'
        )


# -- Workflows runs ------------------------------------------------------------

class InvalidRunStateError(ROBError):
    """Exception indicating that an attempt to modify the state of a run was
    made that is not allowed in the current run state or that would result in
    an illegal sequence of workflow states.
    """
    def __init__(self, state, resulting_state=None):
        """Initialize the error message.

        Parameters
        ----------
        state: robtmpl.workflow.state.base.WorkflowState
            Current run state
        resulting_state: robtmpl.workflow.state.base.WorkflowState, optional
            Resulting workflow state (for invalid state sequence)
        """
        if resulting_state is None:
            msg = 'invalid operation for run in state {}'.format(state)
        else:
            msg = 'illegal state transition from {} to {}'
            msg = msg.format(state, resulting_state)
        super(InvalidRunStateError, self).__init__(message=msg)
