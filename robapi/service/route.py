# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""Factory for Urls to access and manipulate API resources."""

import robapi.config.api as config


class UrlFactory(object):
    """The Url factory provides methods to generate API urls to access and
    manipulate resources. For each API route there is a corresponding factory
    method to generate the respective Url.
    """
    def __init__(self, base_url=None):
        """Initialize the base Url for the service API. If the argument is not
        given the value is expcted in the environment variable
        'robapi_API_BASEURL'.

        Parameters
        ----------
        base_url: string
            Base Url for all API resources
        """
        # Set base Url depending on whether it is given as argument or not
        if base_url is None:
            self.base_url = config.API_URL()
        else:
            self.base_url = base_url
        # Remove trailing '/' from the base url
        while self.base_url.endswith('/'):
            self.base_url = self.base_url[:-1]
        # Set base Url for resource related requests
        self.benchmark_base_url = self.base_url + '/benchmarks'
        self.submission_base_url = self.base_url + '/submissions'
        self.user_base_url = self.base_url + '/users'

    def activate_user(self):
        """Url to POST user activation request for newly registered users.

        Returns
        -------
        string
        """
        return self.user_base_url + '/activate'

    def add_team_members(self, team_id):
        """Url to POST list of new team members.

        Parameters
        ----------
        team_id: string
            Unique team identifier

        Returns
        -------
        string
        """
        return self.get_team(team_id) + '/members'

    def delete_file(self, submission_id, file_id):
        """Url to DELETE a previously uploaded file.

        Parameters
        ----------
        submission_id: string
            Unique submission identifier
        file_id: string
            Unique file identifier

        Returns
        -------
        string
        """
        return self.list_files(submission_id) + '/' + file_id

    def download_file(self, submission_id, file_id):
        """Url to GET a previously uploaded file.

        Parameters
        ----------
        submission_id: string
            Unique submission identifier
        file_id: string
            Unique file identifier

        Returns
        -------
        string
        """
        return self.list_files(submission_id) + '/' + file_id

    def get_benchmark(self, benchmark_id):
        """Url to GET benchmark handle.

        Parameters
        ----------
        benchmark_id: string
            Unique benchmark identifier

        Returns
        -------
        string
        """
        return self.benchmark_base_url + '/' + benchmark_id

    def get_leaderboard(self, benchmark_id):
        """Url to GET benchmark leaderboard.

        Parameters
        ----------
        benchmark_id: string
            Unique benchmark identifier

        Returns
        -------
        string
        """
        return self.get_benchmark(benchmark_id) + '/leaderboard'

    def get_submission(self, submission_id):
        """Url to GET submission handle.

        Parameters
        ----------
        submission_id: string
            Unique submission identifier

        Returns
        -------
        string
        """
        return self.submission_base_url + '/' + submission_id

    def list_benchmarks(self):
        """Url to GET a list of all benchmarks.

        Returns
        -------
        string
        """
        return self.benchmark_base_url

    def list_files(self, submission_id):
        """Url to GET listing of all uploaded files for a given submission.

        Parameters
        ----------
        submission_id: string
            Unique submission identifier

        Returns
        -------
        string
        """
        return self.get_submission(submission_id) + '/files'

    def list_submissions(self):
        """Url to GET list of submissions that a user is a memebr of.

        Returns
        -------
        string
        """
        return self.submission_base_url

    def list_users(self):
        """Url to GET listing of registered users.

        Returns
        -------
        string
        """
        return self.user_base_url

    def login(self):
        """Url to POST user credentials for login.

        Returns
        -------
        string
        """
        return self.user_base_url + '/login'

    def logout(self):
        """Url to POST user logout request.

        Returns
        -------
        string
        """
        return self.user_base_url + '/logout'

    def register_user(self):
        """Url to POST registration request for new users.

        Returns
        -------
        string
        """
        return self.user_base_url + '/register'

    def remove_team_member(self, team_id, user_id):
        """Url to DELETE a member for a team.

        Parameters
        ----------
        team_id: string
            Unique team identifier
        user_id: string
            Unique user identifier

        Returns
        -------
        string
        """
        return self.add_team_members(team_id) + '/' + user_id

    def service_descriptor(self):
        """Url to GET the service descriptor.

        Returns
        -------
        string
        """
        return self.base_url

    def team_files(self, team_id):
        """Base Url to access uploaded files for a given team.

        Parameters
        ----------
        team_id: string
            Unique team identifier

        Returns
        -------
        string
        """
        return self.get_team(team_id) + '/files'

    def upload_file(self, team_id):
        """Url to POST a new file to upload. The uploaded file is associated
        with the given team.


        Parameters
        ----------
        team_id: string
            Unique team identifier
        file_id: string
            Unique file identifier

        Returns
        -------
        string
        """
        return self.team_files(team_id) + '/upload'

    def whoami(self):
        """Url to GET information about a user that is logged in.

        Returns
        -------
        string
        """
        return self.user_base_url + '/whoami'
