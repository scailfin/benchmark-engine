# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""Interface to serialize benchmark resource objects."""


from benchengine.api.serialize.base import Serializer

import benchengine.api.serialize.hateoas as hateoas
import benchengine.api.serialize.labels as labels


class BenchmarkSerializer(Serializer):
    """Serializer for benchmark resource objects. Defines the methods that are
    used to serialize benchmark descriptors and handles.
    """
    def __init__(self, urls):
        """Initialize the reference to the Url factory.

        Parameters
        ----------
        urls: benchengine.api.route.UrlFactory
            Factory for resource urls
        """
        super(BenchmarkSerializer, self).__init__(urls)

    def benchmark_descriptor(self, benchmark):
        """Get dictionary serialization containing the descriptor of a
        benchmark resource.

        Parameters
        ----------
        benchmark: benchengine.benchmark.base.BenchmarkDescriptor
            Competition handle

        Returns
        -------
        dict
        """
        benchmark_id = benchmark.identifier
        leaderboard_url = self.urls.get_leaderboard(benchmark_id)
        obj = {
            labels.ID: benchmark_id,
            labels.NAME: benchmark.name,
            labels.LINKS: hateoas.serialize({
                hateoas.SELF: self.urls.get_benchmark(benchmark_id),
                hateoas.benchmark(hateoas.LEADERBOARD): leaderboard_url
            })
        }
        if benchmark.has_description():
            obj[labels.DESCRIPTION] = benchmark.description
        if benchmark.has_instructions():
            obj[labels.INSTRUCTIONS] = benchmark.instructions
        return obj

    def benchmark_handle(self, benchmark):
        """Get dictionary serialization containing the handle of a
        benchmark resource.

        Parameters
        ----------
        benchmark: enataengine.benchmark.base.BenchmarkHandle
            Handle for benchmark resource

        Returns
        -------
        dict
        """
        obj = self.benchmark_descriptor(benchmark)
        # Add parameter declarations to the serialized benchmark descriptor
        obj[labels.PARAMETERS] = [p.to_dict() for p in benchmark.template.parameters.values()]
        return obj

    def benchmark_leaderboard(self, benchmark, leaderboard):
        """Get dictionary serialization for a benchmark leaderboard.

        Parameters
        ----------
        benchmark: enataengine.benchmark.base.BenchmarkHandle
            Handle for benchmark resource
        leaderboard: list(benchengine.benchmark.base.LeaderboardEntry)
            List of entries in the benchmark leaderboard

        Returns
        -------
        dict
        """
        runs = list()
        for run in leaderboard:
            results = list()
            for key in run.results:
                results.append({labels.ID: key, labels.VALUE: run.results[key]})
            runs.append({
                labels.USERNAME: run.user.username,
                labels.RESULTS: results
            })
        return {
            labels.SCHEMA: [{
                    labels.ID: c.identifier,
                    labels.NAME: c.name,
                    labels.DATA_TYPE: c.data_type
                } for c in benchmark.template.schema.columns
            ],
            labels.RUNS: runs
        }

    def benchmark_listing(self, benchmarks):
        """Get dictionary serialization of a benchmark listing.

        Parameters
        ----------
        benchmarks: list(benchengine.benchmark.base.BenchmarkDescriptor)
            List of benchmark descriptors

        Returns
        -------
        dict
        """
        return {
            labels.BENCHMARKS: [self.benchmark_descriptor(b) for b in benchmarks],
            labels.LINKS: hateoas.serialize({
                hateoas.SELF: self.urls.list_benchmarks()
            })
        }

    def benchmark_run(self, benchmark_id, run_id, state):
        """Get dictionary serialization for the current state of a benchmark
        run.

        Parameters
        ----------
        benchmark_id: string
            Unique benchmark identifier
        run_id: string
            Unique run identifier
        state: benchtmpl.workflow.state.WorkflowState
            Current run state

        Returns
        -------
        dict
        """
        obj = {
            labels.ID: run_id,
            labels.STATE: state.type_id
        }
        # If the workflow is not in pending mode it has a started_at timestamp
        if not state.is_pending():
            obj[labels.STARTED_AT] = state.started_at.isoformat()
        # If the workflow is not active it has a finished_at timestamp
        if not state.is_active():
            obj[labels.FINISHED_AT] = state.finished_at.isoformat()
        # If the workflow is in error state it has a list of error messages
        if state.is_error():
            obj[labels.MESSAGES] = state.messages
        return obj
