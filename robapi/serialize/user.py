# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""Serializer for user resources."""

import robapi.serialize.hateoas as hateoas
import robapi.serialize.labels as labels


class UserSerializer(object):
    """Serializer for user resources."""
    def __init__(self, urls):
        """Initialize the reference to the Url factory.

        Parameters
        ----------
        urls: robapi.api.route.UrlFactory
            Factory for resource urls
        """
        self.urls = urls

    def registered(self, user):
        """Serialization for user handle of a newly registered user. The list of
        HATEOAS references will contain a link to activate the user.

        Parameters
        ----------
        user: robapi.model.user.UserHandle
            Handle for a registered user

        Returns
        -------
        dict
        """
        doc = self.user(user)
        link = {hateoas.user(hateoas.ACTIVATE): self.urls.activate_user()}
        doc[labels.LINKS].append(hateoas.serialize(link)[0])
        return doc

    def user(self, user):
        """Serialization for user handle. Contains the user name and the access
        token if the user is logged in. The list of HATEOAS references will
        contain a logout link only if the user is logged in.

        Parameters
        ----------
        user: robapi.model.user.UserHandle
            Handle for a registered user

        Returns
        -------
        dict
        """
        doc = {labels.ID: user.identifier, labels.USERNAME: user.name}
        links = {hateoas.user(hateoas.WHOAMI): self.urls.whoami()}
        if user.is_logged_in():
            doc[labels.ACCESS_TOKEN] = user.api_key
            links[hateoas.user(hateoas.LOGOUT)] = self.urls.logout()
        else:
            links[hateoas.user(hateoas.LOGIN)] = self.urls.login()
        doc[labels.LINKS] = hateoas.serialize(links)
        return doc
