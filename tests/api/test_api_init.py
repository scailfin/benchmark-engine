"""Test initializing the engine API."""

import os
import shutil

from unittest import TestCase

from benchengine.api.base import EngineApi
from benchengine.api.route import UrlFactory
from benchengine.db import DatabaseDriver

import benchengine.api.serialize.hateoas as hateoas
import benchengine.api.serialize.labels as labels
import benchengine.config as config


TMP_DIR = 'tests/files/.tmp'
CONNECT = 'sqlite:{}/test.db'.format(TMP_DIR)


class TestApiInit(TestCase):
    """Test methods for initializing the Api and related components."""
    def setUp(self):
        """Create temporary directory and clean database instance."""
        if os.path.isdir(TMP_DIR):
            shutil.rmtree(TMP_DIR)
        os.makedirs(TMP_DIR)
        # Create fresh database instance
        DatabaseDriver.init_db(connect_string=CONNECT)

    def tearDown(self):
        """Close connection and remove database file."""
        if os.path.isdir(TMP_DIR):
            shutil.rmtree(TMP_DIR)

    def test_init_from_environ(self):
        """Test initializing the engine API using the values of environment
        variables.
        """
        # Set environment variable for database and engine base directory
        os.environ[config.ENV_DATABASE] = CONNECT
        os.environ[config.ENV_BASEDIR] = TMP_DIR
        os.environ[config.ENV_SERVICE_NAME] = 'Test service'
        # Create engine without any arguments
        api = EngineApi()
        # The temporary base directory should contain sub-folders for templates
        # and uploaded files. The directory also contains the database file
        tmpl_dir = os.path.join(TMP_DIR, config.TEMPLATE_DIR)
        self.assertTrue(os.path.isdir(tmpl_dir))
        upload_dir = os.path.join(TMP_DIR, config.UPLOAD_DIR)
        self.assertTrue(os.path.isdir(upload_dir))
        db_file = os.path.join(TMP_DIR, 'test.db')
        self.assertTrue(os.path.isfile(db_file))
        # Get the service descriptor
        service = api.service_descriptor()
        self.assertEqual(service[labels.NAME], 'Test service')
        self.assertEqual(service[labels.VERSION], api.version)
        links = hateoas.deserialize(service[labels.LINKS])
        self.assertEqual(len(links), 5)
        self.assertTrue(hateoas.SELF in links)
        self.assertTrue(hateoas.user(hateoas.LOGIN) in links)
        self.assertTrue(hateoas.user(hateoas.LOGOUT) in links)
        self.assertTrue(hateoas.user(hateoas.REGISTER) in links)
        self.assertTrue(hateoas.benchmark(hateoas.LIST) in links)
        # Make sure to close the database connesction
        api.close()

    def test_url_factory_init(self):
        """Test initializing the ulr factory with and without arguments."""
        os.environ[config.ENV_APIURL] = 'http://my.app/api'
        urls = UrlFactory(base_url='http://some.url/api////')
        self.assertEqual(urls.base_url, 'http://some.url/api')
        urls = UrlFactory()
        self.assertEqual(urls.base_url, 'http://my.app/api')


if __name__ == '__main__':
    import unittest
    unittest.main()
