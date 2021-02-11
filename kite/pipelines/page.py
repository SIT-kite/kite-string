# -*- coding: utf-8 -*-
# @Time    : 2021/2/11 17:15
# @Author  : sunnysab
# @File    : page.py

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
        self.pg_cursor = self.pg_client.cursor()

    def close_spider(self, spider: scrapy.Spider):
        self.pg_client.commit()
        self.pg_cursor = None
        self.pg_client = None

    def submit_item(self, item: PageItem):
        insert_sql = \
            f'''
            INSERT INTO 
                files (a_title, a_publish_time, a_content, f_id)
            VALUES 
                ('{item['title']}', '{item['publish_time']}', '{item['content']}', null);
            '''

        self.pg_cursor.execute(insert_sql)
        self.pg_client.commit()

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

        result = self.gne_extractor.extract(content.decode(encoding))
        item['title'] = item['title'] or result['title']
        item['publish_time'] = result['publish_time']
        item['content'] = "".join(result['content'].replace('\n', '<br>').split())

        self.submit_item(item)

        item['is_continuing'] = False
        return item
