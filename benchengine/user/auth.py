# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""The authentication and authorization module contains methods to login and
logout users, i.e., assigne and revoke API keys to users. The module Auth class
in this module also contains the required methods to authorize that a given
user can execute a requested action.
"""

import dateutil.parser
import datetime as dt

from passlib.hash import pbkdf2_sha256

from benchengine.user.base import RegisteredUser

import benchengine.config as config
import benchengine.error as err
import benchtmpl.util.core as util


class Auth(object):
    """Base class for authentication and authorization methods.

    Allows users to login and logout. A user that is logged in has an API
    associated with them. This key is valid until a timeout period has passed.

    The authentication methods allow to confirm that a user is authorized to
    perform a requested method.
    """
    def __init__(self, con, login_timeout=None):
        """Initialize the database connection and the login timeout.

        Parameters
        ----------
        con: DB-API 2.0 database connection
            Connection to underlying database
        login_timeout: int
            Specifies the period (in seconds) for which a user API key is valid
        """
        self.con = con
        if not login_timeout is None:
            self.login_timeout = login_timeout
        else:
            self.login_timeout = config.get_login_timeout()

    def authenticate(self, api_key):
        """Get the registered user that is associated with a given API key.

        Returns
        -------
        benchengine.user.base.RegisteredUser

        Raises
        ------
        benchengine.error.UnauthenticatedAccessError
        """
        # Get information for user that that is associated with the API key
        # together with the expiry date of the key. If the API key is unknown
        # or expired raise an error.
        sql = 'SELECT u.id as id, u.email as email, k.expires as expires '
        sql += 'FROM registered_user u, user_key k '
        sql += 'WHERE u.id = k.user_id AND u.active = 1 AND k.api_key = ?'
        user = self.con.execute(sql, (api_key,)).fetchone()
        if user is None:
            raise err.UnauthenticatedAccessError()
        expires = dateutil.parser.parse(user['expires'])
        if expires < dt.datetime.now():
            raise err.UnauthenticatedAccessError()
        return RegisteredUser(
            identifier=user['id'],
            email=user['email'],
            valid_until=expires
        )

    def close(self):
        """Shortcut to close the associated database connection."""
        self.con.close()

    def is_member_of_competing_team(self, user_id, team_id, comp_id):
        """Test if a user is a member of a given team and that team is
        participating in a given competition.

        Parameters
        ----------
        user_id: string
            Unique user identifier
        team_id: string
            Unique team identifier
        comp_id: string
            Unique competition identifier

        Returns
        -------
        bool
        """
        sql = 'SELECT * FROM team_member m, competition_team p '
        sql += 'WHERE m.team_id = p.team_id AND '
        sql += 'm.user_id = ? AND m.team_id = ? AND p.comp_id = ?'
        rs = self.con.execute(sql, (user_id, team_id, comp_id)).fetchone()
        return not rs is None

    def is_owner_of_competing_team(self, user_id, team_id, comp_id):
        """Test if a user is the owner of a given team and that team is
        participating in a given competition.

        Parameters
        ----------
        user_id: string
            Unique user identifier
        team_id: string
            Unique team identifier
        comp_id: string
            Unique competition identifier

        Returns
        -------
        bool
        """
        sql = 'SELECT * FROM team t, competition_team p '
        sql += 'WHERE t.id = p.team_id AND '
        sql += 't.owner_id = ? AND t.id = ? AND p.comp_id = ?'
        rs = self.con.execute(sql, (user_id, team_id, comp_id)).fetchone()
        return not rs is None

    def is_team_member(self, user_id, team_id):
        """Test if a user is member of a given team. The result is True if the
        team does not exist.

        Parameters
        ----------
        user_id: string
            Unique user identifier
        team_id: string
            Unique team identifier

        Returns
        -------
        bool
        """
        sql = 'SELECT user_id AS id FROM team_member WHERE team_id = ?'
        users = self.con.execute(sql, (team_id,)).fetchall()
        if users is None or len(users) == 0:
            return True
        for user in users:
            if user['id'] == user_id:
                return True
        return False


    def is_team_owner(self, user_id, team_id):
        """Test if a user is the owner of a given team. The result is True if
        the team does not exist.

        Parameters
        ----------
        user_id: string
            Unique user identifier
        team_id: string
            Unique team identifier

        Returns
        -------
        bool
        """
        sql = 'SELECT owner_id FROM team WHERE id = ?'
        team = self.con.execute(sql, (team_id,)).fetchone()
        if team is None:
            return True
        else:
            return team['owner_id'] == user_id

    def login(self, username, password):
        """Authorize a given user and assigne an API key for them. If the user
        is unknown or the given credentials do not match those in the database
        an unknown user error is raised.

        Returns the API key that has been associated with the user identifier.

        Parameters
        ----------
        username: string
            Unique name (i.e., email address) that the user provided when they
            registered
        password: string
            User password specified during registration (in plain text)

        Returns
        -------
        string

        Raises
        ------
        benchengine.user.error.UnknownUserError
        """
        # Get the unique user identifier and encrypted password. Raise error
        # if user is unknown
        sql = 'SELECT id, secret FROM registered_user '
        sql += 'WHERE email = ? AND active = 1'
        user = self.con.execute(sql, (username,)).fetchone()
        if user is None:
            raise err.UnknownUserError(username)
        # Validate that given credentials match the stored user secret
        if not pbkdf2_sha256.verify(password, user['secret']):
            raise err.UnknownUserError(username)
        user_id = user['id']
        # Remove any API key that may be associated with the user currently
        sql = 'DELETE FROM user_key WHERE user_id = ?'
        self.con.execute(sql, (user_id,))
        # Create a new API key for the user and set the expiry date. The key
        # expires login_timeout seconds from now.
        api_key = util.get_unique_identifier()
        expires = dt.datetime.now() + dt.timedelta(seconds=self.login_timeout)
        # Insert API key and expiry date into database and return the key
        sql = 'INSERT INTO user_key(user_id, api_key, expires) VALUES(?, ?, ?)'
        self.con.execute(sql, (user_id, api_key, expires.isoformat()))
        self.con.commit()
        return api_key

    def logout(self, api_key):
        """Invalidate the given API key. This will logout the user that is
        associated with the key.

        Parameters
        ----------
        api_key: string
            Unique API key assigned at login
        """
        self.con.execute('DELETE FROM user_key WHERE api_key = ?', (api_key,))
        self.con.commit()
