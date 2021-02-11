# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

import hashlib
import os

import scrapy
from scrapy.pipelines.files import FilesPipeline

from .items import FileItem


def create_directory_if_not_exists(path: str) -> None:
    """
    Create directory if it not exists.
    :param path: Path in str.
    :return: None
    """
    if not os.path.exists(path):
        os.makedirs(path)


def get_file_extension(file: str) -> str:
    """
    Get file extension section from filename or url. If the file is not separated by dot(s),
    it returns an empty string.
    For example: 'index.html' -> 'html', 'index' -> ''
    By the way, for url like 'http://www.sit.edu.cn/', the file extension is '' because we can not detect the truly
    extension section.
    :param file: Original file name
    :return: File extension
    """
    if not file:
        return ''

    dot_pos = file.rfind('.')
    slash_pos = file.rfind('/')

    result = ''
    if slash_pos == -1:  # It's a file name
        if dot_pos != -1:
            result = file[dot_pos + 1:]
    else:  # It's an url string
        if dot_pos > slash_pos:  # www.sit.edu.cn/index.html
            result = file[dot_pos + 1:]
        # Else: www.sit.edu.cn/
    return result


def generate_file_name(url: str) -> str:
    """
    Generate a file name using UUID5
    :param url: File url
    :return: New file name
    """
    extension = get_file_extension(url)
    if not extension:
        # Set default extension as 'html' seems to be arbitrary, however,
        # When get_file_extension(url) returns an empty string, the file probably be a html file because
        # the file usually is the 'index.html' or 'php' or 'jsp' and so on.
        extension = 'htm'

    filename = hashlib.sha1(url.encode('utf-8')).hexdigest()
    return f'{filename}.{extension}'


class FileCachingPipeline(FilesPipeline):

    def get_media_requests(self, item: FileItem, info):
        yield scrapy.Request(item['url'], meta={'title': item['title']})

    def file_path(self, request, response=None, info=None, *, item=None):
        new_name = generate_file_name(request.url)

        return new_name

    def item_completed(self, results, item: FileItem, info):
        b_result, result_info = results[0]
        if not b_result:
            item['is_continuing'] = False
        else:
            item['checksum'] = result_info['checksum']
            item['path'] = result_info['path']

        return item
