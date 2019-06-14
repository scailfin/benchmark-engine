"""Test API methods for team resources."""

import os
import shutil

from unittest import TestCase

from benchengine.api.base import EngineApi
from benchengine.db import DatabaseDriver
from benchtmpl.util.tests import FakeStream

import benchengine.api.serialize.hateoas as hateoas
import benchengine.api.serialize.labels as labels
import benchengine.config as config
import benchengine.error as err

TMP_DIR = 'tests/files/.tmp'
CONNECT = 'sqlite:{}/benchengine.db'.format(TMP_DIR)


class TestTeamApi(TestCase):
    """Test API methods that access and manipulate teams."""
    def setUp(self):
        """Create empty directory."""
        if os.path.isdir(TMP_DIR):
            shutil.rmtree(TMP_DIR)
        os.mkdir(TMP_DIR)
        os.environ[config.ENV_DATABASE] = CONNECT
        os.environ[config.ENV_BASEDIR] = os.path.join(TMP_DIR, 'files')
        DatabaseDriver.init_db()
        self.engine = EngineApi()

    def tearDown(self):
        """Remove temporary directory."""
        self.engine.close()
        if os.path.isdir(TMP_DIR):
            shutil.rmtree(TMP_DIR)

    def test_create_team(self):
        """Test creating a new team."""
        users = self.engine.users()
        users.register(username='myuser', password='mypwd')
        response = users.login(username='myuser', password='mypwd')
        access_token = response[labels.ACCESS_TOKEN]
        teams = self.engine.teams()
        response = teams.create_team(access_token=access_token, name='My Team')
        self.assertEqual(len(response), 5)
        self.assertTrue(labels.ID in response)
        self.assertTrue(labels.NAME in response)
        self.assertTrue(labels.OWNER_ID in response)
        self.assertTrue(labels.MEMBER_COUNT in response)
        self.assertTrue(labels.LINKS in response)
        self.assertEqual(response[labels.MEMBER_COUNT], 1)
        links = hateoas.deserialize(response[labels.LINKS])
        self.assertEqual(len(links), 4)
        self.assertTrue(hateoas.SELF in links)
        self.assertTrue(hateoas.ADD in links)
        self.assertTrue(hateoas.DELETE in links)
        self.assertTrue(hateoas.UPLOAD in links)
        # Error when specifying unknonw user
        with self.assertRaises(err.UnknownUserError):
            teams.create_team(
                access_token=access_token,
                name='No Team',
                members=['myfriend']
            )
        response = users.register(username='myfriend', password='mypwd')
        user_id = response[labels.ID]
        response = teams.create_team(
            access_token=access_token,
            name='No Team',
            members=[user_id]
        )
        self.assertEqual(response[labels.MEMBER_COUNT], 2)

    def test_delete_team(self):
        """Test deleting a team."""
        # Initialize database with two user, each being the owner of one team
        users = self.engine.users()
        users.register(username='u1', password='p1')
        users.register(username='u2', password='p2')
        token1 = users.login(username='u1', password='p1')[labels.ACCESS_TOKEN]
        token2 = users.login(username='u2', password='p2')[labels.ACCESS_TOKEN]
        teams = self.engine.teams()
        team1 = teams.create_team(access_token=token1, name='Team1')[labels.ID]
        team2 = teams.create_team(access_token=token2, name='Team2')[labels.ID]
        # Delete team 1 for user 1 returns SUCCESS
        response = self.engine.teams().delete_team(team_id=team1, access_token=token1)
        self.assertEqual(response, {labels.STATE: 'SUCCESS'})
        # Deleting the same team again will raise unknown team error
        with self.assertRaises(err.UnknownTeamError):
            self.engine.teams().delete_team(team_id=team1, access_token=token1)
        # If user 1 attempts to delete team 2 an error is raised
        with self.assertRaises(err.UnauthorizedAccessError):
            self.engine.teams().delete_team(team_id=team2, access_token=token1)
        # The superuser (no access token) can delete team 2
        response = self.engine.teams().delete_team(team_id=team2)
        self.assertEqual(response, {labels.STATE: 'SUCCESS'})

    def test_team_get(self):
        """Test get team handle."""
        users = self.engine.users()
        users.register(username='u1', password='p1')[labels.ID]
        users.register(username='u2', password='p2')[labels.ID]
        token1 = users.login(username='u1', password='p1')[labels.ACCESS_TOKEN]
        token2 = users.login(username='u2', password='p2')[labels.ACCESS_TOKEN]
        teams = self.engine.teams()
        # User 1 and 2 are member of two teams.
        team_id = teams.create_team(access_token=token1, name='Team1')[labels.ID]
        response = teams.get_team(team_id=team_id, access_token=token1)
        self.assertEqual(len(response),6)
        self.assertTrue(labels.ID in response)
        self.assertTrue(labels.NAME in response)
        self.assertTrue(labels.MEMBERS in response)
        self.assertTrue(labels.MEMBER_COUNT in response)
        self.assertTrue(labels.OWNER_ID in response)
        self.assertTrue(labels.LINKS in response)
        members = response[labels.MEMBERS]
        for user in members:
            self.assertEqual(len(user), 3)
            self.assertTrue(labels.ID in user)
            self.assertTrue(labels.USERNAME in user)
            self.assertTrue(labels.LINKS in user)
            links = hateoas.deserialize(user[labels.LINKS])
            self.assertEqual(len(links), 1)
            self.assertTrue(hateoas.DELETE in links)
        links = hateoas.deserialize(response[labels.LINKS])
        self.assertEqual(len(links), 4)
        self.assertTrue(hateoas.SELF in links)
        self.assertTrue(hateoas.ADD in links)
        self.assertTrue(hateoas.DELETE in links)
        self.assertTrue(hateoas.UPLOAD in links)
        team_id = teams.create_team(access_token=token2, name='Team2')[labels.ID]
        with self.assertRaises(err.UnauthorizedAccessError):
            teams.get_team(team_id=team_id, access_token=token1)
        teams.get_team(team_id=team_id)

    def test_list_teams(self):
        """Test getting team listings."""
        users = self.engine.users()
        u1 = users.register(username='u1', password='p1')[labels.ID]
        u2 = users.register(username='u2', password='p2')[labels.ID]
        token1 = users.login(username='u1', password='p1')[labels.ACCESS_TOKEN]
        token2 = users.login(username='u2', password='p2')[labels.ACCESS_TOKEN]
        teams = self.engine.teams()
        # User 1 and 2 are member of two teams.
        teams.create_team(access_token=token1, name='Team1')
        teams.create_team(access_token=token2, name='Team2', members=[u1])
        teams.create_team(access_token=token2, name='Team3')
        tlist = teams.list_teams(access_token=token1)
        self.assertEqual(len(tlist[labels.TEAMS]), 2)
        links = hateoas.deserialize(tlist[labels.LINKS])
        self.assertEqual(len(links), 2)
        self.assertTrue(hateoas.SELF in links)
        self.assertTrue(hateoas.CREATE in links)
        tlist = teams.list_teams(access_token=token2)
        self.assertEqual(len(tlist[labels.TEAMS]), 2)
        tlist = teams.list_teams()
        self.assertEqual(len(tlist[labels.TEAMS]), 3)

    def test_team_members(self):
        """Test adding and removing team members."""
        # Initialize database with three users and one team
        users = self.engine.users()
        u1 = users.register(username='u1', password='p1')[labels.ID]
        u2 = users.register(username='u2', password='p2')[labels.ID]
        u3 = users.register(username='u3', password='p3')[labels.ID]
        token1 = users.login(username='u1', password='p1')[labels.ACCESS_TOKEN]
        token2 = users.login(username='u2', password='p2')[labels.ACCESS_TOKEN]
        teams = self.engine.teams()
        team1 = teams.create_team(access_token=token1, name='Team1')[labels.ID]
        teams = self.engine.teams()
        # User 2 cannot add themselves as team member
        with self.assertRaises(err.UnauthorizedAccessError):
            teams.add_members(team_id=team1, members=[u2], access_token=token2)
        # User 1 can add user 2 as team member
        response = teams.add_members(team_id=team1, members=[u2], access_token=token1)
        self.assertTrue(len(response[labels.MEMBERS]), 2)
        # The superuser can also add team members
        response = teams.add_members(team_id=team1, members=[u3])
        self.assertTrue(len(response[labels.MEMBERS]), 3)
        # User 2 cannot remove user 3 as team member
        with self.assertRaises(err.UnauthorizedAccessError):
            teams.remove_member(team_id=team1, member_id=u3, access_token=token2)
        # User 2 can remove themselves as team member
        response = teams.remove_member(team_id=team1, member_id=u2, access_token=token2)
        self.assertTrue(len(response[labels.MEMBERS]), 2)
        # User 1 can remove user 3 as team member
        response = teams.remove_member(team_id=team1, member_id=u3, access_token=token1)
        self.assertTrue(len(response[labels.MEMBERS]), 1)
        # User 1 cannot remove themselves as team member
        with self.assertRaises(err.ConstraintViolationError):
            teams.remove_member(team_id=team1, member_id=u1, access_token=token1)

    def test_update_team_name(self):
        """Test updating the team name."""
        users = self.engine.users()
        users.register(username='u1', password='p1')[labels.ID]
        users.register(username='u2', password='p2')[labels.ID]
        token1 = users.login(username='u1', password='p1')[labels.ACCESS_TOKEN]
        token2 = users.login(username='u2', password='p2')[labels.ACCESS_TOKEN]
        teams = self.engine.teams()
        # Create first team and rename it
        team_id = teams.create_team(access_token=token1, name='Team1')[labels.ID]
        response = teams.update_team_name(team_id=team_id, name='My Team', access_token=token1)
        self.assertEqual(len(response), 5)
        self.assertEqual(response[labels.NAME], 'My Team')
        # Create second team and let user2 try to rename it
        team_id = teams.create_team(access_token=token1, name='Team1')[labels.ID]
        with self.assertRaises(err.UnauthorizedAccessError):
            teams.update_team_name(team_id=team_id, name='My Other Team', access_token=token2)

    def test_upload_files(self):
        """Test uploading and deleting files."""
        # Create two users and one team
        users = self.engine.users()
        users.register(username='u1', password='p1')[labels.ID]
        users.register(username='u2', password='p2')[labels.ID]
        token1 = users.login(username='u1', password='p1')[labels.ACCESS_TOKEN]
        token2 = users.login(username='u2', password='p2')[labels.ACCESS_TOKEN]
        teams = self.engine.teams()
        team_id = teams.create_team(access_token=token1, name='Team1')[labels.ID]
        # Upload file
        response = teams.upload_file(
            file=FakeStream(),
            file_name='file.txt',
            team_id=team_id,
            access_token=token1
        )
        self.assertEqual(len(response), 5)
        self.assertTrue(labels.ID in response)
        self.assertTrue(labels.NAME in response)
        self.assertTrue(labels.CREATED_AT in response)
        self.assertTrue(labels.FILESIZE in response)
        self.assertTrue(labels.LINKS in response)
        links = hateoas.deserialize(response[labels.LINKS])
        self.assertEqual(len(links), 2)
        self.assertTrue(hateoas.DELETE in links)
        self.assertTrue(hateoas.DOWNLOAD in links)
        # Error when uploading as a non-member
        with self.assertRaises(err.UnauthorizedAccessError):
            teams.upload_file(
                file=FakeStream(),
                file_name='file.txt',
                team_id=team_id,
                access_token=token2
            )
        # Get handle for uploaded file
        file_id = response[labels.ID]
        fh = teams.get_file(team_id=team_id, file_id=file_id, access_token=token1)
        self.assertEqual(fh, response)
        # Error when getting file as a non-member
        with self.assertRaises(err.UnauthorizedAccessError):
            teams.get_file(team_id=team_id, file_id=file_id, access_token=token2)
        # Error when deleting file as non member
        with self.assertRaises(err.UnauthorizedAccessError):
            teams.delete_file(team_id=team_id, file_id=file_id, access_token=token2)
        # Delete file
        response = teams.delete_file(
            team_id=team_id,
            file_id=file_id,
            access_token=token1
        )
        self.assertEqual(response, {labels.STATE: 'SUCCESS'})
        # Error when accessing or deleting a non-existing file
        with self.assertRaises(err.UnknownFileError):
            teams.get_file(team_id=team_id, file_id=file_id, access_token=token1)
        with self.assertRaises(err.UnknownFileError):
            teams.delete_file(team_id=team_id, file_id=file_id, access_token=token1)


if __name__ == '__main__':
    import unittest
    unittest.main()
