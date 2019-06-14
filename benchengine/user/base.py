"""Base class to manage information about users that have registered with the
application. Each user has to provide a unique email address. We also associate
a unique user identifier with each user. The latter is used internally to
reference a user.
"""

import datetime as dt

class RegisteredUser(object):
    """Each user that registers with the application has a unique identifier
    and email associated with them. The valid until date contains the time
    until the current API key for the user expires.
    """
    def __init__(self, identifier, email, valid_until=None):
        """Initialize the user properties.

        Parameters
        ----------
        identifier: string
            Unique user identifier
        email: string
            User-provided unique email address
        valid_until: datetime.date, optional
            Time when current user API key expires
        """
        self.identifier = identifier
        self.email = email
        self.valid_until = valid_until

    def is_logged_in(self):
        """Test if the user is currently logged in.

        Returns
        -------
        bool
        """
        return not self.valid_until is None and self.valid_until >= dt.datetime.now()

    @property
    def username(self):
        """For now the user name and email address are the same.

        Returns
        -------
        string
        """
        return self.email
