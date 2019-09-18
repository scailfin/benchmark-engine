# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""Benchmark engine used to execute benchmarks for a given set of arguments.
This implementation of the engine executes all workflows synchronously. It is
primarily intended for test purposes and NOT for production systems.
"""

import os

import benchtmpl.util.core as util


class BenchmarkEngine(object):
    """Benchmark engine to execute benchmark workflows for a given set of
    argument values. All workflows are executed synchronously. After a workflow
    completes successfully the results are parsed and entered into the reuslt
    table of the benchmark.
    """
    def __init__(self, con, backend):
        """Initialize the connection to the databases that contains the
        benchmark result tables and the workflow execution backend.

        Parameters
        ----------
        con: DB-API 2.0 database connection
            Connection to underlying database
        backend: benchtmpl.backend.base.WorkflowEngine
            Workflow engine that is used to run benchmarks
        """
        self.con = con
        self.backend = backend

    def run(self, benchmark, arguments, user_id):
        """Run benchmark for given set of arguments. Returns the identifier of
        the created run and the resulting workflow run state.

        Parameters
        ----------
        benchmark: benchengine.benchmark.base.BenchmarkHandle
            Handle for benchmark that is being executed
        arguments: dict(benchtmpl.workflow.parameter.value.TemplateArgument)
            Dictionary of argument values for parameters in the template

        Returns
        -------
        string, benchtmpl.workflow.state.WorkflowState

        Raises
        ------
        benchtmpl.error.MissingArgumentError
        """
        # Execute the benchmark workflow for the given set of arguments.
        run_id, state = backend.execute(
            template=benchmark.template,
            arguments=arguments
        )
        # Insert run info and run results into database. The run results are
        # only available if case of a successful run.
        if state.is_success():
            fh = state.resources[benchmark.template.schema.result_file_id]
            results = util.read_object(fh.filepath)
            benchmark.insert_results(run_id=run_id, results=results)
        sql = 'INSERT INTO benchmark_run('
        sql += 'run_id, benchmark_id, user_id, state, created_at, started_at, ended_at'
        sql += ') VALUES(?, ?, ?, ?, ?, ?, ?)'
        s_type = state.type_id
        t_start = state.started_at.isoformat()
        if not state.is_active():
            t_end = state.finished_at.isoformat()
        else:
            t_end = None
        self.con.execute(sql, (run_id, benchmark.identifier, user_id, s_type, t_start, t_end))
        self.con.commit()
        return run_id, state
