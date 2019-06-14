"""Test functionality of the team manager."""

import os
import shutil

from passlib.hash import pbkdf2_sha256
from unittest import TestCase

from benchengine.db import DatabaseDriver
from benchengine.user.team.manager import TeamManager

import benchengine.error as err
import benchtmpl.util.core as util
import benchengine.user.team.manager as role


TMP_DIR = './tests/files/.tmp'
CONNECT = 'sqlite:{}/team.db'.format(TMP_DIR)

USER_1 = util.get_unique_identifier()
USER_2 = util.get_unique_identifier()
USER_3 = util.get_unique_identifier()
USER_4 = util.get_unique_identifier()


class TestTeamManager(TestCase):
    """Test creating and maintaining teams."""
    def setUp(self):
        if os.path.isdir(TMP_DIR):
            shutil.rmtree(TMP_DIR)
        os.makedirs(TMP_DIR)
        """Create a fresh database and insert two default users."""
        DatabaseDriver.init_db(connect_string=CONNECT)
        con = DatabaseDriver.connect(connect_string=CONNECT)
        sql = 'INSERT INTO registered_user(id, email, secret, active) VALUES(?, ?, ?, ?)'
        con.execute(sql, (USER_1, USER_1, pbkdf2_sha256.hash(USER_1), 1))
        con.execute(sql, (USER_2, USER_2, pbkdf2_sha256.hash(USER_2), 1))
        con.execute(sql, (USER_3, USER_3, pbkdf2_sha256.hash(USER_3), 1))
        con.execute(sql, (USER_4, USER_4, pbkdf2_sha256.hash(USER_4), 0))
        con.commit()
        self.team_manager = TeamManager(con)

    def tearDown(self):
        """Close connection and remove database file."""
        self.team_manager.close()
        if os.path.isdir(TMP_DIR):
            shutil.rmtree(TMP_DIR)

    def test_add_and_remove_member(self):
        """Test adding a new team member."""
        team = self.team_manager.create_team(
            name='My Team',
            owner_id=USER_1,
            members=[USER_1]
        )
        self.assertEqual(team.name, 'My Team')
        self.assertEqual(team.member_count, 1)
        # Ensure that user 1 is both member and owner of the team
        self.assertTrue(
            self.team_manager.is_team_member(
                user_id=USER_1,
                team_id=team.identifier
            )
        )
        self.assertTrue(
            self.team_manager.is_team_owner(
                user_id=USER_1,
                team_id=team.identifier
            )
        )
        self.team_manager.add_member(team_id=team.identifier, user_id=USER_2)
        # Ensure that user 2 is member of the team but not the team owner
        self.assertTrue(
            self.team_manager.is_team_member(
                user_id=USER_2,
                team_id=team.identifier
            )
        )
        self.assertFalse(
            self.team_manager.is_team_owner(
                user_id=USER_2,
                team_id=team.identifier
            )
        )
        team = self.team_manager.get_team(team.identifier)
        self.assertEqual(team.name, 'My Team')
        self.assertEqual(team.member_count, 2)
        self.assertTrue(USER_1 in team.members)
        self.assertTrue(USER_2 in team.members)
        # Adding user to unknonw team raises error
        with self.assertRaises(err.UnknownTeamError):
            self.team_manager.add_member(team_id='unknown', user_id=USER_1)
        # Adding unknown user to team raises error
        with self.assertRaises(err.UnknownUserError):
            self.team_manager.add_member(team_id=team.identifier, user_id='unknown')
        # Adding duplicate user to team raises error
        with self.assertRaises(err.DuplicateUserError):
            self.team_manager.add_member(team_id=team.identifier, user_id=USER_1)
        # Remove user 2 as team member
        self.team_manager.remove_member(team.identifier, USER_2)
        team = self.team_manager.get_team(team.identifier)
        self.assertEqual(team.name, 'My Team')
        self.assertEqual(team.member_count, 1)
        self.assertTrue(USER_1 in team.members)
        self.assertFalse(USER_2 in team.members)
        # Remove from unknown team raises error.
        with self.assertRaises(err.UnknownTeamError):
            self.team_manager.remove_member('unknown', USER_2)
        # Remove team owner raises error.
        with self.assertRaises(err.ConstraintViolationError):
            self.team_manager.remove_member(team.identifier, USER_1)
        # Removing unknown user raises no exception
        self.team_manager.remove_member(team.identifier, 'unknown')
        team = self.team_manager.get_team(team.identifier)
        self.assertEqual(team.name, 'My Team')
        self.assertEqual(team.member_count, 1)
        self.assertTrue(USER_1 in team.members)
        self.assertFalse(USER_2 in team.members)

    def test_authorize(self):
        """Test user authorization."""
        # Create team with two members
        team = self.team_manager.create_team(
            name='My Team',
            owner_id=USER_1,
            members=[USER_1]
        )
        team_id = team.identifier
        self.team_manager.add_member(team_id=team.identifier, user_id=USER_2)
        token1 = self.team_manager.login(USER_1, USER_1)
        # User 1 has all roles
        self.team_manager.authorize(
            access_token=token1,
            team_id=team_id,
            role=role.OWNER,
            member_id=USER_1
        )
        self.team_manager.authorize(
            access_token=token1,
            team_id=team_id,
            role=role.OWNER_OR_SELF,
            member_id=USER_1
        )
        self.team_manager.authorize(
            access_token=token1,
            team_id=team_id,
            role=role.MEMBER
        )
        # If user is not logged in an error is raised
        with self.assertRaises(err.UnauthenticatedAccessError):
            self.team_manager.authorize(
                access_token=USER_2,
                team_id=team_id,
                role=role.MEMBER
            )
        # User 2 has team member roles
        token2 = self.team_manager.login(USER_2, USER_2)
        self.team_manager.authorize(
            access_token=token2,
            team_id=team_id,
            role=role.MEMBER
        )
        self.team_manager.authorize(
            access_token=token2,
            team_id=team_id,
            role=role.OWNER_OR_SELF,
            member_id=USER_2
        )
        with self.assertRaises(err.UnauthorizedAccessError):
            self.team_manager.authorize(
                access_token=token2,
                team_id=team_id,
                role=role.OWNER,
                member_id=USER_2
            )
        # User 3 has no roles
        token3 = self.team_manager.login(USER_3, USER_3)
        with self.assertRaises(err.UnauthorizedAccessError):
            self.team_manager.authorize(
                access_token=token3,
                team_id=team_id,
                role=role.OWNER
            )
        with self.assertRaises(err.UnauthorizedAccessError):
            self.team_manager.authorize(
                access_token=token3,
                team_id=team_id,
                role=role.OWNER_OR_SELF,
                member_id=USER_3
            )
        with self.assertRaises(err.UnauthorizedAccessError):
            self.team_manager.authorize(
                access_token=token3,
                team_id=team_id,
                role=role.MEMBER
            )

    def test_create_team(self):
        """Test creating new teams."""
        team = self.team_manager.create_team(name='My Team', owner_id=USER_1)
        self.assertEqual(team.name, 'My Team')
        self.assertEqual(team.member_count, 1)
        team = self.team_manager.create_team(
            name='My Second Team',
            owner_id=USER_2,
            members=[USER_1, USER_2, USER_1, USER_2]
        )
        self.assertEqual(team.name, 'My Second Team')
        self.assertEqual(team.member_count, 2)
        # Get second team to ensure that all members and the owner are set
        # properly
        team = self.team_manager.get_team(team.identifier)
        self.assertEqual(team.name, 'My Second Team')
        self.assertEqual(team.member_count, 2)
        self.assertEqual(team.owner_id, USER_2)
        self.assertTrue(USER_1 in team.members)
        self.assertTrue(USER_2 in team.members)
        # Duplicate name raises error
        with self.assertRaises(err.ConstraintViolationError):
            self.team_manager.create_team(name='My Team', owner_id=USER_1)
        # Long name raises error
        with self.assertRaises(err.ConstraintViolationError):
            self.team_manager.create_team(name='a' * 256, owner_id=USER_1)
        # Empty name
        with self.assertRaises(err.ConstraintViolationError):
            self.team_manager.create_team(name=' ', owner_id=USER_1)
        # Create team with unknown owner or member raises error
        with self.assertRaises(err.UnknownUserError):
            self.team_manager.create_team(name='New Team', owner_id='unknown')
        with self.assertRaises(err.UnknownUserError):
            self.team_manager.create_team(
            name='New Team 2',
            owner_id=USER_1,
            members=[USER_2, 'unknown']
        )
        # Get team with unknown identifier raises error
        with self.assertRaises(err.UnknownTeamError):
            self.team_manager.get_team('unknown')

    def test_delete_team(self):
        """Test creating and deleting a team."""
        # Create team and ensure that accessing the team does not raise an
        # exception
        team = self.team_manager.create_team(name='My Team', owner_id=USER_1)
        team = self.team_manager.get_team(team.identifier)
        # Delete team
        self.team_manager.delete_team(team.identifier)
        # If we try to access the deleted team an error is raises. Same if we
        # try to delete the team again.
        with self.assertRaises(err.UnknownTeamError):
            self.team_manager.get_team(team.identifier)
        with self.assertRaises(err.UnknownTeamError):
            self.team_manager.delete_team(team.identifier)

    def test_inactive_user(self):
        """Test creating teams or adding members using inactive users."""
        # Create a team that has an inactive owner raises error
        with self.assertRaises(err.UnknownUserError):
            self.team_manager.create_team(name='My Team', owner_id=USER_4)
        # Create a team with an inactive team member raises error
        with self.assertRaises(err.UnknownUserError):
            self.team_manager.create_team(
                name='My Team',
                owner_id=USER_1,
                members=[USER_4]
            )
        # Adding inactive user to existing team raises error
        team = self.team_manager.create_team(name='My Team', owner_id=USER_1)
        with self.assertRaises(err.UnknownUserError):
            self.team_manager.add_member(team_id=team.identifier, user_id=USER_4)

    def test_list_teams(self):
        """Test listing all teams."""
        self.team_manager.create_team(name='Team1', owner_id=USER_1, members=[USER_2])
        self.team_manager.create_team(name='Team2', owner_id=USER_2)
        self.team_manager.create_team(name='Team3', owner_id=USER_2, members=[USER_1, USER_2])
        teams = {t.name: t for t in self.team_manager.list_teams()}
        self.assertEqual(len(teams), 3)
        self.assertEqual(teams['Team1'].member_count, 2)
        self.assertEqual(teams['Team2'].member_count, 1)
        self.assertEqual(teams['Team3'].member_count, 2)
        # List teams for user 1
        teams = {t.name: t for t in self.team_manager.list_teams(user_id=USER_1)}
        self.assertEqual(len(teams), 2)
        self.assertEqual(teams['Team1'].member_count, 2)
        self.assertEqual(teams['Team3'].member_count, 2)
        # List teams for user 2
        teams = {t.name: t for t in self.team_manager.list_teams(user_id=USER_2)}
        self.assertEqual(len(teams), 3)
        self.assertEqual(teams['Team1'].member_count, 2)
        self.assertEqual(teams['Team2'].member_count, 1)
        self.assertEqual(teams['Team3'].member_count, 2)

    def test_update_team_name(self):
        """Test updating the team name."""
        team1 = self.team_manager.create_team(name='My Team', owner_id=USER_1)
        team2 = self.team_manager.create_team(name='Second', owner_id=USER_2)
        self.assertEqual(team2.name, 'Second')
        team2 = self.team_manager.update_team_name(
            team_id=team2.identifier,
            name='Second Team'
        )
        self.assertEqual(team2.name, 'Second Team')
        # Error when updating to a name that exists
        with self.assertRaises(err.ConstraintViolationError):
            self.team_manager.update_team_name(
                team_id=team2.identifier,
                name='My Team'
            )
        with self.assertRaises(err.ConstraintViolationError):
            self.team_manager.update_team_name(
                team_id=team2.identifier,
                name='A' * 256
            )


if __name__ == '__main__':
    import unittest
    unittest.main()
