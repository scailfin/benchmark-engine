# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""The benchmark API component provides methods to list and interact with
benchmarks in the repository.
"""

from benchengine.api.serialize.benchmark import BenchmarkSerializer


class BenchmarkApi(object):
    """API component that provides methods to interact with benchmarks in a
    given benchmark repository.
    """
    def __init__(self, repository, backend, urls):
        """Initialize the internal reference to the benchmark repository and
        the Url factory.

        Parameters
        ----------
        repository: benchengine.benchmark.repo.BenchmarkRepository
            Repository to access registered benchmarks
        backend: benchengine.benchmark.engine.BenchmarkEngine
            Workflow execution backend
        urls: benchengine.api.route.UrlFactory
            Factory for API resource Urls
        """
        self.repository = repository
        self.backend = backend
        self.urls = urls
        self.serialize = BenchmarkSerializer(urls)

    def get_benchmark(self, benchmark_id, access_token=None):
        """Get serialization of the handle for the given benchmark.

        Parameters
        ----------
        benchmark_id: string
            Unique benchmark identifier
        access_token: string, optional
            User access token

        Returns
        -------
        dict

        Raises
        ------
        benchengine.error.UnauthenticatedAccessError
        benchengine.error.UnauthorizedAccessError
        benchengine.error.UnknownBenchmarkError
        benchengine.error.UnknownTeamError
        """
        # Authenticate the user for the given access token. This is to ensure
        # that the access token is valid. The user information is no further
        # used by this method.
        if not access_token is None:
            self.repository.authenticate(access_token)
        # Return serialized benchmark handle
        benchmark = self.repository.get_benchmark(benchmark_id)
        return self.serialize.benchmark_handle(benchmark)

    def get_leaderboard(self, benchmark_id, sort_key=None, all_entries=False, access_token=None):
        """Get serialization of the handle for the given benchmark.

        Parameters
        ----------
        benchmark_id: string
            Unique benchmark identifier
        sort_key: string, optional
            Use the given attribute to sort entries in the leaderboard. If not
            given the benchmark schema default attribute is used.
        all_entries: bool, optional
            Include at most one entry per user in the leaderboard if False
        access_token: string, optional
            User access token

        Returns
        -------
        dict

        Raises
        ------
        benchengine.error.UnauthenticatedAccessError
        benchengine.error.UnauthorizedAccessError
        benchengine.error.UnknownBenchmarkError
        benchengine.error.UnknownTeamError
        """
        # Authenticate the user for the given access token. This is to ensure
        # that the access token is valid. The user information is no further
        # used by this method.
        if not access_token is None:
            self.repository.authenticate(access_token)
        # Return serialized benchmark handle
        benchmark = self.repository.get_benchmark(benchmark_id)
        return self.serialize.benchmark_leaderboard(
            benchmark,
            benchmark.get_leaderboard(
                sort_key=sort_key,
                all_entries=all_entries
            )
        )

    def list_benchmarks(self, access_token=None):
        """Get serialized listing of all benchmarks in the repository.

        Parameters
        ----------
        access_token: string, optional
            User access token

        Returns
        -------
        dict
        """
        # Authenticate the user for the given access token. This is to ensure
        # that the access token is valid. The user information is no further
        # used by this method.
        if not access_token is None:
            self.repository.authenticate(access_token)
        # Return serialized benchmark listing
        benchmarks = self.repository.list_benchmarks()
        return self.serialize.benchmark_listing(benchmarks)

    def run_benchmark(self, benchmark_id, arguments, access_token=None):
        """Run the specified benchmark for the given set of argument values.

        Parameters
        ----------
        benchmark_id: string
            Unique benchmark identifier
        arguments: dict
            Dictionary of argument values for parameters in the template
        access_token: string, optional
            User access token

        Returns
        -------
        dict

        Raises
        ------
        benchengine.error.UnauthenticatedAccessError
        benchengine.error.UnauthorizedAccessError
        benchengine.error.UnknownBenchmarkError
        benchtmpl.error.MissingArgumentError
        """
        # Authenticate the user for the given access token.
        user_id = None
        if not access_token is None:
            user_id = self.repository.authenticate(access_token).identifier
        # Get benchmark handle. This will raise an error if the benchmark
        # identifier is unknown.
        benchmark = self.repository.get_benchmark(benchmark_id)
        # Run the benchmark and return the serialized run identifier and the
        # current run status
        args = dict()
        for key in arguments:
            args[key] = benchmark.template.get_argument(key, arguments[key])
        run_id, state = self.backend.run(
            benchmark=benchmark,
            arguments=args,
            user_id=user_id
        )
        return self.serialize.benchmark_run(
            benchmark_id=benchmark.identifier,
            run_id=run_id,
            state=state
        )
