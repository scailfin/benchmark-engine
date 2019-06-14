"""Test functionality of the benchmark engine."""

import os
import shutil

from unittest import TestCase

from benchengine.benchmark.repo import BenchmarkRepository
from benchengine.benchmark.engine import BenchmarkEngine
from benchengine.db import DatabaseDriver
from benchtmpl.io.files.base import FileHandle
from benchtmpl.workflow.benchmark.loader import BenchmarkTemplateLoader
from benchtmpl.workflow.template.repo import TemplateRepository

import benchengine.benchmark.base as bm
import benchengine.config as config
import benchengine.error as err


DATA_FILE = './tests/files/templates/helloworld/data/names.txt'
TEMPLATE_DIR = './tests/files/templates/helloworld'
TMP_DIR = './tests/files/.tmp'
CONNECT = 'sqlite:{}/test.db'.format(TMP_DIR)



class TestBenchmarkEngine(TestCase):
    """Test running benchmarks using the simple synchronous benchmark engine."""
    def setUp(self):
        if os.path.isdir(TMP_DIR):
            shutil.rmtree(TMP_DIR)
        os.makedirs(TMP_DIR)
        """Create a fresh database."""
        DatabaseDriver.init_db(connect_string=CONNECT)
        self.con = DatabaseDriver.connect(connect_string=CONNECT)
        os.environ[config.ENV_BASEDIR] = os.path.abspath(TMP_DIR)
        self.repository = BenchmarkRepository(
            con=self.con,
            template_store=TemplateRepository(
                base_dir=config.get_template_dir(),
                loader=BenchmarkTemplateLoader(),
                filenames=['benchmark', 'template', 'workflow']
            )
        )
        self.engine = BenchmarkEngine(self.con)

    def tearDown(self):
        """Close connection and remove database file."""
        self.con.close()
        if os.path.isdir(TMP_DIR):
            shutil.rmtree(TMP_DIR)

    def test_run_benchmark(self):
        """Test running a benchmarks."""
        # Add with minimal information
        benchmark = self.repository.add_benchmark(
            name='My benchmark',
            src_dir=TEMPLATE_DIR
        )
        template = benchmark.template
        arguments = {
            'names': template.get_argument('names', FileHandle(DATA_FILE)),
            'sleeptime': template.get_argument('sleeptime', 1),
            'greeting': template.get_argument('greeting', 'Welcome')
        }
        run_id, state = self.engine.run(benchmark, arguments, 'USERID')
        self.assertTrue(state.is_success())
        sql = 'SELECT * FROM benchmark_run WHERE run_id = ?'
        rs = self.con.execute(sql, (run_id, )).fetchone()
        self.assertEqual(rs['benchmark_id'], benchmark.identifier)
        self.assertEqual(rs['user_id'], 'USERID')
        self.assertEqual(rs['state'], state.type_id)
        table_name = bm.PREFIX_RESULT_TABLE + benchmark.identifier
        sql ='SELECT * FROM {} WHERE run_id = ?'.format(table_name)
        rs = self.con.execute(sql, (run_id, )).fetchone()
        self.assertEqual(rs['max_line'], 'Welcome Alice!')


if __name__ == '__main__':
    import unittest
    unittest.main()
