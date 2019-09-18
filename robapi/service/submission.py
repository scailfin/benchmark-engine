# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""Implementation of API methods that access and manipulate benchmark
submissions and their results.
"""

from robapi.model.auth import SUBMISSION as RESOURCE_TYPE
from robapi.serialize.submission import SubmissionSerializer
from robapi.service.route import UrlFactory

import robapi.error as err


class SubmissionService(object):
    """API component that provides methods to access benchmark submissions and
    their runs.
    """
    def __init__(self, manager, auth, urls=None, serializer=None):
        """Initialize the internal reference to the submission manager and to
        the route factory.

        Parameters
        ----------
        manager: robapi.model.submission.SubmissionManager
            Manager for benchmark submissions
        auth: robapi.model.auth.Auth
            Implementation of the authorization policy for the API
        urls: robapi.service.route.UrlFactory
            Factory for API resource Urls
        serializer: robapi.serialize.submission.SubmissionSerializer, optional
            Override the default serializer
        """
        self.manager = manager
        self.auth = auth
        self.urls = urls if not urls is None else UrlFactory()
        self.serialize = serializer
        if self.serialize is None:
            self.serialize = SubmissionSerializer(self.urls)

    def create_submission(self, benchmark_id, name, user, members=None):
        """Create a new submission for a given benchmark. Each submission for
        the benchmark has a unique name, a submission owner, and a list of
        additional submission members.

        Parameters
        ----------
        benchmark_id: string
            Unique benchmark identifier
        name: string
            Unique team name
        user: robapi.model.user.UserHandle
            Handle for the submission owner
        members: list(string), optional
            List of user identifier for submission members

        Returns
        -------
        dict

        Raises
        ------
        robapi.error.ConstraintViolationError
        robapi.error.UnknownBenchmarkError
        """
        submission = self.manager.create_submission(
            benchmark_id=benchmark_id,
            name=name,
            user_id=user.identifier,
            members=members
        )
        return self.serialize.submission_handle(submission)

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
        robapi.error.UnauthenticatedAccessError
        robapi.error.UnauthorizedAccessError
        robapi.error.UnknownFileError
        robapi.error.UnknownTeamError
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

    def delete_submission(self, submission_id, user):
        """Get a given submission and all associated runs and results. If the
        user is not an administrator or a member of the submission an
        unauthorized access error is raised.

        Returns a listing of the remaining submissions that the user is a
        member of.

        Parameters
        ----------
        submission_id: string
            Unique submission identifier
        user: robapi.model.user.UserHandle
            Handle for user that is deleting the submission

        Returns
        -------
        dict

        Raises
        ------
        robapi.error.UnauthorizedAccessError
        robapi.error.UnknownSubmissionError
        """
        # Raise an error if the user is not authorized to delete the submission
        if not self.auth.can_delete(RESOURCE_TYPE, submission_id, user):
            raise err.UnauthorizedAccessError()
        self.manager.delete_submission(submission_id)
        return self.list_submissions(user)

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
        robapi.error.UnauthenticatedAccessError
        robapi.error.UnauthorizedAccessError
        robapi.error.UnknownFileError
        robapi.error.UnknownTeamError
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

    def get_submission(self, submission_id, user):
        """Get handle for submission with the given identifier. If the user is
        not an administrator or a member of the submission an unauthorized
        access error is raised.

        Parameters
        ----------
        submission_id: string
            Unique submission identifier
        user: robapi.model.user.UserHandle
            Handle for user that is accessing the submission

        Returns
        -------
        dict

        Raises
        ------
        robapi.error.UnknownSubmissionError
        """
        submission = self.manager.get_submission(submission_id)
        return self.serialize.submission_handle(submission)

    def list_submissions(self, user):
        """Get a listing of all submissions that a user is a member of.

        Parameters
        ----------
        user: robapi.model.user.UserHandle
            Handle for user that is requesting the submission listing

        Returns
        -------
        dict
        """
        submissions = self.manager.list_submissions(user=user)
        return self.serialize.submission_listing(submissions)

    def update_submission(self, submission_id, user, name=None, members=None):
        """Update the name for the team with the given identifier. The access
        token is optional to allow a super user to change team names from the
        command line interface without the need to be a team owner. A web
        service implementation should always ensure that an access token is
        given.

        Parameters
        ----------
        submission_id: string
            Unique submission identifier
        user: robapi.model.user.UserHandle
            Handle for user that is accessing the submission
        name: string, optional
            New submission name
        members: list(string), optional
            Modified list of team members

        Returns
        -------
        dict

        Raises
        ------
        robapi.error.ConstraintViolationError
        robapi.error.UnauthorizedAccessError
        robapi.error.UnknownSubmissionError
        """
        # Raise an error if the user is not authorized to modify the submission
        if not self.auth.can_modify(RESOURCE_TYPE, submission_id, user):
            raise err.UnauthorizedAccessError()
        submission = self.manager.update_submission(
            submission_id,
            name=name,
            members=members
        )
        return self.serialize.submission_handle(submission)

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
        robapi.filestore.base.FileHandle
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
