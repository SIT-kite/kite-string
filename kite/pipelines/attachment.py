# -*- coding: utf-8 -*-
# @Time    : 2021/2/12 17:32
# @Author  : sunnysab
# @File    : attachment.py

import os
from urllib.parse import parse_qs

import scrapy

from . import download_directory, create_connection_pool
from .. import divide_url
from ..items import AttachmentItem


def get_file_extension(path: str, title: str = '', local_name: str = '') -> str:
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

    normalized_path = path
    if '#' in normalized_path:
        normalized_path = normalized_path.split('#', 1)[0]

    base_path, _, query = normalized_path.partition('?')
    query_params = parse_qs(query, keep_blank_values=True)

    for key in ('e', 'ext', 'extension', 'suffix'):
        values = query_params.get(key)
        if not values:
            continue

        extension = values[0].strip().lower()
        if extension.startswith('.'):
            extension = extension[1:]
        if extension:
            return extension

    normalized_path = base_path

    dot_pos = normalized_path.rfind('.')
    slash_pos = normalized_path.rfind('/')

    result = ''
    if slash_pos == -1:  # It's a file name
        if dot_pos != -1:
            result = normalized_path[dot_pos + 1:]
        else:
            pass
    else:  # It's an path string
        if dot_pos > slash_pos:  # www.sit.edu.cn/index.html
            result = normalized_path[dot_pos + 1:]
        else:  # www.sit.edu.cn/
            pass

    if result in {'jsp', 'vsb', ''}:
        for candidate in (title, local_name):
            if not candidate:
                continue

            candidate = candidate.split('?', 1)[0].split('#', 1)[0]
            candidate_dot_pos = candidate.rfind('.')
            candidate_slash_pos = candidate.rfind('/')
            if candidate_dot_pos > candidate_slash_pos:
                candidate_ext = candidate[candidate_dot_pos + 1:].lower()
                if candidate_ext:
                    return candidate_ext

    return result.lower()


def get_file_size(path: str) -> int:
    """
    Get file size in bytes.
    :param path: file path on disk
    :return: -1 if file not exists, otherwise the file size
    """
    if '://' in download_directory:
        return -1

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
        local_name = item['path']
        ext = get_file_extension(path, item.get('title', ''), local_name)
        size = item.get('size')
        if size is None:
            size = get_file_size(local_name)
        checksum = item['checksum']
        referer = item['referer']

        cursor.execute(insert_sql,
                       (item['title'], host, path, ext, size, local_name, checksum, referer))

    def process_item(self, item: AttachmentItem):
        if item and isinstance(item, AttachmentItem):
            self.pg_pool.runInteraction(self.submit_item, item)

        return item
