# -*- coding: utf-8 -*-
# @Time    : 2021/2/12 17:32
# @Author  : sunnysab
# @File    : attachment.py

import os

import scrapy

from . import download_directory, create_connection_pool
from .. import divide_url
from ..items import AttachmentItem


def get_file_extension(path: str) -> str:
    """
    Get file extension section from filename or path. If the file is not separated by dot(s),
    it returns an empty string.
    For example: '/index.html' -> 'html', '/index' -> ''
    By the way, for path like '/', the file extension is '' because we can not detect the truly
    extension section.
    :param path: file path in url
    :return: File extension
    """
    if not path:
        return ''

    dot_pos = path.rfind('.')
    slash_pos = path.rfind('/')

    result = ''
    if slash_pos == -1:  # It's a file name
        if dot_pos != -1:
            result = path[dot_pos + 1:]
        else:
            pass
    else:  # It's an path string
        if dot_pos > slash_pos:  # www.sit.edu.cn/index.html
            result = path[dot_pos + 1:]
        else:  # www.sit.edu.cn/
            pass
    return result


def get_file_size(path: str) -> int:
    """
    Get file size in bytes.
    :param path: file path on disk
    :return: -1 if file not exists, otherwise the file size
    """
    try:
        r = os.stat(download_directory + '/' + path)
        return r.st_size
    except FileNotFoundError:
        return -1


class AttachmentPipeline:

    def __init__(self):
        self.pg_pool = create_connection_pool()

    def submit_item(self, cursor, item: AttachmentItem):
        insert_sql = \
            f'''
            -- (_title text, _host text, _path text, _ext text, _size integer, _local_name text, _checksum text, 
            --  _referer text)
            
            CALL public.submit_attachment(%s, %s, %s, %s, %s, %s, %s, %s);
            '''

        host, path = divide_url(item['url'])
        ext = get_file_extension(path)
        local_name = item['path']
        size = get_file_size(local_name)
        checksum = item['checksum']
        referer = item['referer']

        cursor.execute(insert_sql,
                       (item['title'], host, path, ext, size, local_name, checksum, referer))

    def process_item(self, item: AttachmentItem, spider: scrapy.Spider):
        if item and isinstance(item, AttachmentItem):
            self.pg_pool.runInteraction(self.submit_item, item)

        return item
