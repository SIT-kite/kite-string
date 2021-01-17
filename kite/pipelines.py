# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

import os
import uuid

import chardet
from gne import GeneralNewsExtractor

from .items import AttachmentItem, PageItem


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
        else:
            pass
    else:  # It's an url string
        if dot_pos > slash_pos:  # www.sit.edu.cn/index.html
            result = file[dot_pos + 1:]
        else:  # www.sit.edu.cn/
            pass
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
        extension = 'htm'

    return f'{uuid_name}.{extension}'


class FilePipeline:
    """
    File download pipeline.
    """
    extractor = None

    def __init__(self):
        self.extractor = GeneralNewsExtractor()

    def extract_main_page(self, html: str) -> dict:
        """
        Use GNE (GeneralNewsExtractor) to extract main content from html.
        :param html: Html page
        :return: A dict returned by extract method.
            Keys: title, author, publish_time, content, images
        """
        result = self.extractor.extract(html)
        return result

    def process_item(self, item: PageItem or AttachmentItem, spider) -> PageItem or AttachmentItem:
        item['filename'] = generate_file_name(item['url'], item['title'])

        if 'text/html' in item['meta_type']:
            # Check page encoding and use GNE to extract the main page.
            encoding_result = chardet.detect(item['content'])
            content = item['content'].decode(encoding_result['encoding'])
            parsed_page = self.extract_main_page(content)

            item['content'] = parsed_page.get('content')
            item['publish_time'] = parsed_page.get('publish_time')

        '''
        FileItem fields.
        title, filename, url, content, meta_type
        '''
        # open('E:\\File\\' + item['filename'], 'wb+').write(item['content'])
        # open('files.txt', 'a+', encoding='utf-8').write()
        return item
