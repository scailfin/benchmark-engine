# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""Submissions are used to (1) define groups of users that participate together
as a team in a benchmark, and (2) group the different runs (using different
parameters for example) that teams execute as part of their participation in
a benchmark.
"""

import json

from robapi.model.benchmark.result import ResultRanking
from robapi.model.benchmark.run import RunHandle
from robtmpl.template.schema import ResultSchema

import robapi.model.benchmark.base as base
import robapi.error as err
import robtmpl.util as util


class SubmissionHandle(object):
    """A submission is a set of workflow runs that are submmited by a group of
    users that participate in a benchmark.

    Submissions have unique identifier and names that are used to identify them
    internally and externally. Each submission has an owner and a list of team
    memebers.

    Maintains an optional reference to the submission manager that allows to
    load submission runs in-demand.
    """
    def __init__(self, identifier, name, owner_id, members=None, manager=None):
        """Initialize the object properties.

        Parameters
        ----------
        identifier: string
            Unique submission identifier
        name: string
            Unique submission name
        owner_id: string
            Unique identifier for the user that created the submission
        members: list(string)
            List of user identifier for team members
        manager: robapi.model.benchmark.submission.SubmissionManager, optional
            Optional reference to the submission manager
        """
        self.identifier = identifier
        self.name = name
        self.owner_id = owner_id
        self.members = set(members) if not members is None else set()
        self.manager = manager

    def get_results(self, order_by=None):
        """Get list of handles for all successful runs in the given submission.
        The resulting handles contain timestamp information and run results.

        Parameters
        ----------
        order_by: list(robtmpl.template.schema.SortColumn), optional
            Use the given attribute to sort run results. If not given the schema
            default attribute is used

        Returns
        -------
        robapi.model.benchmark.result.ResultRanking

        Raises
        ------
        robapi.error.UnknownSubmissionError
        """
        return self.manager.get_results(self.identifier, order_by=order_by)

    def get_runs(self):
        """Get list of handles for all runs in the submission.

        Returns
        -------
        list(robapi.model.benchmark.run.RunHandle)

        Raises
        ------
        robapi.error.UnknownSubmissionError
        """
        return self.manager.get_runs(self.identifier)


class SubmissionManager(object):
    """Manager for submissions from groups of users that participate in a
    benchmark. All information is maintained in an underlying database.
    """
    def __init__(self, con):
        """Initialize the connection to the database that is used for storage.

        Parameters
        ----------
        con: DB-API 2.0 database connection
            Connection to underlying database
        """
        self.con = con

    def add_member(self, submission_id, user_id):
        """Add a user as member to an existing submission. If the user already
        is a member of the submission an error is raised.

        Parameters
        ----------
        submission_id: string
            Unique submission identifier
        user_id: string
            Unique user identifier

        Raises
        ------
        robapi.error.ConstraintViolationError
        """
        # Query the database to ensure that the user isn't already a member of
        # the submission.
        sql = 'INSERT INTO submission_member(submission_id, user_id) VALUES(?, ?)'
        try:
            self.con.execute(sql, (submission_id, user_id))
            self.con.commit()
        except Exception:
            # Depending on the database system that is being used the type of
            # the exception may differ. Here we assume that any exception is
            # due to a primary key violation (i.e., the user is already a
            # member of the submission)
            msg = '{} already member of {}'.format(submission_id, user_id)
            raise err.ConstraintViolationError(msg)

    def create_submission(self, benchmark_id, name, user_id, members=None):
        """Create a new submission for a given benchmark. Within each benchmark,
        the names of submissions are expected to be unique.

        A submission may have a list of users that are submission members which
        allows them to submit runs. The user that creates the submission, i.e.,
        the user identified by user_id is always part of the list of submission
        members.

        Parameters
        ----------
        benchmark_id: string
            Unique benchmark identifier
        name: string
            Submission name
        user_id: string
            Unique identifier of the user that created the submission
        members: list(string), optional
            Optional list of user identifiers for other sumbission members

        Returns
        -------
        robapi.model.benchmark.base.SubmissionHandle

        Raises
        ------
        robapi.error.ConstraintViolationError
        robapi.error.UnknownBenchmarkError
        """
        # Ensure that the benchmark exists
        sql = 'SELECT * FROM benchmark WHERE benchmark_id = ?'
        if self.con.execute(sql, (benchmark_id,)).fetchone() is None:
            raise err.UnknownBenchmarkError(benchmark_id)
        # Ensure that the given name is valid and unique for the benchmark
        sql = 'SELECT name FROM benchmark_submission '
        sql += 'WHERE benchmark_id = \'{}\' AND name = ?'.format(benchmark_id)
        base.validate_name(name, con=self.con, sql=sql)
        # Create a new instance of the sumbission class.
        submission = SubmissionHandle(
            identifier=util.get_unique_identifier(),
            name=name,
            owner_id=user_id,
            members=members,
            manager=self
        )
        # Add owner to list of initial members
        if not user_id in submission.members:
            submission.members.add(user_id)
        # Enter submission information into database and commit all changes
        sql = 'INSERT INTO benchmark_submission('
        sql += 'submission_id, benchmark_id, name, owner_id'
        sql += ') VALUES(?, ?, ?, ?)'
        values = (submission.identifier, benchmark_id, name, user_id)
        self.con.execute(sql, values)
        sql = 'INSERT INTO submission_member(submission_id, user_id) VALUES(?, ?)'
        for member_id in submission.members:
            self.con.execute(sql, (submission.identifier, member_id))
        self.con.commit()
        # Return the created submission object
        return submission

    def delete_submission(self, submission_id):
        """Delete the entry for the given submission from the underlying
        database. Note that this will not remove any runs and run results that
        are associated with the submission.

        The return value indicates if the identifier referenced an existing
        submission or not.

        Parameters
        ----------
        identifier: string
            Unique submission identifier

        Returns
        -------
        bool
        """
        cur = self.con.cursor()
        sql = 'DELETE FROM benchmark_submission WHERE submission_id = ?'
        # Use row count to determine if the submission existed or not
        rowcount = cur.execute(sql, (submission_id,)).rowcount
        self.con.commit()
        return rowcount > 0

    def get_results(self, submission_id, order_by=None):
        """Get list of handles for all successful runs in the given submission.
        The result handles contain timestamp information and run results.

        Parameters
        ----------
        submission_id: string
            Unique submission identifier
        order_by: list(robtmpl.template.schema.SortColumn), optional
            Use the given attribute to sort run results. If not given the schema
            default attribute is used

        Returns
        -------
        robapi.model.benchmark.result.ResultRanking

        Raises
        ------
        robapi.error.UnknownSubmissionError
        """
        # Get result schema for the associated benchmark. Raise error if the
        # given submission identifier is invalid.
        sql = 'SELECT b.benchmark_id, b.result_schema '
        sql += 'FROM benchmark b, benchmark_submission s '
        sql += 'WHERE b.benchmark_id = s.benchmark_id AND s.submission_id = ?'
        row = self.con.execute(sql, (submission_id,)).fetchone()
        if row is None:
            raise err.UnknownSubmissionError(submission_id)
        # Get the result schema as defined in the workflow template
        if not row['result_schema'] is None:
            schema = ResultSchema.from_dict(json.loads(row['result_schema']))
        else:
            schema = ResultSchema()
        return ResultRanking.query(
            con=self.con,
            benchmark_id=row['benchmark_id'],
            schema=schema,
            filter_stmt='s.submission_id = ?',
            args=(submission_id,),
            order_by=order_by,
            include_all=True
        )

    def get_runs(self, submission_id):
        """Get list of handles for all runs in the given submission. All run
        information is read from the underlying database. This method does
        not query the backend to get workflow states.

        Parameters
        ----------
        submission_id: string
            Unique submission identifier

        Returns
        -------
        list(robapi.model.benchmark.run.RunHandle)

        Raises
        ------
        robapi.error.UnknownSubmissionError
        """
        # Raise error if the given submission identifier is invalid
        sql = 'SELECT submission_id '
        sql += 'FROM benchmark_submission '
        sql += 'WHERE submission_id = ?'
        if self.con.execute(sql, (submission_id,)).fetchone() is None:
            raise err.UnknownSubmissionError(submission_id)
        # Fetch run information from the database and return list of run
        # handles.
        sql = 'SELECT r.run_id, s.benchmark_id, s.submission_id, r.state, '
        sql += 'r.created_at, r.started_at, r.ended_at '
        sql += 'FROM benchmark b, benchmark_submission s, benchmark_run r '
        sql += 'WHERE s.submission_id = r.submission_id AND r.submission_id = ? '
        sql += 'ORDER BY r.created_at'
        result = list()
        for row in self.con.execute(sql, (submission_id,)).fetchall():
            result.append(RunHandle.from_db(doc=row, con=self.con))
        return result

    def get_submission(self, submission_id):
        """Get handle for submission with the given identifier.

        Parameters
        ----------
        identifier: string
            Unique submission identifier

        Returns
        -------
        robapi.model.benchmark.submission.SubmissionHandle

        Raises
        ------
        robapi.error.UnknownSubmissionError
        """
        # Get submission information. Raise error if the identifier is unknown.
        sql = 'SELECT name, owner_id '
        sql += 'FROM benchmark_submission '
        sql += 'WHERE submission_id = ?'
        row = self.con.execute(sql, (submission_id,)).fetchone()
        if row is None:
            raise err.UnknownSubmissionError(submission_id)
        name = row['name']
        owner_id = row['owner_id']
        # Get list of team members
        members = list()
        sql = 'SELECT user_id FROM submission_member WHERE submission_id = ?'
        for row in self.con.execute(sql, (submission_id,)).fetchall():
            members.append(row['user_id'])
        # Return the submission handle
        return SubmissionHandle(
            identifier=submission_id,
            name=name,
            owner_id=owner_id,
            members=members,
            manager=self
        )

    def remove_member(self, submission_id, user_id):
        """Remove a user as a menber from the given submission. The return value
        indicates if the submission exists and the user was a memmer of that
        submission.

        There are currently not constraints enforced, i.e., any user can be
        removed as submission member, even the submission owner.

        Parameters
        ----------
        submission_id: string
            Unique submission identifier
        user_id: string
            Unique user identifier

        Returns
        -------
        bool

        Raises
        ------
        robapi.error.ConstraintViolationError
        """
        cur = self.con.cursor()
        sql = 'DELETE FROM submission_member '
        sql += 'WHERE submission_id = ? AND user_id = ?'
        # Use row count to determine if the submission existed or not
        rowcount = cur.execute(sql, (submission_id, user_id)).rowcount
        self.con.commit()
        return rowcount > 0
