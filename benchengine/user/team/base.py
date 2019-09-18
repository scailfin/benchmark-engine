# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""Base classes that define team descriptors and handles.

The team descriptor contains the basic information about a team, namely the team
identifier, name, and member count. The team handle extends the descriptor and
contains references to the team members and the team owner.
"""


class TeamDescriptor(object):
    """Basic information about a team of users that may participate in a
    competition. Each team has a unique identifier and a unique name.
    """
    def __init__(self, identifier, name, owner_id, member_count):
        """Initialize the descriptor attributes.

        Parameters
        ----------
        identifier: string
            Unique team identifier
        name: string
            Unique team name
        owner_id: string
            Unique identifier for user that created the team
        member_count: int
            Number of team members
        """
        self.identifier = identifier
        self.name = name
        self.owner_id = owner_id
        self.member_count = member_count


class TeamHandle(TeamDescriptor):
    """The team handle extends the team descriptor. The handle contains
    references to the individual team members and the team owner.
    """
    def __init__(self, identifier, name, owner_id, members):
        """Initialize the team handle.

        Parameters
        ----------
        identifier: string
            Unique team identifier
        name: string
            Unique team name
        owner_id: string
            Unique identifier for user that created the team
        members: dict(benchengine.user.base.RegisteredUser)
            List of users that are team members. Includes at least one member
            which is the team owner.
        """
        super(TeamHandle, self).__init__(
            identifier=identifier,
            name=name,
            owner_id=owner_id,
            member_count=len(members)
        )
        self.members = members
