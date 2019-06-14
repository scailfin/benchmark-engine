"""Implementation of API methods that access and manipulate teams that the
current user is an owner or a member of. The current user is the user that is
associated with a given access token.
"""

import os

from benchengine.api.serialize.team import TeamSerializer
from benchtmpl.io.files.store import Filestore

import benchengine.error as err
import benchengine.user.team.manager as role


class TeamApi(object):
    """Implement methods that allow to create and modify teams and team member
    ships. For each team a folder on disk is maintained that contains uploaded
    files.

    The current user is always identified by the access token that is provided
    as argument to all methods.
    """
    def __init__(self, manager, base_dir, urls):
        """Initialize the components of the team API.

        Parameters
        ----------
        manager: benchengine.user.team.manager.TeamManager
            Manager for all teams in the database
        base_dir: string
            Path to the base directory to store uploaded files
        urls: benchengine.api.route.UrlFactory
            Factory for API resource Urls
        """
        self.manager = manager
        self.urls = urls
        self.base_dir = base_dir
        self.serialize = TeamSerializer(urls)

    def add_members(self, team_id, members, access_token=None):
        """Add new members to a given team. Team members are identified by their
        unique user identifier If the access token is given it is verified that
        the associated user is the team owner.

        Parameters
        ----------
        team_id: string
            Unique team identifier
        members: list(string)
            List of unique user identifier
        access_token: string, optional
            User access token

        Returns
        -------
        dict

        Raises
        ------
        benchengine.error.UnauthenticatedAccessError
        benchengine.error.UnauthorizedAccessError
        benchengine.error.UnknownUserError
        benchengine.error.UnknownTeamError
        """
        # Get user identifier if access token is given. Ensure that user is the
        # team owner.
        user_id = None
        if not access_token is None:
            user_id = self.manager.authorize(
                access_token=access_token,
                team_id=team_id,
                role=role.OWNER
            )
        for member_id in members:
            self.manager.add_member(team_id=team_id, user_id=member_id)
        # Return serialized team handle
        team = self.manager.get_team(team_id)
        return self.serialize.team_handle(team, user_id=user_id)

    def create_team(self, access_token, name, members=None):
        """Create a new team with the given name. The team owner is the user
        that is associated with the given access token, Ensures that at least
        the team owner is added as a member to the new team.

        Parameters
        ----------
        access_token: string
            User access token
        name: string
            Unique team name
        members: list(string), optional
            List of team members

        Returns
        -------
        dict

        Raises
        ------
        benchengine.error.ConstraintViolationError
        benchengine.error.UnauthenticatedAccessError
        benchengine.error.UnknownUserError
        """
        owner = self.manager.authenticate(access_token)
        team = self.manager.create_team(
            name=name,
            owner_id=owner.identifier,
            members=members
        )
        return self.serialize.team_descriptor(team, user_id=owner.identifier)

    def delete_file(self, team_id, file_id, access_token=None):
        """Delete file with given identifier that was previously uploaded.

        Raises errors if the file or the team is unknown or the user is not
        authorized to delete the file.

        Parameters
        ----------
        team_id: string
            Unique team identifier
        file_id: string
            Unique file identifier
        access_token: string, optional
            User access token

        Returns
        -------
        dict

        Raises
        ------
        benchengine.error.UnauthenticatedAccessError
        benchengine.error.UnauthorizedAccessError
        benchengine.error.UnknownFileError
        benchengine.error.UnknownTeamError
        """
        # Ensure that the team exists
        self.manager.assert_team_exists(team_id)
        # If the access token is given, ensure that user is a team member.
        if not access_token is None:
            self.manager.authorize(
                access_token=access_token,
                team_id=team_id,
                role=role.MEMBER
            )
        # Delete file. If result is False (i.e., the file did not exist) an
        # error is raised
        fs = Filestore(os.path.join(self.base_dir, team_id))
        if not fs.delete_file(file_id):
            raise err.UnknownFileError(file_id)
        return self.serialize.success()

    def delete_team(self, team_id, access_token=None):
        """Delete the team with the given identifier. If an access token is
        given it is verified that the associated user is the team owner.

        Parameters
        ----------
        team_id: string
            Unique team identifier

        Returns
        -------
        dict

        Raises
        ------
        benchengine.error.UnauthenticatedAccessError
        benchengine.error.UnauthorizedAccessError
        benchengine.error.UnknownTeamError
        """
        # Get user identifier if access token is given. Ensure that user is the
        # team owner.
        if not access_token is None:
            self.manager.authorize(
                access_token=access_token,
                team_id=team_id,
                role=role.OWNER
            )
        self.manager.delete_team(team_id)
        return self.serialize.success()

    def get_file(self, team_id, file_id, access_token=None):
        """Get handle for file with given identifier that was uploaded by the
        team.

        Parameters
        ----------
        team_id: string
            Unique team identifier
        file_id: string
            Unique file identifier
        access_token: string, optional
            User access token

        Returns
        -------
        dict

        Raises
        ------
        benchengine.error.UnauthenticatedAccessError
        benchengine.error.UnauthorizedAccessError
        benchengine.error.UnknownFileError
        benchengine.error.UnknownTeamError
        """
        # Ensure that the team exists
        self.manager.assert_team_exists(team_id)
        # If the access token is given, ensure that user is a team member.
        if not access_token is None:
            self.manager.authorize(
                access_token=access_token,
                team_id=team_id,
                role=role.MEMBER
            )
        # Get serialized file handle. Raise error if the file does not exist.
        fh = Filestore(os.path.join(self.base_dir, team_id)).get_file(file_id)
        if fh is None:
            raise err.UnknownFileError(file_id)
        return self.serialize.file_handle(fh=fh, team_id=team_id)

    def get_team(self, team_id, access_token=None):
        """Get handle for team with given identifier. If the access token is
        given it is confirmed that the user is a member of the team.

        The option of calling this method without the access token is not
        intended to be exposed via a web API. It's main purpose is to allow
        an adminstrator to view any teams via the command line interface.

        Parameters
        ----------
        team_id: string
            Unique team identifier
        access_token: string, optional
            User access token

        Returns
        -------
        dict

        Raises
        ------
        benchengine.error.UnauthenticatedAccessError
        benchengine.error.UnauthorizedAccessError
        benchengine.error.UnknownTeamError
        """
        # Get user identifier if access token is given. Ensure that the user is
        # at least a team member
        user_id = None
        if not access_token is None:
            user_id = self.manager.authorize(
                access_token=access_token,
                team_id=team_id,
                role=role.MEMBER
            )
        team = self.manager.get_team(team_id)
        return self.serialize.team_handle(team, user_id=user_id)

    def list_teams(self, access_token=None):
        """Get a listing of all teams that a user is a member of. If the token
        is omitted the list of all teams is returned.

        Parameters
        ----------
        access_token: string, optional
            User access token

        Returns
        -------
        dict

        Raises
        ------
        benchengine.error.UnauthenticatedAccessError
        """
        # Get the identifier for the registered user that is associated with the
        # access token if given
        user_id = None
        if not access_token is None:
            user_id = self.manager.authenticate(access_token).identifier
        # Return serialized team listing
        teams = self.manager.list_teams(user_id=user_id)
        return self.serialize.team_listing(teams, user_id=user_id)

    def remove_member(self, team_id, member_id, access_token=None):
        """Remove a user as a member from a given team. If the access token is
        given it is ensured that the associated user is the team owner.

        Parameters
        ----------
        team_id: string
            Unique team identifier
        member_id: string
            Unique user identifier
        access_token: string, optional
            User access token

        Returns
        -------
        dict

        Raises
        ------
        benchengine.error.ConstraintViolationError
        benchengine.error.UnauthenticatedAccessError
        benchengine.error.UnauthorizedAccessError
        benchengine.error.UnknownTeamError
        """
        # Get user identifier if access token is given. Ensure that user is
        # either the team owner or a team member that matches the member id.
        # Team members can remove themselves from a team but not any other
        # team member.
        user_id = None
        if not access_token is None:
            user_id = self.manager.authorize(
                access_token=access_token,
                team_id=team_id,
                role=role.OWNER_OR_SELF,
                member_id=member_id
            )

        self.manager.remove_member(team_id=team_id, user_id=member_id)
        # Return serialized team handle
        team = self.manager.get_team(team_id)
        return self.serialize.team_handle(team, user_id=user_id)

    def update_team_name(self, team_id, name, access_token=None):
        """Update the name for the team with the given identifier. The access
        token is optional to allow a super user to change team names from the
        command line interface without the need to be a team owner. A web
        service implementation should always ensure that an access token is
        given.

        Parameters
        ----------
        team_id: string
            Unique team identifier
        name: string
            Unique team name
        access_token: string, optional
            User access token

        Returns
        -------
        dict

        Raises
        ------
        benchengine.error.ConstraintViolationError
        benchengine.error.UnauthenticatedAccessError
        benchengine.error.UnauthorizedAccessError
        benchengine.error.UnknownTeamError
        """
        # Get user identifier if access token is given. Ensure that user is the
        # team owner.
        user_id = None
        if not access_token is None:
            user_id = self.manager.authorize(
                access_token=access_token,
                team_id=team_id,
                role=role.OWNER
            )
        team = self.manager.update_team_name(team_id, name)
        return self.serialize.team_descriptor(team, user_id=user_id)

    def upload_file(self, file, file_name, team_id, access_token=None):
        """Create a new entry from a given file stream. Will copy the given
        file to a file in the base directory.

        Parameters
        ----------
        file: werkzeug.datastructures.FileStorage
            File object (e.g., uploaded via HTTP request)
        file_name: string
            Name of the file
        team_id: string
            Unique team identifier
        access_token: string, optional
            User access token

        Returns
        -------
        benchengine.filestore.base.FileHandle
        """
        # Ensure that the team exists
        self.manager.assert_team_exists(team_id)
        # If the access token is given, ensure that user is a team member.
        if not access_token is None:
            self.manager.authorize(
                access_token=access_token,
                team_id=team_id,
                role=role.MEMBER
            )
        # Store file and return serialized file handle.
        fs = Filestore(os.path.join(self.base_dir, team_id))
        fh = fs.upload_stream(file=file, file_name=file_name)
        return self.serialize.file_handle(fh=fh, team_id=team_id)
