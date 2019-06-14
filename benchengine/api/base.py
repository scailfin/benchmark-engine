"""The API engine is a wrapper around the different system resources that
constitue the benchmark engine. The componets of the engine are the (i) user
manager, (ii) team manager, (iii) bechmark repository, and (iv) thebenchmark
engine. Together, these components implement all methods that are defined in
the API specification document (resources/api/v1/engine.yaml).

All API methods returns a dictionary serialization of the respective result.

The main purpose of having a separate API instance is to allow different server
implementations (e.g., Flask, Tornado) to be used to implement a web service for
the API.
"""

from benchengine.api.benchmark import BenchmarkApi
from benchengine.api.route import UrlFactory
from benchengine.api.serialize.base import Serializer
from benchengine.api.team import TeamApi
from benchengine.api.user import UserApi
from benchengine.benchmark.engine import BenchmarkEngine
from benchengine.benchmark.repo import BenchmarkRepository
from benchengine.db import DatabaseDriver
from benchengine.user.team.manager import TeamManager
from benchengine.user.manager import UserManager

import benchengine.config as config
import benchtmpl.util.core as util


class EngineApi(object):
    """The competition engine API is a wrapper for different API components that
    implement the methods that are specified in the API interface document. The
    main components of the API are the competition API, the team API, the file
    store API, and the user API.

    The engine connects to the database to store and retrieve all resource
    information. The engine maintains uploaded file and downloaded results for
    each team in a separate subfolder under a base directory.
    """
    def __init__(self, con=None, backend=None, base_dir=None, urls=None):
        """Initialize the database connection, the engine backend, the base
        directory for uploaded files. and the factory for API Urls.

        If connection or backend are not provided the instances will be created
        using the respective drivers and the configuration that is given in the
        environment variables.

        If the base directory is not given the value is expected to be
        contained in the environment variable 'benchengine_BASEDIR'. If the base
        directory does not exist it will be created.

        If the Url factory is not given it will be instatiated using the base
        Url that is expected to be present in the respective environment
        variable.

        Parameters
        ----------
        con: DB-API 2.0 database connection, optional
            Connection to underlying database
        backend: benchengine.benchmark.engine.BenchmarkEngine, optional
            Workflow execution backend
        base_dir: string, optional
            Path to directory to store uploaded and downloaded files
        urls: benchengine.api.route.UrlFactory, optional
            Factory for Urls to access API resources

        Raises
        ------
        ValueError
        """
        # Use database driver to get connection if the connection is not given
        self.con = con if not con is None else DatabaseDriver.connect()
        # Set the base directory (either from given argument value or from the
        # value of the environment variable). Raise error if the base directory
        # value is None. Otherwise, create the directory if it does not exist.
        self.base_dir = base_dir if not base_dir is None else config.get_base_dir()
        if self.base_dir is None:
            raise ValueError('no base directory given')
        util.create_dir(self.base_dir)
        # Use default benchmark engine if no backend is given
        self.backend = backend if not backend is None else BenchmarkEngine(self.con)
        # Create subfolder to store uploaded files for individual teams
        self.team_files_dir = config.get_upload_dir()
        util.create_dir(self.team_files_dir)
        # Set Url factory and serialized
        self.urls = urls if not urls is None else UrlFactory()
        self.serialize = Serializer(self.urls)

    def close(self):
        """Close the database connection when the API is no longer used."""
        self.con.close()

    def benchmarks(self):
        """Get API component that provides methods to list benchmarks that a
        user (or team) can submit solutions for.

        Returns
        -------
        benchengine.api.benchmark.BenchmarkApi
        """
        return BenchmarkApi(
            repository=BenchmarkRepository(con=self.con),
            backend=self.backend,
            urls=self.urls
        )

    @property
    def name(self):
        """Each instance of the API should have a (unique) name to identify it.

        Returns
        -------
        string
        """
        return config.get_service_name()

    def service_descriptor(self):
        """Get serialization of descriptor containing the basic information
        about the API.

        Returns
        -------
        dict
        """
        return self.serialize.service_descriptor(
            name=self.name,
            version=self.version
        )

    def teams(self):
        """Get the API component that implements methods to manage teams that
        the current user is an owner or a member of.

        Returns
        --------
        benchengine.api.team.TeamApi
        """
        return TeamApi(
            manager=TeamManager(con=self.con),
            base_dir=self.team_files_dir,
            urls=self.urls
        )

    def users(self):
        """Get API component to access and manipulate user resources.

        Returns
        -------
        benchengine.api.user.UserApi
        """
        return UserApi(manager=UserManager(con=self.con), urls=self.urls)

    @property
    def version(self):
        """Return the engine API version.

        Returns
        -------
        string
        """
        return '0.1.0'
