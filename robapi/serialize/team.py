# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""Serializer for team resources."""

from robapi.serialize.base import Serializer

import robapi.serialize.hateoas as hateoas
import robapi.serialize.labels as labels


class TeamSerializer(Serializer):
    """Serializer for team resources."""
    def __init__(self, urls):
        """Initialize the reference to the Url factory.

        Parameters
        ----------
        urls: robapi.api.route.UrlFactory
            Factory for resource urls
        """
        super(TeamSerializer, self).__init__(urls)

    def team_descriptor(self, team, user_id=None):
        """Get serialization for a team descriptor. The optional user identifier
        specifies the current user. If given it controls the references that are
        included in the HATEOAS links list. Only team owners, for example, are
        allowed to delete a team.

        Parameters
        ----------
        team: robapi.model.user.team.base.TeamDescriptor
            Team descriptor
        user_id: string, optional
            Unique identifier of current user

        Returns
        -------
        dict
        """
        team_id = team.identifier
        team_url = self.urls.get_team(team_id)
        links = {
            hateoas.SELF: team_url,
            hateoas.UPLOAD: self.urls.upload_file(team_id)
        }
        if user_id is None or user_id == team.owner_id:
            links[hateoas.DELETE] = team_url
            links[hateoas.ADD] = self.urls.add_team_members(team_id)
        return {
            labels.ID: team_id,
            labels.NAME: team.name,
            labels.OWNER_ID: team.owner_id,
            labels.MEMBER_COUNT: team.member_count,
            labels.LINKS: hateoas.serialize(links)
        }

    def team_handle(self, team, user_id=None):
        """Get serialization for a team handle. The optional user identifier
        specifies the current user that controlls the list of HATEOAS links
        in the response.

        Parameters
        ----------
        team: robapi.model.user.team.base.TeamHandle
            Team descriptor
        user_id: string, optional
            Unique identifier of current user

        Returns
        -------
        dict
        """
        # The serialization of the team handle is an extension of the team
        # descriptor serialization
        obj = self.team_descriptor(team, user_id=user_id)
        # Add serializations for all team members
        members = list()
        for user in team.members.values():
            members.append({
                    labels.ID: user.identifier,
                    labels.USERNAME: user.username,
                    labels.LINKS: hateoas.serialize({
                        hateoas.DELETE: self.urls.remove_team_member(
                            team_id=team.identifier,
                            user_id=user.identifier
                        )
                    })
                })
        obj[labels.MEMBERS] = members
        return obj

    def team_listing(self, teams, user_id=None):
        """Get serialization of the team descriptor list. The optional user id
        identifiers the current user and determines the content of the HATEOAS
        links list.

        Parameters
        ----------
        teams: list(robapi.model.user.team.base.TeamDescriptor)
            Descriptors for competition teams
        user_id: string, optional
            Unique identifier of current user

        Returns
        -------
        dict
        """
        url = self.urls.list_teams()
        return {
            labels.TEAMS: [
                self.team_descriptor(team, user_id=user_id) for team in teams
            ],
            labels.LINKS: hateoas.serialize({
                hateoas.SELF: url,
                hateoas.CREATE: url
            })
        }
