"""The team manager class provides methods to create and maintain information
about teams that participate in competitions.
"""

from benchengine.user.team.base import TeamDescriptor, TeamHandle
from benchengine.user.auth import Auth
from benchengine.user.base import RegisteredUser

import benchengine.error as err
import benchtmpl.util.core as util


"""Roles that a user can have for a team. Used for authorization."""
MEMBER = 'MEMBER'
OWNER = 'OWNER'
OWNER_OR_SELF = 'OWNER_OR_SELF'


class TeamManager(Auth):
    """Team information is maintaine in the database. The team manager provides
    the methods that are used to create, maintain, and query team information.
    """
    def __init__(self, con):
        """The team manager is initialized by providing an open connection to
        the database that contains team information.

        Parameters
        ----------
        con: DB-API 2.0 database connection
            Connection to underlying database
        """
        super(TeamManager, self).__init__(con)

    def add_member(self, team_id, user_id):
        """Add a new member to the given team.

        Parameters
        ----------
        team_id: string
            Unique team identifier
        user_id: string
            Unique user identifier

        Raises
        ------
        benchengine.error.DuplicateUserError
        benchengine.error.UnknownTeamError
        benchengine.error.UnknownUserError
        """
        # Validate that the team and user exist. Raises exception if either
        #  does not exist.
        self.assert_team_exists(team_id)
        self.assert_user_exists(user_id)
        # Ensure that the user is not alreay a member of the team
        sql = 'SELECT * FROM team_member WHERE team_id = ? AND user_id = ?'
        if not self.con.execute(sql, (team_id, user_id)).fetchone() is None:
            raise err.DuplicateUserError(user_id)
        # Add team member and commit changes
        sql = 'INSERT INTO team_member(team_id, user_id) VALUES(?, ?)'
        self.con.execute(sql, (team_id, user_id))
        self.con.commit()

    def assert_team_exists(self, team_id):
        """Ensure that a team with the given identifier exists. If the team
        does not exist an UnknownTeam exception is raised.

        Parameters
        ----------
        team_id: string
            Unique team identifier

        Raises
        ------
        benchengine.error.UnknownTeamError
        """
        result = self.con.execute(
            'SELECT id FROM team WHERE id = ?', (team_id,)
        ).fetchone()
        if result is None:
            raise err.UnknownTeamError(team_id)

    def assert_user_exists(self, user_id):
        """Ensure that a user with the given identifier exists. If the user
        does not exist an UnknownUser exception is raised.

        Parameters
        ----------
        user_id: string
            Unique user identifier

        Raises
        ------
        benchengine.error.UnknownUserError
        """
        result = self.con.execute(
            'SELECT id FROM registered_user WHERE id = ? AND active = 1',
            (user_id,)
        ).fetchone()
        if result is None:
            raise err.UnknownUserError(user_id)

    def authorize(self, access_token, team_id, role=None, member_id=None):
        """Get the identifier for the user that is associated with the given
        access token. Authorize the users role in the given team (if role is
        not None).

        If the required role is 'OWNER_OR_SELF' the user identifier that is
        associated with the access token is compared against the optional
        member id argument. If both are equal it is sufficient for the user
        to be a team member. Otherwise, the user is required to be the team
        owner.

        Parameters
        ----------
        access_token: string
            User access token
        team_id: string
            Unique team identifier
        role: string, optional
            Required team role for user
        member_id: string, optional
            Optional member identifier for 'OWNER_OR_SELF' role

        Returns
        -------
        string

        Raises
        ------
        benchengine.error.UnauthenticatedAccessError
        benchengine.error.UnauthorizedAccessError
        """
        # Get user identifier
        user_id = self.authenticate(access_token).identifier
        # Ensure that the user has the required role
        if role == OWNER or (role == OWNER_OR_SELF and user_id != member_id):
            if not self.is_team_owner(user_id=user_id, team_id=team_id):
                raise err.UnauthorizedAccessError()
        elif role == MEMBER or (role == OWNER_OR_SELF and user_id == member_id):
            if not self.is_team_member(user_id=user_id, team_id=team_id):
                raise err.UnauthorizedAccessError()
        return user_id

    def create_team(self, name, owner_id, members=None):
        """Create a new team with the given name. Ensures that at least the team
        owner is added as a member to the new team.

        Parameters
        ----------
        name: string
            Unique team name
        owner_id: string
            Unique user identifier for team owner
        members: list(string), optional
            List of team members

        Returns
        -------
        benchengine.user.team.base.TeamDescriptor

        Raises
        ------
        benchengine.error.ConstraintViolationError
        benchengine.error.UnknownUserError
        """
        # Ensure that the owner exists and all team members exist. Will raise
        # exception if user is unknown.
        self.assert_user_exists(owner_id)
        if not members is None:
            for user_id in set(members):
                if not user_id == owner_id:
                    self.assert_user_exists(user_id)
        # Ensure that the given team name is uniqe and does not contain too many
        # characters
        sql = 'SELECT * FROM team WHERE name = ?'
        if name is None or name.strip() == '':
            raise err.ConstraintViolationError('missing team name')
        elif len(name.strip()) > 255:
            raise err.ConstraintViolationError('team name contains more than 255 character')
        elif not self.con.execute(sql, (name.strip(),)).fetchone() is None:
            raise err.ConstraintViolationError('team name \'{}\' exists'.format(name.strip()))
        # Get unique identifier for the new team.
        team_id = util.get_unique_identifier()
        # Create the new team and add team members. Ensure that at least the
        # team owner is added as a team member.
        sql = 'INSERT INTO team_member(team_id, user_id) VALUES(?, ?)'
        self.con.execute(
            'INSERT INTO team(id, name, owner_id) VALUES(?, ?, ?)',
            (team_id, name.strip(), owner_id)
        )
        self.con.execute(sql, (team_id, owner_id))
        member_count = 1
        if not members is None:
            for user_id in set(members):
                if not user_id == owner_id:
                    self.con.execute(sql, (team_id, user_id))
                    member_count += 1
        self.con.commit()
        # Return team descriptor
        return TeamDescriptor(
            identifier=team_id,
            name=name,
            owner_id=owner_id,
            member_count=member_count
        )

    def delete_team(self, team_id):
        """Delete the team with the given identifier. Raises an exception if the
        given team is unknown.

        Parameters
        ----------
        team_id: string
            Unique team identifier

        Raises
        ------
        benchengine.error.UnknownTeamError
        """
        # Ensure that the team exists. Raises error if team does not exist.
        self.assert_team_exists(team_id)
        # First delete all team members. Delete the team record at the end to
        # avoid foreign key reference errors.
        sql = 'DELETE FROM team_member WHERE team_id = ?'
        self.con.execute(sql, (team_id,))
        sql = 'DELETE FROM team WHERE id = ?'
        self.con.execute(sql, (team_id,))
        self.con.commit()

    def get_team(self, team_id):
        """Get handle for the team with the given identifier. Raises exception
        if no team with the given identifier exists.

        Parameters
        ----------
        team_id: string
            Unique team identifier

        Returns
        -------
        benchengine.user.team.base.TeamHandle

        Raises
        ------
        benchengine.error.UnknownTeamError
        """
        # Get team information. Raise error if no team with given identifier
        # exists
        sql = 'SELECT name, owner_id FROM team WHERE id = ?'
        team = self.con.execute(sql, (team_id,)).fetchone()
        if team is None:
            raise err.UnknownTeamError(team_id)
        # Get handles for team members
        members = dict()
        sql = 'SELECT u.id, u.email '
        sql += 'FROM registered_user u, team_member t '
        sql += 'WHERE u.id = t.user_id AND t.team_id = ?'
        for row in self.con.execute(sql, (team_id,)).fetchall():
            user = RegisteredUser(identifier=row['id'], email=row['email'])
            members[user.identifier] = user
        return TeamHandle(
            identifier=team_id,
            name=team['name'],
            owner_id=team['owner_id'],
            members=members
        )

    def list_teams(self, user_id=None):
        """Get a list of all teams that are currently in the database. The
        optional user identifier allows to list only those teams which the given
        user is a member of. If the value is None all teams in the database are
        returned.

        Parameters
        ----------
        user_id: string, optional
            Unique user identifier

        Returns
        -------
        list(benchengine.user.team.base.TeamDescriptor)
        """
        # Create initial query with placeholder for the table that the teams
        # are selected from.
        sql = 'SELECT t.id, t.name, t.owner_id, COUNT(*) as member '
        sql += 'FROM {} t, team_member m WHERE t.id = m.team_id '
        sql += 'GROUP BY t.id, t.name, t.owner_id'
        # Depending on whether the user id is given the teams are either
        # taken directly from the teams table of a sub-query that filters
        # teams that the user is member of.
        if not user_id is None:
            team_table = 'SELECT id, name, owner_id FROM team t1, team_member m1 '
            team_table += 'WHERE t1.id = m1.team_id AND m1.user_id = ?'
            team_table = '(' + team_table + ')'
            bindings = (user_id,)
        else:
            team_table = 'team'
            bindings = ()
        sql = sql.format(team_table)
        result = list()
        for team in self.con.execute(sql, bindings).fetchall():
            result.append(
                TeamDescriptor(
                    identifier=team['id'],
                    name=team['name'],
                    owner_id=team['owner_id'],
                    member_count=team['member']
                )
            )
        return result

    def remove_member(self, team_id, user_id):
        """Remove the given user as member of the given team. Raises error if
        the team is unknown or if the user is the team owner. No error is raised
        if the user is unknown or not a team member.

        Parameters
        ----------
        team_id: string
            Unique team identifier
        user_id: string
            Unique user identifier

        Raises
        ------
        benchengine.error.ConstraintViolationError
        benchengine.error.UnknownTeamError
        """
        # Ensure that the team exists. Raises error if team does not exist.
        # If the user is the team owner the constraint that the owner has to be
        # a team member is violated.
        sql = 'SELECT owner_id FROM team WHERE id = ?'
        team = self.con.execute(sql, (team_id,)).fetchone()
        if team is None:
            raise err.UnknownTeamError(team_id)
        elif team['owner_id'] == user_id:
            raise err.ConstraintViolationError('cannot remove team owner')
        sql = 'DELETE FROM team_member WHERE team_id = ? AND user_id = ?'
        self.con.execute(sql, (team_id, user_id))
        self.con.commit()

    def update_team_name(self, team_id, name):
        """Update the name of the team with the given identifier. Will raise
        errors if the team is unknown or the name is invalid or not unique.

        Parameters
        ----------
        team_id: string
            Unique team identifier
        name: string
            New unique team name

        Returns
        -------
        benchengine.user.team.base.TeamHandle

        Raises
        ------
        benchengine.error.ConstraintViolationError
        benchengine.error.UnknownTeamError
        """
        # Ensure that the team exists. Raises error if team does not exist.
        self.assert_team_exists(team_id)
        # Ensure that no other team has the same name
        sql = 'SELECT * FROM team WHERE id <> ? AND name = ?'
        if len(name.strip()) > 255:
            raise err.ConstraintViolationError('team name contains more than 255 character')
        elif not self.con.execute(sql, (team_id, name)).fetchone() is None:
            raise err.ConstraintViolationError('team name \'{}\' exists'.format(name.strip()))
        # Update the team name
        sql = 'UPDATE team SET name = ? WHERE id = ?'
        self.con.execute(sql, (name, team_id))
        self.con.commit()
        # Return the handle for the team
        return self.get_team(team_id)
