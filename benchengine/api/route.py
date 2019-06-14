"""Factory for Urls to access and manipulate API resources."""

import benchengine.config as config


class UrlFactory(object):
    """The Url factory provides methods to generate API urls to access and
    manipulate resources. For each API route there is a corresponding factory
    method to generate the respective Url.
    """
    def __init__(self, base_url=None):
        """Initialize the base Url for the service API. If the argument is not
        given the value is expcted in the environment variable
        'benchengine_API_BASEURL'.

        Parameters
        ----------
        base_url: string
            Base Url for all API resources
        """
        # Set base Url depending on whether it is given as argument or not
        if base_url is None:
            self.base_url = config.get_apiurl()
        else:
            self.base_url = base_url
        # Remove trailing '/' from the base url
        while self.base_url.endswith('/'):
            self.base_url = self.base_url[:-1]
        # Set base Url for resource related requests
        self.benchmark_base_url = self.base_url + '/benchmarks'
        self.team_base_url = self.base_url + '/teams'
        self.user_base_url = self.base_url + '/user'

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

    def delete_file(self, team_id, file_id):
        """Url to DELETE a previously uploaded file.

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
        return self.team_files(team_id) + '/' + file_id

    def download_file(self, team_id, file_id):
        """Url to GET a previously uploaded file.

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
        return self.team_files(team_id) + '/' + file_id + '/download'

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

    def get_team(self, team_id):
        """Url to GET team handle.

        Parameters
        ----------
        team_id: string
            Unique team identifier

        Returns
        -------
        string
        """
        return self.team_base_url + '/' + team_id

    def list_benchmarks(self):
        """Url to GET a list of all benchmarks.

        Returns
        -------
        string
        """
        return self.benchmark_base_url

    def list_teams(self):
        """Url to GET list of teams that a user is subscribed to and to POST a
        create team request.

        Returns
        -------
        string
        """
        return self.team_base_url

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
