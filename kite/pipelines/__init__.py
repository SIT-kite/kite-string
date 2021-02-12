# -*- coding: utf-8 -*-
# @Time    : 2021/2/11 17:14
# @Author  : sunnysab
# @File    : __init__.py

from psycopg2.pool import ThreadedConnectionPool
from scrapy.utils.project import get_project_settings

# Global pg connection pool for pipelines.
__pg_pool: ThreadedConnectionPool = None

# attachment directory
download_directory = get_project_settings()['FILES_STORE']


def open_database():
    """
    Open database configured in scrapy settings.
    :return: If everything successful, returns a db client handler. While error occurred, it raise exceptions.
    """
    global __pg_pool

    if __pg_pool:
        return None

    settings = get_project_settings()
    database = settings['PG_DATABASE']
    username = settings['PG_USERNAME']
    password = settings['PG_PASSWORD']
    host = settings['PG_HOST']
    port = settings['PG_PORT']

    pg_pool = ThreadedConnectionPool(2, 10, database=database, user=username, password=password,
                                     host=host, port=port)
    __pg_pool = pg_pool


def get_database():
    if __pg_pool:
        conn = __pg_pool.getconn()
        conn.set_client_encoding('utf8')

        return conn


# Exports
from .page import PagePipeline
from .caching import FileCachingPipeline
from .attachment import AttachmentPipeline
