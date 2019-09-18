# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""Test functionality of the submission manager."""

import os
import pytest

from passlib.hash import pbkdf2_sha256

from robapi.model.benchmark.engine import BenchmarkEngine
from robapi.model.benchmark.repo import BenchmarkRepository
from robapi.model.benchmark.submission import SubmissionManager
from robapi.tests.benchmark import StateEngine
from robtmpl.template.repo.fs import TemplateFSRepository
from robtmpl.workflow.state.base import StatePending

import robapi.error as err
import robapi.tests.db as db
import robtmpl.util as util


DIR = os.path.dirname(os.path.realpath(__file__))
TEMPLATE_DIR = os.path.join(DIR, '../../.files/templates/helloworld')
TEMPLATE_WITHOUT_SCHEMA = os.path.join(DIR, '../../.files/templates/template.json')


USER_1 = util.get_unique_identifier()
USER_2 = util.get_unique_identifier()
USER_3 = util.get_unique_identifier()


class TestSubmissionManager(object):
    """Unit tests for managing submissions and team members through the
    submission manager.
    """
    def init(self, base_dir):
        """Create a fresh database with three users and a template repository
        with a single entry. Returns an tuple containing an instance of the
        submission manager the handle for the created benchmark, and an
        instance of the benchmark engine.
        """
        con = db.init_db(base_dir).connect()
        sql = 'INSERT INTO api_user(user_id, name, secret, active) VALUES(?, ?, ?, ?)'
        con.execute(sql, (USER_1, USER_1, pbkdf2_sha256.hash(USER_1), 1))
        con.execute(sql, (USER_2, USER_2, pbkdf2_sha256.hash(USER_2), 1))
        con.execute(sql, (USER_3, USER_3, pbkdf2_sha256.hash(USER_3), 0))
        con.commit()
        bm = repo = BenchmarkRepository(
            con=con,
            template_repo=TemplateFSRepository(base_dir=str(base_dir))
        ).add_benchmark(name='A', src_dir=TEMPLATE_DIR)
        return SubmissionManager(con=con), bm, BenchmarkEngine(con=con)

    def test_create_submission(self, tmpdir):
        """Test creating a submission."""
        # Initialize the repository and the benchmark
        manager, bm, _ = self.init(str(tmpdir))
        submission = manager.create_submission(
            benchmark_id=bm.identifier,
            name='A',
            user_id=USER_1
        )
        assert submission.name == 'A'
        assert submission.owner_id == USER_1
        assert len(submission.members) == 1
        assert USER_1 in submission.members
        submission = manager.create_submission(
            benchmark_id=bm.identifier,
            name='B',
            user_id=USER_2,
            members=[USER_1, USER_3]
        )
        assert submission.owner_id == USER_2
        assert len(submission.members) == 3
        for user_id in [USER_1, USER_2, USER_3]:
            assert user_id in submission.members
        # Error conditions
        # - Unknown benchmark
        with pytest.raises(err.UnknownBenchmarkError):
            manager.create_submission(
                benchmark_id='UNK',
                name='C',
                user_id=USER_1
            )
        # - Invalid name
        with pytest.raises(err.ConstraintViolationError):
            manager.create_submission(
                benchmark_id=bm.identifier,
                name='A' * 513,
                user_id=USER_1
            )

    def test_delete_submission(self, tmpdir):
        """Test creating and deleting submissions."""
        # Initialize the repository and the benchmark
        manager, bm, _ = self.init(str(tmpdir))
        submission = manager.create_submission(
            benchmark_id=bm.identifier,
            name='A',
            user_id=USER_1
        )
        submission = manager.get_submission(submission.identifier)
        assert manager.delete_submission(submission.identifier)
        assert not manager.delete_submission(submission.identifier)
        with pytest.raises(err.UnknownSubmissionError):
            manager.get_submission(submission.identifier)

    def test_get_runs(self, tmpdir):
        """Test retrieving list of submission runs."""
        # Initialize the repository and the benchmark
        manager, bm, engine = self.init(str(tmpdir))
        # Create two submissions
        s1 = manager.create_submission(
            benchmark_id=bm.identifier,
            name='A',
            user_id=USER_1
        )
        s2 = manager.create_submission(
            benchmark_id=bm.identifier,
            name='B',
            user_id=USER_1
        )
        # Add two runs to submission 1 and set them into running state
        engine.start_run(
            submission_id=s1.identifier,
            template=bm.get_template(),
            source_dir='/dev/null',
            arguments=dict(),
            backend=StateEngine(StatePending().start())
        )
        engine.start_run(
            submission_id=s1.identifier,
            template=bm.get_template(),
            source_dir='/dev/null',
            arguments=dict(),
            backend=StateEngine(StatePending().start())
        )
        # Add one run to submission 2 that is in pending state
        engine.start_run(
            submission_id=s2.identifier,
            template=bm.get_template(),
            source_dir='/dev/null',
            arguments=dict(),
            backend=StateEngine()
        )
        # Ensure that submission 1 has two runs in running state
        submission = manager.get_submission(s1.identifier)
        runs = submission.get_runs()
        assert len(runs) == 2
        for run in runs:
            assert run.is_running()
        # Ensure that submission 2 has one run in pending state
        submission = manager.get_submission(s2.identifier)
        runs = submission.get_runs()
        assert len(runs) == 1
        for run in runs:
            assert run.is_pending()
        # Error when accessing an unknown submission
        with pytest.raises(err.UnknownSubmissionError):
            manager.get_runs('UNK')

    def test_get_submission(self, tmpdir):
        """Test creating and retrieving submissions."""
        # Initialize the repository and the benchmark
        manager, bm, _ = self.init(str(tmpdir))
        submission = manager.create_submission(
            benchmark_id=bm.identifier,
            name='A',
            user_id=USER_1
        )
        submission = manager.get_submission(submission.identifier)
        assert submission.name == 'A'
        assert submission.owner_id == USER_1
        assert len(submission.members) == 1
        assert USER_1 in submission.members
        submission = manager.create_submission(
            benchmark_id=bm.identifier,
            name='B',
            user_id=USER_2,
            members=[USER_1, USER_3]
        )
        submission = manager.get_submission(submission.identifier)
        assert submission.name == 'B'
        assert submission.owner_id == USER_2
        assert len(submission.members) == 3
        for user_id in [USER_1, USER_2, USER_3]:
            assert user_id in submission.members
        # Error when accessing an unknown submission
        with pytest.raises(err.UnknownSubmissionError):
            manager.get_submission('UNK')

    def test_submission_membership(self, tmpdir):
        """Test adding and removing submission members."""
        # Initialize the repository and the benchmark
        manager, bm, _ = self.init(str(tmpdir))
        submission = manager.create_submission(
            benchmark_id=bm.identifier,
            name='A',
            user_id=USER_1
        )
        s_id = submission.identifier
        submission = manager.get_submission(s_id)
        assert len(submission.members) == 1
        manager.add_member(submission_id=s_id, user_id=USER_2)
        submission = manager.get_submission(s_id)
        assert len(submission.members) == 2
        with pytest.raises(err.ConstraintViolationError):
            manager.add_member(submission_id=s_id, user_id=USER_2)
        assert manager.remove_member(submission_id=s_id, user_id=USER_2)
        manager.add_member(submission_id=s_id, user_id=USER_2)
        submission = manager.get_submission(s_id)
        assert len(submission.members) == 2
        for user_id in [USER_1, USER_2]:
            assert user_id in submission.members
        assert manager.remove_member(submission_id=s_id, user_id=USER_1)
        assert not manager.remove_member(submission_id=s_id, user_id=USER_1)
        submission = manager.get_submission(s_id)
        assert len(submission.members) == 1
        assert USER_2 in submission.members
        assert manager.remove_member(submission_id=s_id, user_id=USER_2)
        submission = manager.get_submission(s_id)
        assert len(submission.members) == 0
