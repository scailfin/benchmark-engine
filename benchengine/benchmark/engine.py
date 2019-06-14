"""Benchmark engine used to execute benchmarks for a given set of arguments.
This implementation of the engine executes all workflows synchronously. It is
promarily intended for test purposes and NOT for production systems.
"""

import os

from benchtmpl.backend.multiprocess.engine import MultiProcessWorkflowEngine

import benchengine.config as config
import benchtmpl.util.core as util


class BenchmarkEngine(object):
    """Benchmark engine to execute benchmark workflows for a given set of
    argument values. All workflows are executed synchronously. After a workflow
    completes successfully the results are parsed and entered into the reuslt
    table of the benchmark.
    """
    def __init__(self, con):
        """Initialize the connection to the databases that contains the
        benchmark result tables.

        Parameters
        ----------
        con: DB-API 2.0 database connection
            Connection to underlying database
        """
        self.con = con
        # Benchmark runs are stored in a subfolder within the respective
        # template directory. Keep track of the base directory for benchmark
        # templates. Create the directory if it does not exist.
        self.template_dir = config.get_template_dir()
        util.create_dir(self.template_dir)

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
        bmk_id = benchmark.identifier
        # Benchmark runs are stored in a subfolder within the respective
        # template directory. Create workflow engine for the given benchmark.
        runs_dir = os.path.join(self.template_dir, bmk_id, 'runs')
        backend = MultiProcessWorkflowEngine(base_dir=runs_dir)
        # Execute the benchmark workflow for the given set of arguments. In this
        # implementation all workflows are executed synchronously.
        run_id = backend.exec(
            template=benchmark.template,
            arguments=arguments,
            run_async=False,
            verbose=False
        )
        state = backend.get_state(run_id)
        # Insert run info and run results into database. The run results are
        # only available if case of a successful run.
        if state.is_success():
            fh = state.resources[benchmark.template.schema.result_file_id]
            results = util.read_object(fh.filepath)
            benchmark.insert_results(run_id=run_id, results=results)
        sql = 'INSERT INTO benchmark_run('
        sql += 'run_id, benchmark_id, user_id, state, started_at, finished_at'
        sql += ') VALUES(?, ?, ?, ?, ?, ?)'
        s_type = state.type_id
        t_start = state.started_at.isoformat()
        t_end = state.finished_at.isoformat()
        self.con.execute(sql, (run_id, bmk_id, user_id, s_type, t_start, t_end))
        self.con.commit()
        return run_id, state
