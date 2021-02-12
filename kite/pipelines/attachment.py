# -*- coding: utf-8 -*-
# @Time    : 2021/2/12 17:32
# @Author  : sunnysab
# @File    : attachment.py

import os

import scrapy

from . import download_directory
from . import open_database, get_database
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
    pg_client = None
    pg_cursor = None

    def __init__(self):
        pass

    def open_spider(self, spider: scrapy.Spider):
        open_database()

        self.pg_client = get_database()
        self.pg_cursor = self.pg_client.cursor()
        spider.log('One Pg client opened.')

    def close_spider(self, spider: scrapy.Spider):
        self.pg_client.commit()
        spider.log('One Pg client committed and closed.')

    def submit_item(self, item: AttachmentItem, spider: scrapy.Spider):
        insert_sql = \
            f'''
            INSERT INTO 
                attachments (title, host, path, ext, size, local_name, checksum)
            VALUES 
                (%s, %s, %s, %s, %s, %s, %s);
            '''

        host, path = divide_url(item['url'])
        ext = get_file_extension(path)
        local_name = item['path']
        size = get_file_size(local_name)
        checksum = item['checksum']
        try:
            self.pg_cursor.execute(insert_sql,
                                   (item['title'], host, path, ext, size, local_name, checksum))
            self.pg_client.commit()
        except Exception as e:
            spider.logger.error(f'Error while submitting item {item} to pg, detail: {e}')

    def process_item(self, item: AttachmentItem, spider: scrapy.Spider):
        if item and isinstance(item, AttachmentItem):
            self.submit_item(item, spider)

        return item
