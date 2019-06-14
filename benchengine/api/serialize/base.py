"""Base serializer interface. Includes implementation of base methods that are
used by several different serializers.
"""

import benchengine.api.serialize.hateoas as hateoas
import benchengine.api.serialize.labels as labels


class Serializer(object):
    """Basic serialization methods that are inherited by the more specific
    serializers for different API resources.
    """
    def __init__(self, urls):
        """Initialize the Url factory.

        Parameters
        ----------
        urls: benchengine.api.route.UrlFactory
            Factory for resource Urls
        """
        self.urls = urls

    def file_handle(self, fh, team_id):
        """Get serialization for a file handle. Each file is associated with a
        specific team that is identified by the given id.

        Parameters
        ----------
        fh: benchengine.filestore.base.FileHandle
            Handle for uploaded file
        team_id: string
            Unique team identifier

        Returns
        -------
        dict
        """
        return {
            labels.ID: fh.identifier,
            labels.NAME: fh.name,
            labels.CREATED_AT: fh.created_at.isoformat(),
            labels.FILESIZE: fh.size,
            labels.LINKS: hateoas.serialize({
                hateoas.DELETE: self.urls.delete_file(
                    team_id=team_id,
                    file_id=fh.identifier
                ),
                hateoas.DOWNLOAD: self.urls.download_file(
                    team_id=team_id,
                    file_id=fh.identifier
                )
            })
        }

    def service_descriptor(self, name, version):
        """Serialization of the service descriptor. The descriptor contains the
        service name, version, and a list of HATEOAS references.

        Parameters
        ----------
        name: string
            Service name
        version: string
            Service version number

        Returns
        -------
        dict
        """
        return {
            labels.NAME: name,
            labels.VERSION: version,
            labels.LINKS: hateoas.serialize({
                hateoas.SELF: self.urls.service_descriptor(),
                hateoas.user(hateoas.LOGIN): self.urls.login(),
                hateoas.user(hateoas.LOGOUT): self.urls.logout(),
                hateoas.user(hateoas.REGISTER): self.urls.logout(),
                hateoas.benchmark(hateoas.LIST): self.urls.list_benchmarks(),
            })
        }

    def success(self, links=None):
        """Simple object indicating successful operations that do not have any
        further return value. May contain an optinal list of HATEOAS references.

        Parameters
        ----------
        links: dict(), optional
            Optional list of HATEOAS references

        Returns
        -------
        dict
        """
        obj = {labels.STATE: 'SUCCESS'}
        # Add optional HATEOAS references if given
        if not links is None:
            obj[labels.LINKS] = hateoas.serialize(links)
        return obj
