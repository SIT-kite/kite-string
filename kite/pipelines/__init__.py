# -*- coding: utf-8 -*-
# @Time    : 2021/2/11 17:14
# @Author  : sunnysab
# @File    : __init__.py

from scrapy.utils.project import get_project_settings
from twisted.enterprise import adbapi

# attachment directory
download_directory = get_project_settings()['FILES_STORE']


def initial_connection(conn):
    conn.autocommit = True
    conn.set_client_encoding('utf8')


def create_connection_pool() -> adbapi.ConnectionPool:
    settings = get_project_settings()
    params = {
        'database': settings['PG_DATABASE'],
        'host': settings['PG_HOST'],
        'port': settings['PG_PORT'],
        'user': settings['PG_USERNAME'],
        'password': settings['PG_PASSWORD'],
    }
    pool = adbapi.ConnectionPool('psycopg2', cp_openfun=initial_connection, **params)
    return pool


# Exports
from .page import PagePipeline
from .caching import FileCachingPipeline
from .attachment import AttachmentPipeline
