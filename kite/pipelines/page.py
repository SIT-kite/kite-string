# -*- coding: utf-8 -*-
# @Time    : 2021/2/11 17:15
# @Author  : sunnysab
# @File    : page.py

import re
from typing import Tuple
from urllib.parse import urlparse

import chardet
import psycopg2
import scrapy
from gne import GeneralNewsExtractor
from scrapy.utils.project import get_project_settings

from ..items import PageItem


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

    db = psycopg2.connect(database=database, user=username, password=password,
                          host=host, port=port)
    return db


def divide_url(url: str) -> Tuple[str, str]:
    """
    Given a full url and return a tuple of host and path.
    Parser is provided by urllib.
    :param url: a full url like 'http://sit.edu.cn/index.htm'
    :return: a tuple like ('sit.edu.cn', '/index.htm')
    """
    result = urlparse(url)
    return result.netloc, result.path


DATE_PATTERN = re.compile(r'\d{4}-\d{1,2}-\d{1,2}')
DATE_SEP_WORDS = re.compile(r'[年月/]')


def validate_date(date_str: str) -> str or None:
    """
    Validate a date string.
    :param date_str: date string like '2020-1-1', '2020年1月1日'...
    :return: None if failed. Otherwise returns a valid date string.
    """
    date_str = DATE_SEP_WORDS.sub('-', date_str).replace('日', '')
    if DATE_PATTERN.match(date_str):
        return date_str
    return None


class PagePipeline:
    pg_client = None
    pg_cursor = None

    gne_extractor = None

    def __init__(self):
        self.gne_extractor = GeneralNewsExtractor()

    def open_spider(self, spider: scrapy.Spider):
        if self.pg_client is not None:
            spider.logger.warning('pg_client is already opened while connecting in open_spider.')
            self.pg_client = None  # Python interpreter will close it automatically.

        self.pg_client = open_database()
        self.pg_client.set_client_encoding('UTF8')
        self.pg_cursor = self.pg_client.cursor()
        spider.log('One Pg client opened.')

    def close_spider(self, spider: scrapy.Spider):
        self.pg_client.commit()
        self.pg_cursor = None
        self.pg_client = None
        spider.log('One Pg client committed and closed.')

    def submit_item(self, item: PageItem, spider: scrapy.Spider):
        insert_sql = \
            f'''
            INSERT INTO 
                pages (title, host, path, publish_date, link_count, content)
            VALUES 
                (%s, %s, %s, %s, %s, %s);
            '''

        host, path = divide_url(item['url'])
        try:
            self.pg_cursor.execute(insert_sql,
                                   (item['title'], host, path, item['publish_time'], item['link_count'],
                                    item['content']))
            self.pg_client.commit()
        except Exception as e:
            spider.logger.error(f'Error while submitting item {item} to pg, detail: {e}')

    def process_item(self, item: PageItem, spider: scrapy.Spider):
        if not item['is_continuing'] or not isinstance(item, PageItem):
            return item

        ''' Extract main content from html. '''
        content = item['content']
        encoding = chardet.detect(content)['encoding']
        # Temp code.
        if encoding.startswith('gb'):
            encoding = 'gb18030'
        elif encoding.startswith('utf-'):
            encoding = 'utf-8'
        else:
            item['is_continuing'] = False
            return item

        result = self.gne_extractor.extract(content.decode(encoding, errors='replace'))
        item['title'] = item['title'] or result['title']
        item['publish_time'] = validate_date(result['publish_time'])
        item['content'] = result['content']

        self.submit_item(item, spider)

        item['is_continuing'] = False
        return item
