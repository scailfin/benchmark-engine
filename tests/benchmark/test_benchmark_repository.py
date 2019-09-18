# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""Test functionality of the benchmark repository."""

import os
import pytest

from benchengine.benchmark.repo import BenchmarkRepository
from benchengine.db import DatabaseDriver

import benchengine.benchmark.base as bm
import benchengine.config as config
import benchengine.error as err


DIR = os.path.dirname(os.path.realpath(__file__))
TEMPLATE_DIR = os.path.join(DIR, '../.files/templates/helloworld')


class TestBenchmarkRepository(object):
    """Test creating and maintaining benchmarks."""
    def init(self, base_dir):
        """Initialize the BASEDIR environment variable. Create a fresh database
        and return an open connection.
        """
        os.environ[config.ENV_BASEDIR] = os.path.abspath(str(base_dir))
        connect_string = 'sqlite:{}/auth.db'.format(str(base_dir))
        DatabaseDriver.init_db(connect_string=connect_string)
        return DatabaseDriver.connect(connect_string=connect_string)

    def test_add_benchmark(self, tmpdir):
        """Test adding new benchmarks."""
        # Add with minimal information
        con = self.init(tmpdir)
        repo = BenchmarkRepository(con=con)
        bdesc = repo.add_benchmark(
            name='My benchmark',
            src_dir=TEMPLATE_DIR
        )
        assert bdesc.name == 'My benchmark'
        assert not bdesc.has_description()
        assert not bdesc.has_instructions()
        # Ensure that a benchmark result table has been created
        table_name = bm.PREFIX_RESULT_TABLE + bdesc.identifier
        con.execute('SELECT * FROM ' + table_name)
        repo = BenchmarkRepository(con=con)
        bmark = repo.get_benchmark(bdesc.identifier)
        assert bmark.identifier == bdesc.identifier
        assert bmark.name == 'My benchmark'
        assert not bmark.has_description()
        assert not bmark.has_instructions()
        repo = BenchmarkRepository(con=con, template_store=repo.template_store)
        # Add benchmark with full information
        bdesc = repo.add_benchmark(
            name='My better benchmark',
            description='Short description',
            instructions='Long instructions',
            src_dir=TEMPLATE_DIR
        )
        assert bdesc.name == 'My better benchmark'
        assert bdesc.has_description()
        assert bdesc.description == 'Short description'
        assert bdesc.has_instructions()
        assert bdesc.instructions == 'Long instructions'
        bmark = repo.get_benchmark(bdesc.identifier)
        assert bmark.name == 'My better benchmark'
        assert bmark.has_description()
        assert bmark.description == 'Short description'
        assert bmark.has_instructions()
        assert bmark.instructions == 'Long instructions'
        # Errors are raised if an attempt is made to add benchmarks with
        # duplicate or invalid names
        with pytest.raises(err.ConstraintViolationError):
            repo.add_benchmark(name='My benchmark', src_dir=TEMPLATE_DIR)
        with pytest.raises(err.ConstraintViolationError):
            repo.add_benchmark(name=None, src_dir=TEMPLATE_DIR)
        with pytest.raises(err.ConstraintViolationError):
            repo.add_benchmark(name=' ', src_dir=TEMPLATE_DIR)
        with pytest.raises(err.ConstraintViolationError):
            repo.add_benchmark(name='a' * 256, src_dir=TEMPLATE_DIR)
        with pytest.raises(ValueError):
            repo.add_benchmark(name='A benchmark')

    def test_delete_benchmark(self, tmpdir):
        """Test deleting a benchmarks from the repository"""
        con = self.init(tmpdir)
        repo = BenchmarkRepository(con=con)
        bdesc_1 = repo.add_benchmark(
            name='First',
            src_dir=TEMPLATE_DIR
        )
        assert len(repo.list_benchmarks()) == 1
        bdesc_2 = repo.add_benchmark(
            name='Second',
            src_dir=TEMPLATE_DIR
        )
        assert len(repo.list_benchmarks()) == 2
        bdesc_3 = repo.add_benchmark(
            name='Third',
            src_dir=TEMPLATE_DIR
        )
        assert len(repo.list_benchmarks()) == 3
        names = [bmark.name for bmark in repo.list_benchmarks()]
        for name in ['First', 'Second', 'Third']:
            assert name in names
        repo.delete_benchmark(bdesc_2.identifier)
        assert len(repo.list_benchmarks()) == 2
        names = [bmark.name for bmark in repo.list_benchmarks()]
        assert not 'Second' in names
        for name in ['First', 'Third']:
            assert name in names
        # Accessing an unknown benchmark will raise an error
        with pytest.raises(err.UnknownBenchmarkError):
            repo.get_benchmark(bdesc_2.identifier)
        repo.delete_benchmark(bdesc_1.identifier)
        assert len(repo.list_benchmarks()) == 1
        repo.delete_benchmark(bdesc_3.identifier)
        assert len(repo.list_benchmarks()) == 0
        # Deleting an unknown benchmark will raise an error
        with pytest.raises(err.UnknownBenchmarkError):
            repo.delete_benchmark(bdesc_1.identifier)

    def test_insert_results(self, tmpdir):
        """Test inserting run results for a benchmark."""
        # Add with minimal information
        con = self.init(tmpdir)
        repo = BenchmarkRepository(con=con)
        benchmark = repo.add_benchmark(
            name='My benchmark',
            src_dir=TEMPLATE_DIR
        )
        benchmark.insert_results('RUN1', {'max_len': 1, 'avg_count': 1.1, 'max_line': 'R1'})
        benchmark.insert_results('RUN2', {'max_len': 2, 'avg_count': 2.1, 'max_line': 'R2'})
        benchmark.insert_results('RUN3', {'max_len': 3, 'avg_count': 3.1})
        table_name = bm.PREFIX_RESULT_TABLE + benchmark.identifier
        sql ='SELECT max_line FROM {} WHERE run_id = ?'.format(table_name)
        rs = con.execute(sql, ('RUN1', )).fetchone()
        assert rs['max_line'] == 'R1'
        rs = con.execute(sql, ('RUN3', )).fetchone()
        assert rs['max_line'] is None
        with pytest.raises(err.ConstraintViolationError):
            benchmark.insert_results('RUN4', {'max_len': 4, 'max_line': 'R4'})
