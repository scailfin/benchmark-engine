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

from robapi.serialize.submission import SubmissionSerializer
from robapi.service.route import UrlFactory

import robapi.error as err
import robapi.model.auth as res


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

    def delete_file(self, submission_id, file_id, user):
        """Delete file with given identifier that was previously uploaded.

        Raises errors if the file or the team is unknown or the user is not
        authorized to delete the file.

        Parameters
        ----------
        submission_id: string
            Unique submission identifier
        file_id: string
            Unique file identifier
        user: robapi.model.user.UserHandle
            Handle for user that requested the deletion

        Returns
        -------
        dict

        Raises
        ------
        robapi.error.UnauthorizedAccessError
        robapi.error.UnknownFileError
        """
        # Raise an error if the user does not have delete rights for the
        # submission
        if not self.auth.can_delete(res.FILE, submission_id, user):
            raise err.UnauthorizedAccessError()
        self.manager.delete_file(submission_id=submission_id, file_id=file_id)
        return self.list_files(submission_id=submission_id, user=user)

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
        if not self.auth.can_delete(res.SUBMISSION, submission_id, user):
            raise err.UnauthorizedAccessError()
        self.manager.delete_submission(submission_id)
        return self.list_submissions(user)

    def get_file(self, submission_id, file_id, user):
        """Get handle for file with given identifier that was uploaded by the
        team.

        Parameters
        ----------
        submission_id: string
            Unique submission identifier
        file_id: string
            Unique file identifier
        user: robapi.model.user.UserHandle
            Handle for user that is accessing the file

        Returns
        -------
        robtmpl.io.files.FileHandle, dict

        Raises
        ------
        robapi.error.UnauthorizedAccessError
        robapi.error.UnknownFileError
        """
        # Raise an error if the user does not have access rights for the
        # submission files
        if not self.auth.has_access(res.FILE, submission_id, user):
            raise err.UnauthorizedAccessError()
        # Return the file handle and of a serialization
        fh = self.manager.get_file(submission_id=submission_id, file_id=file_id)
        doc = self.serialize.file_handle(submission_id=submission_id, fh=fh)
        return fh, doc

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

    def list_files(self, submission_id, user):
        """Get a listing of all files that have been uploaded for the given
        submission.

        Parameters
        ----------
        submission_id: string
            Unique submission identifier
        user: robapi.model.user.UserHandle
            Handle for user that requested the deletion

        Returns
        -------
        dict

        Raises
        ------
        robapi.error.UnauthorizedAccessError
        robapi.error.UnknownSubmissionError
        """
        # Ensure that the user is authorized to retrieve the file listing for
        # the given submission
        if not self.auth.has_access(res.FILE, submission_id, user):
            raise err.UnauthorizedAccessError()
        files = self.manager.list_files(submission_id)
        return self.serialize.file_listing(
            submission_id=submission_id,
            files=files
        )

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
        if not self.auth.can_modify(res.SUBMISSION, submission_id, user):
            raise err.UnauthorizedAccessError()
        submission = self.manager.update_submission(
            submission_id,
            name=name,
            members=members
        )
        return self.serialize.submission_handle(submission)

    def upload_file(self, submission_id, file, file_name, user):
        """Create a file for a given submission.

        Parameters
        ----------
        file: werkzeug.datastructures.FileStorage
            File object (e.g., uploaded via HTTP request)
        file_name: string
            Name of the file
        submission_id: string
            Unique submission identifier
        user: robapi.model.user.UserHandle
            Handle for user that is uploading the file

        Returns
        -------
        dict

        Raises
        ------
        robapi.error.ConstraintViolationError
        robapi.error.UnauthorizedAccessError
        robapi.error.UnknownSubmissionError
        """
        # Ensure that the user is authorized to modify files for the given
        # submission
        if not self.auth.can_modify(res.FILE, submission_id, user):
            raise err.UnauthorizedAccessError()
        # Return serialization of the uploaded file
        fh = self.manager.upload_file(
            submission_id=submission_id,
            file=file,
            file_name=file_name
        )
        return self.serialize.file_handle(submission_id=submission_id, fh=fh)
