from typing import Tuple
from urllib.parse import urlparse

from psycopg import Connection, connect
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


def open_database() -> Connection:
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

    conn = connect(dbname=database, user=username, password=password, host=host, port=port, autocommit=True)
    with conn.cursor() as cursor:
        cursor.execute("SET client_encoding TO 'UTF8'")
    return conn


def get_database():
    return open_database()
