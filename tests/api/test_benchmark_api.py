"""Test API methods for benchmark resources."""

import os
import shutil

from unittest import TestCase

from benchengine.api.base import EngineApi
from benchengine.db import DatabaseDriver

import benchengine.api.serialize.hateoas as hateoas
import benchengine.api.serialize.labels as labels
import benchengine.config as config
import benchengine.error as err


TEMPLATE_DIR = './tests/files/templates/helloworld'
TMP_DIR = 'tests/files/.tmp'
CONNECT = 'sqlite:{}/test.db'.format(TMP_DIR)


class TestBenchmarkApi(TestCase):
    """Test API methods that access and list benchmarks and leaderboards."""
    def setUp(self):
        """Create empty directory."""
        if os.path.isdir(TMP_DIR):
            shutil.rmtree(TMP_DIR)
        os.mkdir(TMP_DIR)
        os.environ[config.ENV_DATABASE] = CONNECT
        os.environ[config.ENV_BASEDIR] = TMP_DIR
        DatabaseDriver.init_db()
        self.engine = EngineApi()

    def tearDown(self):
        """Remove temporary directory."""
        self.engine.close()
        if os.path.isdir(TMP_DIR):
            shutil.rmtree(TMP_DIR)

    def test_get_benchmark(self):
        """Test get benchmark handle."""
        repo = self.engine.benchmarks().repository
        benchmark = repo.add_benchmark(
            name='First competition',
            description='Some text',
            instructions='More text',
            src_dir=TEMPLATE_DIR
        )
        benchmark_id = benchmark.identifier
        response = self.engine.benchmarks().get_benchmark(benchmark_id)
        self.validate_benchmark(response, is_handle=True, has_description=True, has_instructions=True)
        # Create benchmark without the optional description and instructions
        benchmark = repo.add_benchmark(
            name='Second competition',
            src_dir=TEMPLATE_DIR
        )
        benchmark_id = benchmark.identifier
        response = self.engine.benchmarks().get_benchmark(benchmark_id)
        self.validate_benchmark(response, is_handle=True, has_description=False, has_instructions=False)
        # Get handle for invalid access token will raise error
        with self.assertRaises(err.UnauthenticatedAccessError):
            self.engine.benchmarks().get_benchmark(benchmark_id, access_token='unknown')

    def test_list_benchmarks(self):
        """Test benchmark listing."""
        repo = self.engine.benchmarks().repository
        benchmark1 = repo.add_benchmark(
            name='First competition',
            description='Some text',
            instructions='More text',
            src_dir=TEMPLATE_DIR
        )
        benchmark2 = repo.add_benchmark(
            name='Second competition',
            src_dir=TEMPLATE_DIR
        )
        response = self.engine.benchmarks().list_benchmarks()
        self.assertEqual(len(response), 2)
        self.assertTrue(labels.BENCHMARKS in response)
        self.assertTrue(labels.LINKS in response)
        benchmarks = response[labels.BENCHMARKS]
        self.assertEqual(len(benchmarks), 2)
        names = set()
        for benchmark in benchmarks:
            names.add(benchmark[labels.NAME])
            self.validate_benchmark(
                benchmark,
                has_description=benchmark[labels.ID]==benchmark1.identifier,
                has_instructions=benchmark[labels.ID]==benchmark1.identifier
            )
        self.assertTrue('First competition' in names)
        self.assertTrue('Second competition' in names)
        links = hateoas.deserialize(response[labels.LINKS])
        self.assertEqual(len(links), 1)
        self.assertTrue(hateoas.SELF in links)
        # Get listing for invalid access token
        with self.assertRaises(err.UnauthenticatedAccessError):
            self.engine.benchmarks().list_benchmarks(access_token='unknown')

    def validate_benchmark(
        self, benchmark, is_handle=False, has_description=False,
        has_instructions=False,
        rels=[hateoas.SELF, hateoas.benchmark(hateoas.LEADERBOARD)]
    ):
        """Validate a given serialization of a benchmark descriptor."""
        elements = [labels.ID, labels.NAME, labels.LINKS]
        if has_description:
            elements.append(labels.DESCRIPTION)
        if has_instructions:
            elements.append(labels.INSTRUCTIONS)
        if is_handle:
            elements.append(labels.PARAMETERS)
        self.assertEqual(len(benchmark), len(elements))
        for key in elements:
            self.assertTrue(key in benchmark)
        links = hateoas.deserialize(benchmark[labels.LINKS])
        self.assertEqual(len(links), len(rels))
        for key in rels:
            self.assertTrue(key in links)


if __name__ == '__main__':
    import unittest
    unittest.main()
