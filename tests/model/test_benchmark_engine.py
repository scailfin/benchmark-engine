# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""Test functionality of the benchmark engine."""

import os
import pytest

from passlib.hash import pbkdf2_sha256

from robapi.model.engine import BenchmarkEngine
from robapi.model.repo import BenchmarkRepository
from robapi.model.submission import SubmissionManager
from robapi.tests.benchmark import StateEngine
from robtmpl.template.schema import SortColumn
from robtmpl.template.repo.fs import TemplateFSRepository
from robtmpl.workflow.resource import FileResource
from robtmpl.workflow.state.base import StatePending, StateRunning

import robapi.error as err
import robapi.tests.benchmark as wf
import robapi.tests.db as db
import robtmpl.util as util


DIR = os.path.dirname(os.path.realpath(__file__))
TEMPLATE_DIR = os.path.join(DIR, '../.files/templates/helloworld')


USER_1 = util.get_unique_identifier()
USER_2 = util.get_unique_identifier()
USER_3 = util.get_unique_identifier()


class TestBenchmarkEngine(object):
    """Unit tests for getting and setting run states. Uses a fake backend to
    simulate workflow execution.
    """
    def init_db(self, base_dir):
        """Create a fresh database with three users and return an open
        connection to the database.
        """
        con = db.init_db(base_dir).connect()
        sql = 'INSERT INTO api_user(user_id, name, secret, active) VALUES(?, ?, ?, ?)'
        con.execute(sql, (USER_1, USER_1, pbkdf2_sha256.hash(USER_1), 1))
        con.execute(sql, (USER_2, USER_2, pbkdf2_sha256.hash(USER_2), 1))
        con.execute(sql, (USER_3, USER_3, pbkdf2_sha256.hash(USER_3), 0))
        con.commit()
        return con

    def test_run_error(self, tmpdir):
        """Test state transitions when running a workflow that ends in an
        error state.
        """
        # Initialize the repository and the benchmark engine
        con = self.init_db(str(tmpdir))
        repo = BenchmarkRepository(
            con=con,
            template_repo=TemplateFSRepository(base_dir=str(tmpdir))
        )
        engine = BenchmarkEngine(con=con)
        # Add benchmark and create submission
        bm_1 = repo.add_benchmark(name='A', src_dir=TEMPLATE_DIR)
        submission = SubmissionManager(con=con).create_submission(
            benchmark_id=bm_1.identifier,
            name='A',
            user_id=USER_1
        )
        # Run workflow using fake engine
        run = engine.start_run(
            submission_id=submission.identifier,
            template=bm_1.get_template(),
            source_dir='/dev/null',
            arguments=dict(),
            backend=StateEngine()
        )
        run_id = run.identifier
        # Start the run
        engine.update_run(run_id=run_id, state=run.state.start())
        run = engine.get_run(run_id=run_id)
        assert run.state.is_running()
        # Errors for illegal state transitions
        with pytest.raises(err.IllegalStateTransitionError):
            engine.update_run(run_id=run_id, state=StatePending())
        # Set run into error state
        messages = ['there', 'was', 'an', 'error']
        engine.update_run(
            run_id=run_id,
            state=run.state.error(messages=messages)
        )
        run = engine.get_run(run_id=run_id)
        assert run.state.is_error()
        assert run.state.messages == messages
        # Errors for illegal state transitions
        with pytest.raises(err.IllegalStateTransitionError):
            engine.update_run(run_id=run_id, state=StatePending())
        with pytest.raises(err.IllegalStateTransitionError):
            engine.update_run(run_id=run_id, state=StatePending().start())
        with pytest.raises(err.IllegalStateTransitionError):
            engine.update_run(run_id=run_id, state=StatePending().start().error())
        with pytest.raises(err.IllegalStateTransitionError):
            engine.update_run(run_id=run_id, state=StatePending().start().success())

    def test_run_results(self, tmpdir):
        """Test loading run results into the respective result table."""
        # Initialize the repository and the benchmark engine
        con = self.init_db(str(tmpdir))
        repo = BenchmarkRepository(
            con=con,
            template_repo=TemplateFSRepository(base_dir=str(tmpdir))
        )
        engine = BenchmarkEngine(con=con)
        # Add benchmark and create submission
        bm_1 = repo.add_benchmark(name='A', src_dir=TEMPLATE_DIR)
        submission = SubmissionManager(con=con).create_submission(
            benchmark_id=bm_1.identifier,
            name='A',
            user_id=USER_1
        )
        # Run workflow for different result sets
        values = [
            {'max_len': 1, 'avg_count': 1.1, 'max_line': 'R0'},
            {'max_len': 2, 'avg_count': 2.1},
        ]
        for vals in values:
            wf.run_workflow(
                engine=engine,
                template=bm_1.get_template(),
                submission_id=submission.identifier,
                base_dir=str(tmpdir),
                values=vals
            )
        values = [
            {'max_len': 1, 'max_line': 'R0'},
            {'avg_count': 2.1},
        ]
        with pytest.raises(err.ConstraintViolationError):
            for vals in values:
                wf.run_workflow(
                    engine=engine,
                    template=bm_1.get_template(),
                    submission_id=submission.identifier,
                    base_dir=str(tmpdir),
                    values=vals
                )

    def test_run_success(self, tmpdir):
        """Test state transitions when running a workflow that ends in a
        success state.
        """
        # Initialize the repository and the benchmark engine
        con = self.init_db(str(tmpdir))
        repo = BenchmarkRepository(
            con=con,
            template_repo=TemplateFSRepository(base_dir=str(tmpdir))
        )
        engine = BenchmarkEngine(con=con)
        # Add benchmark and create submission
        bm_1 = repo.add_benchmark(name='A', src_dir=TEMPLATE_DIR)
        submission = SubmissionManager(con=con).create_submission(
            benchmark_id=bm_1.identifier,
            name='A',
            user_id=USER_1
        )
        # Run workflow using fake engine
        run = engine.start_run(
            submission_id=submission.identifier,
            template=bm_1.get_template(),
            source_dir='/dev/null',
            arguments=dict(),
            backend=StateEngine()
        )
        run_id = run.identifier
        assert run.state.is_pending()
        run = engine.get_run(run_id=run_id)
        assert run.state.is_pending()
        engine.update_run(run_id=run_id, state=run.state.start())
        run = engine.get_run(run_id=run_id)
        assert run.state.is_running()
        result_file = os.path.join(str(tmpdir), 'run_result.json')
        util.write_object(
            filename=result_file,
            obj={'max_len': 1, 'avg_count': 2.1, 'max_line': 'R0'}
        )
        file_id = bm_1.get_template().get_schema().result_file_id
        files = {
            file_id:
            FileResource(identifier=file_id, filename=result_file)
        }
        state = run.state.success(files=files)
        engine.update_run(run_id=run_id, state=state)
        run = engine.get_run(run_id=run_id)
        assert run.state.is_success()
        assert 'results/analytics.json' in run.state.files
        # Errors for illegal state transitions
        with pytest.raises(err.IllegalStateTransitionError):
            engine.update_run(run_id=run_id, state=StatePending())
        with pytest.raises(err.IllegalStateTransitionError):
            engine.update_run(run_id=run_id, state=StatePending().start())
        with pytest.raises(err.IllegalStateTransitionError):
            engine.update_run(run_id=run_id, state=StatePending().start().error())
        with pytest.raises(err.IllegalStateTransitionError):
            engine.update_run(run_id=run_id, state=StatePending().start().success())
