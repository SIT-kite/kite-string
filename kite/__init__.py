from typing import Tuple
from urllib.parse import urlparse

from psycopg2.pool import ThreadedConnectionPool
from scrapy.utils.project import get_project_settings


def divide_url(url: str) -> Tuple[str, str]:
    """
    Given a full url and return a tuple of host and path.
    Parser is provided by urllib.
    :param url: a full url like 'http://sit.edu.cn/index.htm'
    :return: a tuple like ('sit.edu.cn', '/index.htm')
    """
    result = urlparse(url)
    host, path, query = result.netloc, result.path, result.query

    if len(path) == 0:
        path = '/'
    if len(query) != 0:
        path = path + '?' + query

    return host, path


def open_database():
    """
    Open database configured in scrapy settings.
    :return: If everything successful, returns a db client handler. While error occurred, it raise exceptions.
    """
    settings = get_project_settings()
    database = settings['PG_DATABASE']
    username = settings['PG_USERNAME']
    password = settings['PG_PASSWORD']
    host = settings['PG_HOST']
    port = settings['PG_PORT']

    pg_pool = ThreadedConnectionPool(2, 10, database=database, user=username, password=password,
                                     host=host, port=port)
    return pg_pool


# Global pg connection pool for pipelines.
__pg_pool: ThreadedConnectionPool = open_database()


def get_database():
    if __pg_pool:
        conn = __pg_pool.getconn()
        conn.autocommit = True
        conn.set_client_encoding('utf8')

        return conn
