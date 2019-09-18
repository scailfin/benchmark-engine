# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""Serializer for user resources."""

from benchengine.api.serialize.base import Serializer

import benchengine.api.serialize.hateoas as hateoas
import benchengine.api.serialize.labels as labels


class UserSerializer(Serializer):
    """Serializer for user resources."""
    def __init__(self, urls):
        """Initialize the reference to the Url factory.

        Parameters
        ----------
        urls: benchengine.api.route.UrlFactory
            Factory for resource urls
        """
        super(UserSerializer, self).__init__(urls)

    def login(self, access_token):
        """Serialization for successful login. Contains tha access token and a
        list of HATEOAS references.

        Parameters
        ----------
        access_token: string
            User access token

        Returns
        -------
        dict
        """
        return {
            labels.ACCESS_TOKEN: access_token,
            labels.LINKS: hateoas.serialize({
                hateoas.SERVICE: self.urls.service_descriptor(),
                hateoas.user(hateoas.LOGOUT): self.urls.logout()
            })
        }

    def user(self, user):
        """Get serialization for a given registered user.

        Parameters
        ----------
        user: benchengine.user.base.RegisteredUser
            User object

        Returns
        -------
        dict
        """
        return {
            labels.ID: user.identifier,
            labels.USERNAME: user.username,
            labels.LINKS: hateoas.serialize({
                hateoas.user(hateoas.LOGIN): self.urls.login(),
                hateoas.user(hateoas.LOGOUT): self.urls.logout()
            })
        }
