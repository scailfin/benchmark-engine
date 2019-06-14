"""Constants and methods to serialize 'Hypermedia As The Engine Of Application
State' (HATEOAS) references that are included in API responses.
"""

import benchengine.api.serialize.labels as labels


"""Definition of common HATEOAS link relationship types."""
ADD = 'add'
CREATE = 'create'
DELETE = 'delete'
DOWNLOAD = 'download'
JOIN = 'join'
LEADERBOARD = 'leaderboard'
LEAVE = 'leave'
LIST = 'list'
LOGIN = 'login'
LOGOUT = 'logout'
REGISTER = 'register'
SELF = 'self'
SERVICE = 'service'
TEAMS = 'teams'
UPDATE = 'update'
UPLOAD = 'upload'

# ------------------------------------------------------------------------------
# Reference categories
# ------------------------------------------------------------------------------
def benchmark(rel):
    """Add relationship category prefix for benchmark resources.

    Parameters
    ----------
    rel: string
        Link relationship identifier

    Returns
    -------
    string
    """
    return 'benchmarks:{}'.format(rel)


def category(name, rel):
    """Add relationship category prefix for API resources.

    Parameters
    ----------
    name: string
        Resource type name
    rel: string
        Link relationship identifier

    Returns
    -------
    string
    """
    return '{}:{}'.format(name, rel)


def user(rel):
    """Add relationship category prefix for user resources.

    Parameters
    ----------
    rel: string
        Link relationship identifier

    Returns
    -------
    string
    """
    return 'users:{}'.format(rel)


# ------------------------------------------------------------------------------
# Helper methods for serialization
# ------------------------------------------------------------------------------
def deserialize(links):
    """Deserialize a list of HATEOAS reference objects into a dictionary.

    Parameters
    ----------
    links: list(dict)
        List of HATEOAS references in default serialization format

    Returns
    -------
    dict
    """
    result = dict()
    for link in links:
        result[link[labels.REL]] = link[labels.REF]
    return result


def serialize(links):
    """Serialize a given set of HATEOAS references. Each reference is an entry
    in the given dictionary. The key defines the HATEOAS relationship type for
    the link and the assiciated value is the link target Url.

    Parameters
    ----------
    links: dict()
        Dictionary of link relationship and link target entries

    Returns
    -------
    dict
    """
    return [{labels.REL: key, labels.REF: links[key]} for key in links]
