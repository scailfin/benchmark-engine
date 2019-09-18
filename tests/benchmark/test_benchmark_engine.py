# This file is part of the Reproducible Open Benchmarks for Data Analysis
# Platform (ROB).
#
# Copyright (C) 2019 NYU.
#
# ROB is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""Test functionality of the benchmark engine."""

import os

from benchengine.benchmark.repo import BenchmarkRepository
from benchengine.benchmark.engine import BenchmarkEngine
from benchengine.db import DatabaseDriver
from benchtmpl.io.files.base import FileHandle
from benchtmpl.workflow.benchmark.loader import BenchmarkTemplateLoader
from benchtmpl.workflow.parameter.value import TemplateArgument
from benchtmpl.workflow.template.repo import TemplateRepository

import benchengine.benchmark.base as bm
import benchengine.config as config
import benchengine.error as err


DIR = os.path.dirname(os.path.realpath(__file__))
DATA_FILE = os.path.join(DIR, '../.files/templates/helloworld/data/names.txt')
TEMPLATE_DIR = os.path.join(DIR, '../.files/templates/helloworld')


class TestBenchmarkEngine(object):
    """Test running benchmarks using the simple synchronous benchmark engine."""
    def test_run_benchmark(self, tmpdir):
        """Test running a benchmarks."""
        # Initialize the BASEDIR environment variable
        os.environ[config.ENV_BASEDIR] = os.path.abspath(str(tmpdir))
        # Create a new database and open a connection
        connect_string = 'sqlite:{}/auth.db'.format(str(tmpdir))
        DatabaseDriver.init_db(connect_string=connect_string)
        con = DatabaseDriver.connect(connect_string=connect_string)
        # Create repository and engine instances
        repository = BenchmarkRepository(
            con=con,
            template_store=TemplateRepository(
                base_dir=config.get_template_dir(),
                loader=BenchmarkTemplateLoader(),
                filenames=['benchmark', 'template', 'workflow']
            )
        )
        engine = BenchmarkEngine(con)
        # Add with minimal information
        benchmark = repository.add_benchmark(
            name='My benchmark',
            src_dir=TEMPLATE_DIR
        )
        template = benchmark.template
        arguments = {
            'names': TemplateArgument(
                parameter=template.get_parameter('names'),
                value=FileHandle(DATA_FILE)
            ),
            'sleeptime': TemplateArgument(
                parameter=template.get_parameter('sleeptime'),
                value=1
            ),
            'greeting': TemplateArgument(
                parameter=template.get_parameter('greeting'),
                value='Welcome'
            )
        }
        run_id, state = engine.run(benchmark, arguments, 'USERID')
        assert state.is_success()
        sql = 'SELECT * FROM benchmark_run WHERE run_id = ?'
        rs = con.execute(sql, (run_id, )).fetchone()
        assert rs['benchmark_id'] == benchmark.identifier
        assert rs['user_id'] == 'USERID'
        assert rs['state'] == state.type_id
        table_name = bm.PREFIX_RESULT_TABLE + benchmark.identifier
        sql ='SELECT * FROM {} WHERE run_id = ?'.format(table_name)
        rs = con.execute(sql, (run_id, )).fetchone()
        assert rs['max_line'] == 'Welcome Alice!'
