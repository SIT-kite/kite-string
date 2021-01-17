# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

import os
import uuid
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
    By the way, for url like 'http://www.sit.edu.cn/', the file extension is '' because we can not detect the truely
    extension section.
    :param file: Original file name
    :return: File extension
    """
    dot_pos = file.rfind('.')
    slash_pos = file.rfind('/')

    result = ''
    if slash_pos == -1: # It's a file name
        if dot_pos != -1:
            result = file[dot_pos + 1:]
        result = ''
    else: # It's an url string
        if dot_pos > slash_pos: # www.sit.edu.cn/index.html
            result = file[dot_pos + 1:]
        else:  # www.sit.edu.cn/
            result = ''
    return result


def generate_file_name(url: str, original_name: str) -> str:
    """
    Generate a file name using UUID5
    :param url: File url
    :param original_name: Original name
    :return: New file name
    """
    uuid_name = uuid.uuid5(uuid.NAMESPACE_URL, url)
    extension = get_file_extension(original_name) or get_file_extension(url)
    if not extension:
        # Set default extension as 'html' seems to be arbitrary, however,
        # When get_file_extension(url) returns an empty string, the file probably be a html file because
        # the file usually is the 'index.html' or 'php' or 'jsp' and so on.
        extension = 'html'

    return f'{uuid_name}.{extension}'


class FilePipeline:
    """
    File download pipeline.
    """
    def __init__(self):
        pass

    def process_item(self, item: FileItem, spider) -> FileItem:
        item['filename'] = generate_file_name(item['url'], item['title'])

        '''
        FileItem fields.
        title, filename, url, content, meta_type
        '''
        open('E:\\File\\' + item['filename'], 'wb+').write(item['content'])
        # open('filelist.txt', 'a+', encoding='utf-8').write()
        return item
