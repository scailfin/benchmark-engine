"""Implementation of API methods that access and manipulate user resources as
well as access tokens.
"""

from benchengine.api.serialize.user import UserSerializer
from benchengine.user.base import RegisteredUser

import benchengine.api.serialize.hateoas as hateoas


class UserApi(object):
    """Implement methods that handle user login and logout as well as
    registration of new users.
    """
    def __init__(self, manager, urls):
        """Initialize the user manager that maintains all registered users.

        Parameters
        ----------
        manager: benchengine.user.manager.UserManager
            Manager for registered users
        urls: benchengine.api.route.UrlFactory
            Factory for API resource Urls
        """
        self.manager = manager
        self.urls = urls
        self.serialize = UserSerializer(urls)

    def login(self, username, password):
        """Get access token for user with given credentials. Raises error if
        the user is unknown or if invalid credentials are provided.

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
        benchengine.user.error.UnknownUserError
        """
        access_token = self.manager.login(username, password)
        return self.serialize.login(access_token)

    def logout(self, access_token):
        """Logout user that is associated with the given access token. This
        method will always return a success object.

        Parameters
        ----------
        access_token: string
            User access token

        Returns
        -------
        dict
        """
        self.manager.logout(access_token)
        return self.serialize.success(
            links={hateoas.user(hateoas.LOGIN): self.urls.login()}
        )

    def register(self, username, password):
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

        Returns
        -------
        dict

        Raises
        ------
        benchengine.error.ConstraintViolationError
        benchengine.error.DuplicateUserError
        """
        user_id = self.manager.register_user(
            username=username,
            password=password,
            verify=False
        )
        return self.serialize.user(RegisteredUser(user_id, username))

    def whoami(self, access_token):
        """Get information for user that is associated with the given access
        token.

        Parameters
        ----------
        access_token: string
            User access token

        Returns
        -------
        dict

        Raises
        ------
        benchengine.error.UnauthenticatedAccessError
        """
        return self.serialize.user(user=self.manager.authenticate(access_token))

    def whoarethey(self, username):
        """Get information for user with given user name.

        Parameters
        ----------
        username: string
            Unique user name

        Returns
        -------
        dict

        Raises
        ------
        benchengine.error.UnknownUserError
        """
        return self.serialize.user(user=self.manager.get_user(username))
