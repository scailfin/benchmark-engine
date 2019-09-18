# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""The classes in this module are used to register user and manage password
reset requests.
"""

import dateutil.parser
import datetime as dt

from passlib.hash import pbkdf2_sha256

from benchengine.user.auth import Auth
from benchengine.user.base import RegisteredUser

import benchengine.error as err
import benchtmpl.util.core as util


class UserManager(Auth):
    """The user manager registers new users and handles requests to reset a
    user password.
    """
    def __init__(self, con):
        """Initialize the database connection object.

        Parameters
        ----------
        con: DB-API 2.0 database connection
            Connection to underlying database
        """
        super(UserManager, self).__init__(con)

    def activate_user(self, user_id):
        """Activate the user with the given identifier.

        Parameters
        ----------
        user_id: string
            Unique user identifier
        """
        sql = 'UPDATE registered_user SET active = 1 WHERE id = ?'
        self.con.execute(sql, (user_id,))
        self.con.commit()

    def get_user(self, username):
        """Get handle for user with the given user name.

        Parameters
        ----------
        username: string
            Unique user name

        Returns
        -------
        benchengine.user.base.RegisteredUser

        Raises
        ------
        benchengine.error.UnknownUserError
        """
        # Get information for user with the given user name. If the user is
        # unknown an error is raised.
        sql = 'SELECT id, email FROM registered_user WHERE email = ?'
        user = self.con.execute(sql, (username,)).fetchone()
        if user is None:
            raise err.UnknownUserError(username)
        return RegisteredUser(
            identifier=user['id'],
            email=user['email']
        )

    def list_user(self):
        """Get a list of all registered users.

        Returns
        -------
        list(benchengine.user.base.RegisteredUser)
        """
        sql = 'SELECT u.id as id, u.email as email, k.expires as expires '
        sql += 'FROM registered_user u LEFT OUTER JOIN user_key k '
        sql += 'ON (u.id = k.user_id) WHERE u.active = 1'
        users = list()
        for user in self.con.execute(sql):
            expires = user['expires']
            if not expires is None:
                expires = dateutil.parser.parse(expires)
            else:
                expires = None
            users.append(
                RegisteredUser(
                    identifier=user['id'],
                    email=user['email'],
                    valid_until=expires)
                )
        return users

    def register_user(self, username, password, verify=False):
        """Create a new user for the given username. Raises an error if a user
        with that name already is registered. Returns the internal unique
        identifier for the created user.

        The verify flag allows to create active or inactive users. An inactive
        user cannot login until they have been activated. This option is
        intended for scenarios where the user receives an email after they
        register that contains a verification/activation link to ensure that
        the provided email address is valid.

        Parameters
        ----------
        username: string
            User email address that is used as the username
        password: string
            Password used to authenticate the user
        verify: bool, optional
            Determines whether the created user is active or inactive

        Returns
        -------
        string

        Raises
        ------
        benchengine.error.ConstraintViolationError
        benchengine.error.DuplicateUserError
        """
        # Ensure that the username does not contain more than 255 characters
        # and that the password has at least one (non-space) character
        if len(username) > 255:
            raise err.ConstraintViolationError('username too long')
        self.validate_password(password)
        # If a user with the given username already exists raise an error
        sql = 'SELECT id FROM registered_user WHERE email = ?'
        if not self.con.execute(sql, (username,)).fetchone() is None:
            raise err.DuplicateUserError(username)
        # Insert new user into database after creating an unique user identifier
        # and the password hash.
        user_id = util.get_unique_identifier()
        hash = pbkdf2_sha256.hash(password.strip())
        active = 0 if verify else 1
        sql = 'INSERT INTO registered_user(id, email, secret, active) '
        sql += 'VALUES(?, ?, ?, ?)'
        self.con.execute(sql, (user_id, username, hash, active))
        self.con.commit()
        # Log user in after successful registration and return API key
        return user_id

    def request_password_reset(self, username):
        """Request a passowrd reset for the user with a given name. Returns
        the request identifier that is required as an argument to reset the
        password. The result is always going to be the identifier string
        independently of whether a user with the given username is registered or
        not.

        Invalidates all previous password reset requests for the user.

        Parameters
        ----------
        username: string
            User email that was provided at registration

        Returns
        -------
        string
        """
        request_id = util.get_unique_identifier()
        # Get user identifier that is associated with the username
        sql = 'SELECT id FROM registered_user WHERE email = ? AND active = 1'
        user = self.con.execute(sql, (username,)).fetchone()
        if user is None:
            return request_id
        user_id = user['id']
        # Delete any existing password reset request for the given user
        sql = 'DELETE FROM password_request WHERE user_id = ?'
        self.con.execute(sql, (user_id,))
        # Insert new password reset request. The expiry date for the request is
        # calculated using the login timeout
        expires = dt.datetime.now() + dt.timedelta(seconds=self.login_timeout)
        sql = 'INSERT INTO password_request(user_id, request_id, expires) VALUES(?, ?, ?)'
        self.con.execute(sql, (user_id, request_id, expires.isoformat()))
        self.con.commit()
        return request_id

    def reset_password(self, request_id, password):
        """Reset the password for the user that made the given password reset
        request. Raises an error if no such request exists or if the request
        has timed out.

        Parameters
        ----------
        Raises
        ------
        benchengine.error.ConstraintViolationError
        benchengine.error.UnknownResourceError
        """
        # Ensure that the given password is valid
        self.validate_password(password)
        # Get the user and expiry date for the request. Raise error if the
        # request is unknown or has expired.
        sql = 'SELECT user_id, expires FROM password_request WHERE request_id = ?'
        req = self.con.execute(sql, (request_id,)).fetchone()
        if req is None:
            raise err.UnknownResourceError(request_id, type='reset request')
        expires = dateutil.parser.parse(req['expires'])
        if expires < dt.datetime.now():
            raise err.UnknownResourceError(request_id, type='reset request')
        # Update password hash for the identifier user
        user_id = req['user_id']
        hash = pbkdf2_sha256.hash(password.strip())
        sql = 'UPDATE registered_user SET secret = ? WHERE id = ?'
        self.con.execute(sql, (hash, user_id))
        # Invalidate all current API keys for the user after password is updated
        sql = 'DELETE FROM user_key WHERE user_id = ?'
        self.con.execute(sql, (user_id,))
         # Remove the request
        sql = 'DELETE FROM password_request WHERE request_id = ?'
        self.con.execute(sql, (request_id,))
        self.con.commit()

    def validate_password(self, password):
        """Validate a given password. Raises constraint violation error if an
        invalid password is given.

        Currently, the only constraint for passwords is that they are not empty

        Parameters
        ----------
        password: string
            User password for authentication

        Raises
        ------
        benchengine.error.ConstraintViolationError
        """
        # Raise error if password is invalid
        if password is None or len(password.strip()) == 0:
            raise err.ConstraintViolationError('empty password')
