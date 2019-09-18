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


class EngineError(Exception):
    """Base exception indicating that a component of the benchmark engine
    encountered an error situation.
    """
    def __init__(self, message):
        """Initialize error message.

        Parameters
        ----------
        message : string
            Error message
        """
        Exception.__init__(self)
        self.message = message


class ConstraintViolationError(EngineError):
    """Exception raised when an (implicit) constraint is violated by requested
    operation. Example constraints are that (i) team and user names have to be
    unique, (ii) names can be at most 255 characters long, (iii) team owners
    cannot be removed as team members, etc.
    """
    def __init__(self, message):
        """Initialize error message.

        Parameters
        ----------
        message : string
            Error message
        """
        super(ConstraintViolationError, self).__init__(message=message)


class DuplicateUserError(EngineError):
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


class UnauthenticatedAccessError(EngineError):
    """This exception is raised if an unauthenticated user attempts to access
    or manipulate application resources.
    """
    def __init__(self):
        """Initialize the default error message."""
        super(UnauthenticatedAccessError, self).__init__(
            message='not logged in'
        )


class UnauthorizedAccessError(EngineError):
    """This exception is raised if an authenticated user attempts to access
    or manipulate application resources that they have not authorization to.
    """
    def __init__(self):
        """Initialize the default error message."""
        super(UnauthorizedAccessError, self).__init__(
            message='not authorized'
        )


class UnknownResourceError(EngineError):
    """Exception indicating that a requested resource is unknown."""
    def __init__(self, identifier, type='resource'):
        """Initialize error message.

        Parameters
        ----------
        identifier : string
            Unique resource identifier
        """
        super(UnknownResourceError, self).__init__(
            message='unknown {} \'{}\''.format(type, identifier)
        )


class UnknownBenchmarkError(UnknownResourceError):
    """Exception indicating that a given benchmark identifier is unknown."""
    def __init__(self, benchmark_id):
        """Initialize error message.

        Parameters
        ----------
        benchmark_id : string
            Unique benchmark identifier
        """
        super(UnknownBenchmarkError, self).__init__(
            identifier=benchmark_id,
            type='benchmark'
        )


class UnknownFileError(UnknownResourceError):
    """Exception indicating that a given file handle references an unknown
    file.
    """
    def __init__(self, file_id):
        """Initialize error message.

        Parameters
        ----------
        file_id : string
            Unique file identifier
        """
        super(UnknownFileError, self).__init__(identifier=file_id, type='file')


class UnknownTeamError(UnknownResourceError):
    """Exception indicating that a given team identifier is unknown."""
    def __init__(self, team_id):
        """Initialize error message.

        Parameters
        ----------
        team_id : string
            Unique team identifier
        """
        super(UnknownTeamError, self).__init__(identifier=team_id, type='team')


class UnknownUserError(UnknownResourceError):
    """Exception indicating that a given user identifier is unknown."""
    def __init__(self, user_id):
        """Initialize error message.

        Parameters
        ----------
        user_id : string
            Unique user identifier
        """
        super(UnknownUserError, self).__init__(identifier=user_id, type='user')
