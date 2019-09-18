# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""Test functionality of the team manager."""

import os
import pytest

from passlib.hash import pbkdf2_sha256

from benchengine.db import DatabaseDriver
from benchengine.user.team.manager import TeamManager

import benchengine.error as err
import benchtmpl.util.core as util
import benchengine.user.team.manager as role


USER_1 = util.get_unique_identifier()
USER_2 = util.get_unique_identifier()
USER_3 = util.get_unique_identifier()
USER_4 = util.get_unique_identifier()


class TestTeamManager(object):
    """Test creating and maintaining teams."""
    def connect(self, base_dir):
        """Create a fresh database and insert default users."""
        connect_string = 'sqlite:{}/auth.db'.format(str(base_dir))
        DatabaseDriver.init_db(connect_string=connect_string)
        con = DatabaseDriver.connect(connect_string=connect_string)
        sql = 'INSERT INTO registered_user(id, email, secret, active) VALUES(?, ?, ?, ?)'
        con.execute(sql, (USER_1, USER_1, pbkdf2_sha256.hash(USER_1), 1))
        con.execute(sql, (USER_2, USER_2, pbkdf2_sha256.hash(USER_2), 1))
        con.execute(sql, (USER_3, USER_3, pbkdf2_sha256.hash(USER_3), 1))
        con.execute(sql, (USER_4, USER_4, pbkdf2_sha256.hash(USER_4), 0))
        con.commit()
        return TeamManager(con)

    def test_add_and_remove_member(self, tmpdir):
        """Test adding a new team member."""
        team_manager = self.connect(tmpdir)
        team = team_manager.create_team(
            name='My Team',
            owner_id=USER_1,
            members=[USER_1]
        )
        assert team.name == 'My Team'
        assert team.member_count == 1
        # Ensure that user 1 is both member and owner of the team
        is_member = team_manager.is_team_member(
            user_id=USER_1,
            team_id=team.identifier
        )
        assert is_member
        is_owner = team_manager.is_team_owner(
            user_id=USER_1,
            team_id=team.identifier
        )
        assert is_owner
        team_manager.add_member(team_id=team.identifier, user_id=USER_2)
        # Ensure that user 2 is member of the team but not the team owner
        is_member = team_manager.is_team_member(
            user_id=USER_2,
            team_id=team.identifier
        )
        assert is_member
        is_owner = team_manager.is_team_owner(
            user_id=USER_2,
            team_id=team.identifier
        )
        assert not is_owner
        team = team_manager.get_team(team.identifier)
        assert team.name == 'My Team'
        assert team.member_count == 2
        assert USER_1 in team.members
        assert USER_2 in team.members
        # Adding user to unknonw team raises error
        with pytest.raises(err.UnknownTeamError):
            team_manager.add_member(team_id='unknown', user_id=USER_1)
        # Adding unknown user to team raises error
        with pytest.raises(err.UnknownUserError):
            team_manager.add_member(team_id=team.identifier, user_id='unknown')
        # Adding duplicate user to team raises error
        with pytest.raises(err.DuplicateUserError):
            team_manager.add_member(team_id=team.identifier, user_id=USER_1)
        # Remove user 2 as team member
        team_manager.remove_member(team.identifier, USER_2)
        team = team_manager.get_team(team.identifier)
        assert team.name == 'My Team'
        assert team.member_count == 1
        assert USER_1 in team.members
        assert USER_2 not in team.members
        # Remove from unknown team raises error.
        with pytest.raises(err.UnknownTeamError):
            team_manager.remove_member('unknown', USER_2)
        # Remove team owner raises error.
        with pytest.raises(err.ConstraintViolationError):
            team_manager.remove_member(team.identifier, USER_1)
        # Removing unknown user raises no exception
        team_manager.remove_member(team.identifier, 'unknown')
        team = team_manager.get_team(team.identifier)
        assert team.name =='My Team'
        assert team.member_count == 1
        assert USER_1 in team.members
        assert not USER_2 in team.members

    def test_authorize(self, tmpdir):
        """Test user authorization."""
        # Create team with two members
        team_manager = self.connect(tmpdir)
        team = team_manager.create_team(
            name='My Team',
            owner_id=USER_1,
            members=[USER_1]
        )
        team_id = team.identifier
        team_manager.add_member(team_id=team.identifier, user_id=USER_2)
        token1 = team_manager.login(USER_1, USER_1)
        # User 1 has all roles
        team_manager.authorize(
            access_token=token1,
            team_id=team_id,
            role=role.OWNER,
            member_id=USER_1
        )
        team_manager.authorize(
            access_token=token1,
            team_id=team_id,
            role=role.OWNER_OR_SELF,
            member_id=USER_1
        )
        team_manager.authorize(
            access_token=token1,
            team_id=team_id,
            role=role.MEMBER
        )
        # If user is not logged in an error is raised
        with pytest.raises(err.UnauthenticatedAccessError):
            team_manager.authorize(
                access_token=USER_2,
                team_id=team_id,
                role=role.MEMBER
            )
        # User 2 has team member roles
        token2 = team_manager.login(USER_2, USER_2)
        team_manager.authorize(
            access_token=token2,
            team_id=team_id,
            role=role.MEMBER
        )
        team_manager.authorize(
            access_token=token2,
            team_id=team_id,
            role=role.OWNER_OR_SELF,
            member_id=USER_2
        )
        with pytest.raises(err.UnauthorizedAccessError):
            team_manager.authorize(
                access_token=token2,
                team_id=team_id,
                role=role.OWNER,
                member_id=USER_2
            )
        # User 3 has no roles
        token3 = team_manager.login(USER_3, USER_3)
        with pytest.raises(err.UnauthorizedAccessError):
            team_manager.authorize(
                access_token=token3,
                team_id=team_id,
                role=role.OWNER
            )
        with pytest.raises(err.UnauthorizedAccessError):
            team_manager.authorize(
                access_token=token3,
                team_id=team_id,
                role=role.OWNER_OR_SELF,
                member_id=USER_3
            )
        with pytest.raises(err.UnauthorizedAccessError):
            team_manager.authorize(
                access_token=token3,
                team_id=team_id,
                role=role.MEMBER
            )

    def test_create_team(self, tmpdir):
        """Test creating new teams."""
        team_manager = self.connect(tmpdir)
        team = team_manager.create_team(name='My Team', owner_id=USER_1)
        assert team.name == 'My Team'
        assert team.member_count == 1
        team = team_manager.create_team(
            name='My Second Team',
            owner_id=USER_2,
            members=[USER_1, USER_2, USER_1, USER_2]
        )
        assert team.name == 'My Second Team'
        assert team.member_count == 2
        # Get second team to ensure that all members and the owner are set
        # properly
        team = team_manager.get_team(team.identifier)
        assert team.name == 'My Second Team'
        assert team.member_count == 2
        assert team.owner_id == USER_2
        assert USER_1 in team.members
        assert USER_2 in team.members
        # Duplicate name raises error
        with pytest.raises(err.ConstraintViolationError):
            team_manager.create_team(name='My Team', owner_id=USER_1)
        # Long name raises error
        with pytest.raises(err.ConstraintViolationError):
            team_manager.create_team(name='a' * 256, owner_id=USER_1)
        # Empty name
        with pytest.raises(err.ConstraintViolationError):
            team_manager.create_team(name=' ', owner_id=USER_1)
        # Create team with unknown owner or member raises error
        with pytest.raises(err.UnknownUserError):
            team_manager.create_team(name='New Team', owner_id='unknown')
        with pytest.raises(err.UnknownUserError):
            team_manager.create_team(
            name='New Team 2',
            owner_id=USER_1,
            members=[USER_2, 'unknown']
        )
        # Get team with unknown identifier raises error
        with pytest.raises(err.UnknownTeamError):
            team_manager.get_team('unknown')

    def test_delete_team(self, tmpdir):
        """Test creating and deleting a team."""
        # Create team and ensure that accessing the team does not raise an
        # exception
        team_manager = self.connect(tmpdir)
        team = team_manager.create_team(name='My Team', owner_id=USER_1)
        team = team_manager.get_team(team.identifier)
        # Delete team
        team_manager.delete_team(team.identifier)
        # If we try to access the deleted team an error is raises. Same if we
        # try to delete the team again.
        with pytest.raises(err.UnknownTeamError):
            team_manager.get_team(team.identifier)
        with pytest.raises(err.UnknownTeamError):
            team_manager.delete_team(team.identifier)

    def test_inactive_user(self, tmpdir):
        """Test creating teams or adding members using inactive users."""
        # Create a team that has an inactive owner raises error
        team_manager = self.connect(tmpdir)
        with pytest.raises(err.UnknownUserError):
            team_manager.create_team(name='My Team', owner_id=USER_4)
        # Create a team with an inactive team member raises error
        with pytest.raises(err.UnknownUserError):
            team_manager.create_team(
                name='My Team',
                owner_id=USER_1,
                members=[USER_4]
            )
        # Adding inactive user to existing team raises error
        team = team_manager.create_team(name='My Team', owner_id=USER_1)
        with pytest.raises(err.UnknownUserError):
            team_manager.add_member(team_id=team.identifier, user_id=USER_4)

    def test_list_teams(self, tmpdir):
        """Test listing all teams."""
        team_manager = self.connect(tmpdir)
        team_manager.create_team(name='Team1', owner_id=USER_1, members=[USER_2])
        team_manager.create_team(name='Team2', owner_id=USER_2)
        team_manager.create_team(name='Team3', owner_id=USER_2, members=[USER_1, USER_2])
        teams = {t.name: t for t in team_manager.list_teams()}
        assert len(teams) == 3
        assert teams['Team1'].member_count == 2
        assert teams['Team2'].member_count == 1
        assert teams['Team3'].member_count == 2
        # List teams for user 1
        teams = {t.name: t for t in team_manager.list_teams(user_id=USER_1)}
        assert len(teams) == 2
        assert teams['Team1'].member_count == 2
        assert teams['Team3'].member_count == 2
        # List teams for user 2
        teams = {t.name: t for t in team_manager.list_teams(user_id=USER_2)}
        assert len(teams) == 3
        assert teams['Team1'].member_count == 2
        assert teams['Team2'].member_count == 1
        assert teams['Team3'].member_count == 2

    def test_update_team_name(self, tmpdir):
        """Test updating the team name."""
        team_manager = self.connect(tmpdir)
        team1 = team_manager.create_team(name='My Team', owner_id=USER_1)
        team2 = team_manager.create_team(name='Second', owner_id=USER_2)
        assert team2.name == 'Second'
        team2 = team_manager.update_team_name(
            team_id=team2.identifier,
            name='Second Team'
        )
        assert team2.name == 'Second Team'
        # Error when updating to a name that exists
        with pytest.raises(err.ConstraintViolationError):
            team_manager.update_team_name(
                team_id=team2.identifier,
                name='My Team'
            )
        with pytest.raises(err.ConstraintViolationError):
            team_manager.update_team_name(
                team_id=team2.identifier,
                name='A' * 256
            )
