# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""Implementation of API methods that access and manipulate user resources as
well as access tokens.
"""

from robapi.serialize.user import UserSerializer
from robapi.service.route import UrlFactory

import robapi.model.user as auth


class UserService(object):
    """Implement methods that handle user login and logout as well as
    registration and activation of new users.
    """
    def __init__(self, manager, urls=None, serializer=None):
        """Initialize the user manager that maintains all registered users.

        Parameters
        ----------
        manager: robapi.model.user.UserManager
            Manager for registered users
        urls: robapi.api.route.UrlFactory
            Factory for API resource Urls
        serializer: robapi.api.serialize.user.UserSerializer, optional
            Override the default serializer
        """
        self.manager = manager
        self.urls = urls if not urls is None else UrlFactory()
        self.serialize = serializer if not serializer is None else UserSerializer(self.urls)

    def activate_user(self, user_id):
        """Activate a new user with the given identifier.

        Parameters
        ----------
        user_id: string
            Unique user name

        Returns
        -------
        dict

        Raises
        ------
        robapi.model.user.error.UnknownUserError
        """
        return self.serialize.user(self.manager.activate_user(user_id))

    def login_user(self, username, password):
        """Get handle for user with given credentials. Raises error if the user
        is unknown or if invalid credentials are provided.

        Parameters
        ----------
        username: string
            Unique name of registered user
        password: string
            User password (in plain text)

        Returns
        -------
        dict

        Raises
        ------
        robapi.model.user.error.UnknownUserError
        """
        return self.serialize.user(self.manager.login(username, password))

    def logout_user(self, access_token):
        """Logout user that is associated with the given access token. This
        method will always return a success object.

        Parameters
        ----------
        access_token: string
            User access token

        Returns
        -------
        dict

        Raises
        ------
        robapi.error.UnauthenticatedAccessError
        """
        return self.serialize.user(self.manager.logout(access_token))

    def register_user(self, username, password, verify=False):
        """Create a new user for the given username and password. Raises an
        error if a user with that name already exists or if the user name is
        ivalid (e.g., empty or too long).

        Returns success object if user was registered successfully.

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
        dict

        Raises
        ------
        robapi.error.ConstraintViolationError
        robapi.error.DuplicateUserError
        """
        user = self.manager.register_user(
            username=username,
            password=password,
            verify=verify
        )
        if verify:
            return self.serialize.registered(user)
        else:
            return self.serialize.user(user)

    def whoami_user(self, access_token):
        """Get serialization of the user that is associated with the given
        access token.

        Parameters
        ----------
        access_token: string
            User access token

        Returns
        -------
        dict
        """
        user = auth.authenticate(self.manager.con, access_token)
        return self.serialize.user(user)
