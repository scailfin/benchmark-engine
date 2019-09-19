# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""The authentication and authorization module contains methods to authorize
users that have logged in to the system as well as methods to authorize that a
given user can execute a requested action.
"""

import datetime as dt
import dateutil.parser

from abc import abstractmethod

from robapi.model.user import UserHandle

import robapi.error as err


"""Unique identifier for API resources that are controlled by the authorization
module.
"""
FILE = 'file'
SUBMISSION = 'submission'


class Auth(object):
    """Base class for authentication and authorization methods. Different
    authorization policies can implement different version of this class.
    """
    def __init__(self, con):
        """Initialize the database connection.

        Parameters
        ----------
        con: DB-API 2.0 database connection
            Connection to underlying database
        """
        self.con = con

    def authenticate(self, api_key):
        """Get the unique user identifier that is associated with the given
        API key. Raises an error if the API key is not associated with
        a valid login.

        Parameters
        ----------
        api_key: string
            Unique API access token assigned at login

        Returns
        -------
        robapi.model.user.UserHandle

        Raises
        ------
        robapi.error.UnauthenticatedAccessError
        """
        # Get information for user that that is associated with the API key
        # together with the expiry date of the key. If the API key is unknown
        # or expired raise an error.
        sql = 'SELECT u.user_id, u.name, k.expires as expires '
        sql += 'FROM api_user u, user_key k '
        sql += 'WHERE u.user_id = k.user_id AND u.active = 1 AND k.api_key = ?'
        user = self.con.execute(sql, (api_key,)).fetchone()
        if user is None:
            raise err.UnauthenticatedAccessError()
        expires = dateutil.parser.parse(user['expires'])
        if expires < dt.datetime.now():
            raise err.UnauthenticatedAccessError()
        return UserHandle(
            identifier=user['user_id'],
            name=user['name'],
            api_key=api_key
        )

    @abstractmethod
    def can_delete(self, resource_type, resource_id, user):
        """Verify that the user can delete the given resource.

        Parameters
        ----------
        resource_type: string
            Unique resource type identifier
        resource_id: string
            Unique resource identifier
        user: robapi.model.user.UserHandle
            Handle for user that is accessing the resource

        Returns
        -------
        bool
        """
        raise NotImplementedError()

    @abstractmethod
    def can_modify(self, resource_type, resource_id, user):
        """Verify that the user can modify the given resource.

        Parameters
        ----------
        resource_type: string
            Unique resource type identifier
        resource_id: string
            Unique resource identifier
        user: robapi.model.user.UserHandle
            Handle for user that is accessing the resource

        Returns
        -------
        bool
        """
        raise NotImplementedError()

    @abstractmethod
    def has_access(self, resource_type, resource_id, user):
        """Verify that the user can access the given resource.

        Parameters
        ----------
        resource_type: string
            Unique resource type identifier
        resource_id: string
            Unique resource identifier
        user: robapi.model.user.UserHandle
            Handle for user that is accessing the resource

        Returns
        -------
        bool
        """
        raise NotImplementedError()


class DefaultAuthPolicy(Auth):
    """Default implementation for the API's authorization methods."""
    def __init__(self, con):
        """Initialize the database connection.

        Parameters
        ----------
        con: DB-API 2.0 database connection
            Connection to underlying database
        """
        super(DefaultAuthPolicy, self).__init__(con)

    def can_delete(self, resource_type, resource_id, user):
        """Verify that the user can delete the given resource. The default
        authorization policy does not distinguish between delete and modify
        operations.

        Parameters
        ----------
        resource_type: string
            Unique resource type identifier
        resource_id: string
            Unique resource identifier
        user: robapi.model.user.UserHandle
            Handle for user that is accessing the resource

        Returns
        -------
        bool
        """
        return self.can_modify(resource_type, resource_id, user)

    def can_modify(self, resource_type, resource_id, user):
        """Verify that the user can modify the given resource.

        Parameters
        ----------
        resource_type: string
            Unique resource type identifier
        resource_id: string
            Unique resource identifier
        user: robapi.model.user.UserHandle
            Handle for user that is accessing the resource

        Returns
        -------
        bool
        """
        if resource_type in [SUBMISSION, FILE]:
            return self.is_submission_member(
                submission_id=resource_id,
                user_id=user.identifier
            )
        # By default a user has access to all resources that are not controlled
        # by the policy
        return True

    def has_access(self, resource_type, resource_id, user):
        """Verify that the user can access the given resource.

        Parameters
        ----------
        resource_type: string
            Unique resource type identifier
        resource_id: string
            Unique resource identifier
        user: robapi.model.user.UserHandle
            Handle for user that is accessing the resource

        Returns
        -------
        bool
        """
        if resource_type == FILE:
            # The user has to be a member of the submission in order to access
            # or manipulate uploaded files
            return self.is_submission_member(
                submission_id=resource_id,
                user_id=user.identifier
            )
        # By default a user has access to all resources that are not controlled
        # by the policy
        return True

    def is_submission_member(self, submission_id, user_id):
        """Test if the user is member of the given submission.

        Parameters
        ----------
        submission_id: string
            Unique submission identifier
        user_id: string
            Unique user identifier
            
        Returns
        -------
        bool
        """
        sql = 'SELECT submission_id FROM submission_member '
        sql += 'WHERE submission_id = ? AND user_id = ?'
        params = (submission_id, user_id)
        return not self.con.execute(sql, params).fetchone() is None


class OpenAccessAuth(Auth):
    """Implementation for the API's authorization policy that gives full access
    to any registered user.
    """
    def __init__(self, con):
        """Initialize the database connection.

        Parameters
        ----------
        con: DB-API 2.0 database connection
            Connection to underlying database
        """
        super(OpenAccessAuth, self).__init__(con)

    def can_delete(self, resource_type, resource_id, user):
        """Everyone can delete any resource.

        Parameters
        ----------
        resource_type: string
            Unique resource type identifier
        resource_id: string
            Unique resource identifier
        user: robapi.model.user.UserHandle
            Handle for user that is accessing the resource

        Returns
        -------
        bool
        """
        return True

    def can_modify(self, resource_type, resource_id, user):
        """Everyone can modify any resource.

        Parameters
        ----------
        resource_type: string
            Unique resource type identifier
        resource_id: string
            Unique resource identifier
        user: robapi.model.user.UserHandle
            Handle for user that is accessing the resource

        Returns
        -------
        bool
        """
        return True

    def has_access(self, resource_type, resource_id, user):
        """Everyone can access any resource.

        Parameters
        ----------
        resource_type: string
            Unique resource type identifier
        resource_id: string
            Unique resource identifier
        user: robapi.model.user.UserHandle
            Handle for user that is accessing the resource

        Returns
        -------
        bool
        """
        return True
