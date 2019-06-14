"""Test functionality of the benchmark repository."""

import os
import shutil

from unittest import TestCase

from benchengine.benchmark.repo import BenchmarkRepository
from benchengine.db import DatabaseDriver

import benchengine.benchmark.base as bm
import benchengine.config as config
import benchengine.error as err


TEMPLATE_DIR = './tests/files/templates/helloworld'
TMP_DIR = './tests/files/.tmp'
CONNECT = 'sqlite:{}/test.db'.format(TMP_DIR)



class TestBenchmarkRepository(TestCase):
    """Test creating and maintaining benchmarks."""
    def setUp(self):
        if os.path.isdir(TMP_DIR):
            shutil.rmtree(TMP_DIR)
        os.makedirs(TMP_DIR)
        """Create a fresh database."""
        DatabaseDriver.init_db(connect_string=CONNECT)
        self.con = DatabaseDriver.connect(connect_string=CONNECT)
        os.environ[config.ENV_BASEDIR] = os.path.abspath(TMP_DIR)

    def tearDown(self):
        """Close connection and remove database file."""
        self.con.close()
        if os.path.isdir(TMP_DIR):
            shutil.rmtree(TMP_DIR)

    def test_add_benchmark(self):
        """Test adding new benchmarks."""
        # Add with minimal information
        repo = BenchmarkRepository(con=self.con)
        bdesc = repo.add_benchmark(
            name='My benchmark',
            src_dir=TEMPLATE_DIR
        )
        self.assertEqual(bdesc.name, 'My benchmark')
        self.assertFalse(bdesc.has_description())
        self.assertFalse(bdesc.has_instructions())
        # Ensure that a benchmark result table has been created
        table_name = bm.PREFIX_RESULT_TABLE + bdesc.identifier
        self.con.execute('SELECT * FROM ' + table_name)
        repo = BenchmarkRepository(con=self.con)
        bmark = repo.get_benchmark(bdesc.identifier)
        self.assertEqual(bmark.identifier, bdesc.identifier)
        self.assertEqual(bmark.name, 'My benchmark')
        self.assertFalse(bmark.has_description())
        self.assertFalse(bmark.has_instructions())
        repo = BenchmarkRepository(con=self.con, template_store=repo.template_store)
        # Add benchmark with full information
        bdesc = repo.add_benchmark(
            name='My better benchmark',
            description='Short description',
            instructions='Long instructions',
            src_dir=TEMPLATE_DIR
        )
        self.assertEqual(bdesc.name, 'My better benchmark')
        self.assertTrue(bdesc.has_description())
        self.assertEqual(bdesc.description, 'Short description')
        self.assertTrue(bdesc.has_instructions())
        self.assertEqual(bdesc.instructions, 'Long instructions')
        bmark = repo.get_benchmark(bdesc.identifier)
        self.assertEqual(bmark.name, 'My better benchmark')
        self.assertTrue(bmark.has_description())
        self.assertEqual(bmark.description, 'Short description')
        self.assertTrue(bmark.has_instructions())
        self.assertEqual(bmark.instructions, 'Long instructions')
        # Errors are raised if an attempt is made to add benchmarks with
        # duplicate or invalid names
        with self.assertRaises(err.ConstraintViolationError):
            repo.add_benchmark(name='My benchmark', src_dir=TEMPLATE_DIR)
        with self.assertRaises(err.ConstraintViolationError):
            repo.add_benchmark(name=None, src_dir=TEMPLATE_DIR)
        with self.assertRaises(err.ConstraintViolationError):
            repo.add_benchmark(name=' ', src_dir=TEMPLATE_DIR)
        with self.assertRaises(err.ConstraintViolationError):
            repo.add_benchmark(name='a' * 256, src_dir=TEMPLATE_DIR)
        with self.assertRaises(ValueError):
            repo.add_benchmark(name='A benchmark')

    def test_delete_benchmark(self):
        """Test deleting a benchmarks from the repository"""
        repo = BenchmarkRepository(con=self.con)
        bdesc_1 = repo.add_benchmark(
            name='First',
            src_dir=TEMPLATE_DIR
        )
        self.assertEqual(len(repo.list_benchmarks()), 1)
        bdesc_2 = repo.add_benchmark(
            name='Second',
            src_dir=TEMPLATE_DIR
        )
        self.assertEqual(len(repo.list_benchmarks()), 2)
        bdesc_3 = repo.add_benchmark(
            name='Third',
            src_dir=TEMPLATE_DIR
        )
        self.assertEqual(len(repo.list_benchmarks()), 3)
        names = [bmark.name for bmark in repo.list_benchmarks()]
        for name in ['First', 'Second', 'Third']:
            self.assertTrue(name in names)
        repo.delete_benchmark(bdesc_2.identifier)
        self.assertEqual(len(repo.list_benchmarks()), 2)
        names = [bmark.name for bmark in repo.list_benchmarks()]
        self.assertFalse('Second' in names)
        for name in ['First', 'Third']:
            self.assertTrue(name in names)
        # Accessing an unknown benchmark will raise an error
        with self.assertRaises(err.UnknownBenchmarkError):
            repo.get_benchmark(bdesc_2.identifier)
        repo.delete_benchmark(bdesc_1.identifier)
        self.assertEqual(len(repo.list_benchmarks()), 1)
        repo.delete_benchmark(bdesc_3.identifier)
        self.assertEqual(len(repo.list_benchmarks()), 0)
        # Deleting an unknown benchmark will raise an error
        with self.assertRaises(err.UnknownBenchmarkError):
            repo.delete_benchmark(bdesc_1.identifier)

    def test_insert_results(self):
        """Test inserting run results for a benchmark."""
        # Add with minimal information
        repo = BenchmarkRepository(con=self.con)
        benchmark = repo.add_benchmark(
            name='My benchmark',
            src_dir=TEMPLATE_DIR
        )
        benchmark.insert_results('RUN1', {'max_len': 1, 'avg_count': 1.1, 'max_line': 'R1'})
        benchmark.insert_results('RUN2', {'max_len': 2, 'avg_count': 2.1, 'max_line': 'R2'})
        benchmark.insert_results('RUN3', {'max_len': 3, 'avg_count': 3.1})
        table_name = bm.PREFIX_RESULT_TABLE + benchmark.identifier
        sql ='SELECT max_line FROM {} WHERE run_id = ?'.format(table_name)
        rs = self.con.execute(sql, ('RUN1', )).fetchone()
        self.assertEqual(rs['max_line'], 'R1')
        rs = self.con.execute(sql, ('RUN3', )).fetchone()
        self.assertIsNone(rs['max_line'])
        with self.assertRaises(err.ConstraintViolationError):
            benchmark.insert_results('RUN4', {'max_len': 4, 'max_line': 'R4'})


if __name__ == '__main__':
    import unittest
    unittest.main()
