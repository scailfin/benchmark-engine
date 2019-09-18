# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""The benchmark repository maintains information about benchmarks as well as
the results of different benchmark runs. For each benchmark basic information is
stored in the underlying database, together with the workflow template and the
result files of individual workflow runs.
"""

from benchengine.benchmark.base import BenchmarkDescriptor, BenchmarkHandle
from benchengine.user.auth import Auth
from benchtmpl.workflow.benchmark.loader import BenchmarkTemplateLoader
from benchtmpl.workflow.template.repo import TemplateRepository

import benchengine.config as config
import benchengine.error as err


class BenchmarkRepository(Auth):
    """The repository maintains benchmarks as well as the results of benchmark
    runs. The repository is a wrapper around two components:
    (1) the template repository to maintain workflow templates for for each
        benchmark, and
    (2) the database to store benchamrk informations (e.g., name, descritption)
        and information about result files for workflow runs.
    """
    def __init__(self, con, template_store=None):
        """Initialize the database connection and the template store.

        Parameters
        ----------
        con: DB-API 2.0 database connection
            Connection to underlying database
        template_store: benchtmpl.workflow.template.repo.TemplateRepository, optional
            Repository for workflow templates
        """
        super(BenchmarkRepository, self).__init__(con)
        if not template_store is None:
            self.template_store = template_store
        else:
            template_dir = config.get_template_dir()
            self.template_store = TemplateRepository(
                base_dir=template_dir,
                loader=BenchmarkTemplateLoader(),
                filenames=['benchmark', 'template', 'workflow']
            )

    def add_benchmark(
        self, name, description=None, instructions=None, src_dir=None,
        src_repo_url=None, template_spec_file=None
    ):
        """Add a benchmark to the repository. The associated workflow template
        is created in the template repository from either the given source
        directory or Git repository. The template repository will raise an
        error if neither or both arguments are given.

        Raises an error if the given benchmark name is not unique.

        Parameters
        ----------
        name: string
            Unique benchmark headline name
        description: string, optional
            Optional short description for display in benchmark listings
        instructions: string, optional
            Text containing detailed instructions for benchmark participants
        src_dir: string, optional
            Directory containing the benchmark components, i.e., the fixed
            files and the template specification (optional).
        src_repo_url: string, optional
            Git repository that contains the the benchmark components
        template_spec_file: string, optional
            Path to the workflow template specification file (absolute or
            relative to the workflow directory)

        Returns
        -------
        benchengine.benchmark.base.BenchmarkHandle

        Raises
        ------
        benchengine.error.ConstraintViolationError
        benchtmpl.error.InvalidParameterError
        benchtmpl.error.InvalidTemplateError
        ValueError
        """
        # Ensure that the benchmark name is not empty, not longer than 255
        # character and unique.
        if name is None:
            raise err.ConstraintViolationError('missing benchmark name')
        name = name.strip()
        if name == '' or len(name) > 255:
            raise err.ConstraintViolationError('invalid benchmark name')
        sql = 'SELECT id FROM benchmark WHERE name = ?'
        if not self.con.execute(sql, (name,)).fetchone() is None:
            raise err.ConstraintViolationError('benchmark \'{}\' exists'.format(name))
        # Create the workflow template in the associated template repository
        template = self.template_store.add_template(
            src_dir=src_dir,
            src_repo_url=src_repo_url,
            template_spec_file=template_spec_file
        )
        # Insert benchmark into database and return descriptor
        sql = 'INSERT INTO benchmark'
        sql += '(id, name, description, instructions) '
        sql += 'VALUES(?, ?, ?, ?)'
        self.con.execute(
            sql,
            (template.identifier, name, description, instructions)
        )
        self.con.commit()
        handle = BenchmarkHandle(
            con=self.con,
            template=template,
            name=name,
            description=description,
            instructions=instructions
        )
        handle.create_result_table()
        return handle

    def assert_benchmark_exists(self, benchmark_id):
        """Ensure that the benchmark with the given identifier exists. If no
        benchmark exists with that identifier an unknown benchmark error
        is raised.

        Parameters
        ----------
        benchmark_id: string
            Unique benchmark identifier

        Raises
        ------
        benchengine.error.UnknownBenchmarkError
        """
        sql = 'SELECT id FROM benchmark WHERE id = ?'
        if self.con.execute(sql, (benchmark_id,)).fetchone() is None:
            raise err.UnknownBenchmarkError(benchmark_id)

    def delete_benchmark(self, benchmark_id):
        """Delete the benchmark with the given identifier. Raises an exception
        if the given benchmark is unknown.

        Parameters
        ----------
        benchmark_id: string
            Unique benchmark identifier

        Raises
        ------
        benchengine.error.UnknownBenchmarkError
        """
        # Ensure that the benchmark exists. Raises error if it does not exist.
        self.assert_benchmark_exists(benchmark_id)
        # Delete the workflow handle
        self.template_store.delete_template(benchmark_id)
        # Delete the benchmark record
        sql = 'DELETE FROM benchmark WHERE id = ?'
        self.con.execute(sql, (benchmark_id,))
        self.con.commit()

    def get_benchmark(self, benchmark_id):
        """Get handle for the benchmark with the given identifier. Raises an
        error if no benchmark with the identifier exists.

        Parameters
        ----------
        benchmark_id: string
            Unique benchmark identifier

        Returns
        -------
        benchengine.benchmark.base.BenchmarkHandle

        Raises
        ------
        benchengine.error.UnknownBenchmarkError
        """
        # Get benchmark information from database. If the result is empty an
        # error is raised
        sql = 'SELECT id, name, description, instructions '
        sql += 'FROM benchmark '
        sql += 'WHERE id = ?'
        bmark = self.con.execute(sql, (benchmark_id,)).fetchone()
        if bmark is None:
            raise err.UnknownBenchmarkError(benchmark_id)
        # Get workflow template for template repository
        template = self.template_store.get_template(benchmark_id)
        # Return handle for benchmark
        return BenchmarkHandle(
            con=self.con,
            template=template,
            name=bmark['name'],
            description=bmark['description'],
            instructions=bmark['instructions']
        )

    def list_benchmarks(self):
        """Get a list of descriptors for all benchmarks in the repository.

        Returns
        -------
        list(benchengine.benchmark.base.BenchmarkDescriptor)
        """
        sql = 'SELECT id, name, description, instructions '
        sql += 'FROM benchmark '
        rs = self.con.execute(sql)
        result = list()
        for bmark in rs:
            result.append(
                BenchmarkDescriptor(
                    identifier=bmark['id'],
                    name=bmark['name'],
                    description=bmark['description'],
                    instructions=bmark['instructions']
                )
            )
        return result
