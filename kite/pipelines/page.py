# -*- coding: utf-8 -*-
# @Time    : 2021/2/11 17:15
# @Author  : sunnysab
# @File    : page.py

import re

import chardet
import scrapy
from gne import GeneralNewsExtractor

from . import open_database, get_database
from .. import divide_url
from ..items import PageItem

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
        open_database()

        self.pg_client = get_database()
        self.pg_cursor = self.pg_client.cursor()
        spider.log('One Pg client opened.')

    def close_spider(self, spider: scrapy.Spider):
        self.pg_client.commit()
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
        if item and isinstance(item, PageItem):
            ''' Extract main content from html. '''
            content = item['content']
            encoding = chardet.detect(content)['encoding']
            # Temp code.
            if encoding.startswith('gb'):
                encoding = 'gb18030'
            elif encoding.startswith('utf-'):
                encoding = 'utf-8'
            else:
                return

            result = self.gne_extractor.extract(content.decode(encoding, errors='replace'))
            item['title'] = item['title'] or result['title']
            item['publish_time'] = validate_date(result['publish_time'])
            item['content'] = result['content']

            self.submit_item(item, spider)

        else:
            return item
