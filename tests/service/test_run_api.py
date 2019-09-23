# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""Test API methods for benchmark runs."""

import os
import pytest

from passlib.hash import pbkdf2_sha256

from robapi.model.auth import DefaultAuthPolicy
from robapi.model.submission import SubmissionManager
from robapi.model.benchmark.engine import BenchmarkEngine
from robapi.model.benchmark.repo import BenchmarkRepository
from robapi.model.user import UserManager
from robapi.service.benchmark import BenchmarkService
from robapi.service.run import RunService
from robapi.service.submission import SubmissionService
from robapi.tests.benchmark import StateEngine
from robapi.tests.io import FakeStream
from robtmpl.template.repo.fs import TemplateFSRepository
from robtmpl.workflow.state.base import StatePending
from robtmpl.workflow.resource import FileResource

import robapi.error as err
import robapi.serialize.hateoas as hateoas
import robapi.serialize.labels as labels
import robapi.tests.db as db
import robapi.tests.serialize as serialize
import robtmpl.util as util


DIR = os.path.dirname(os.path.realpath(__file__))
TEMPLATE_DIR = os.path.join(DIR, '../.files/templates/helloworld')

# Default benchmark users
USER_1 = util.get_unique_identifier()
USER_2 = util.get_unique_identifier()
USER_3 = util.get_unique_identifier()

# Mandatory labels for run handles
RUN_LABELS = [labels.ID, labels.STATE, labels.CREATED_AT, labels.LINKS]
RUN_HANDLE = RUN_LABELS + [labels.ARGUMENTS]
RUN_PENDING = RUN_HANDLE
RUN_RUNNING = RUN_PENDING + [labels.STARTED_AT]
RUN_ERROR = RUN_RUNNING + [labels.FINISHED_AT, labels.MESSAGES]
RUN_SUCCESS = RUN_RUNNING + [labels.FINISHED_AT]

# Mandatory HATEOAS relationships in run descriptors
RELS_ACTIVE = [hateoas.SELF, hateoas.action(hateoas.CANCEL)]
RELS_INACTIVE = [hateoas.SELF, hateoas.action(hateoas.DELETE)]


class TestRunApi(object):
    """Test API methods that execute, access and manipulate benchmark runs."""
    def init(self, base_dir):
        """Initialize the database, benchmark repository, submission manager,
        and the benchmark engine. Load one benchmark.

        Returns the run service, submission service, user service, the handle
        for the created benchmark.
        """
        con = db.init_db(base_dir).connect()
        sql = 'INSERT INTO api_user(user_id, name, secret, active) VALUES(?, ?, ?, ?)'
        for user_id in [USER_1, USER_2, USER_3]:
            con.execute(sql, (user_id, user_id, pbkdf2_sha256.hash(user_id), 1))
        repo = BenchmarkRepository(
            con=con,
            template_repo=TemplateFSRepository(base_dir=base_dir)
        )
        bm = repo.add_benchmark(name='A', src_dir=TEMPLATE_DIR)
        auth = DefaultAuthPolicy(con=con)
        submissions = SubmissionManager(con=con, directory=base_dir)
        return (
             RunService(
                engine=BenchmarkEngine(con=con, backend=StateEngine()),
                submissions=submissions,
                repo=repo,
                auth=auth
            ),
            SubmissionService(manager=submissions, auth=auth),
            UserManager(con=con),
            bm
        )

    def test_execute_run(self, tmpdir):
        """Test starting new runs for a submission."""
        runs, submissions, users, benchmark = self.init(str(tmpdir))
        # Get handle for USER_1
        user = users.login_user(USER_1, USER_1)
        # Create new submission with a single member
        s = submissions.create_submission(
            benchmark_id=benchmark.identifier,
            name='A',
            user=user
        )
        submission_id = s[labels.ID]
        # Start a new run. The resulting run is expected to be in pending state.
        r = runs.start_run(submission_id, dict(), user)
        util.validate_doc(doc=r, mandatory_labels=RUN_PENDING)
        serialize.validate_links(r, RELS_ACTIVE)
        # Start a new run in running state.
        runs.engine.backend.state = StatePending().start()
        r = runs.start_run(submission_id, dict(), user)
        util.validate_doc(doc=r, mandatory_labels=RUN_RUNNING)
        serialize.validate_links(r, RELS_ACTIVE)
        # Start a new run in error.
        runs.engine.backend.state = StatePending().start().error(['Error'])
        r = runs.start_run(submission_id, dict(), user)
        util.validate_doc(doc=r, mandatory_labels=RUN_ERROR)
        serialize.validate_links(r, RELS_INACTIVE)
        # Start a new run in running.
        result_file = os.path.join(str(tmpdir), 'run_result.json')
        values = {'max_len': 10, 'avg_count': 11.1}
        util.write_object(filename=result_file, obj=values)
        file_id = benchmark.template.get_schema().result_file_id
        files = {file_id: FileResource(identifier=file_id, filename=result_file)}
        runs.engine.backend.state = StatePending().start().success(files=files)
        r = runs.start_run(submission_id, dict(), user)
        util.validate_doc(doc=r, mandatory_labels=RUN_SUCCESS)
        serialize.validate_links(r, RELS_INACTIVE)
