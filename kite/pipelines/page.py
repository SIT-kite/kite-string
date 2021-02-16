# -*- coding: utf-8 -*-
# @Time    : 2021/2/11 17:15
# @Author  : sunnysab
# @File    : page.py

import re

import scrapy
from lxml import etree

from . import create_connection_pool
from .. import divide_url
from ..items import PageItem

URL_DATE_PATTERN = re.compile(r'/(20[012]\d/\d{4})/')


def try_parse_date(url: str) -> str or None:
    """
    Try to parse date from Url.
    :param url:
    :return:
    """

    '''
    For the CMS of Sit using now, date is usually hide in article url like:
        '/2020/0909/c12570a187683/page.htm'
        '/_t158/2017/0420/c4296a115862/page.htm'
    It's easy to use regex to capture it.
    '''
    if url:
        r = URL_DATE_PATTERN.search(url)
        if r:
            date_str = r.group(1)
            year = date_str[:4]
            month = date_str[-4:-2]
            day = date_str[-2:]

            return f'{year}-{month}-{day}'


class PagePipeline:

    def __init__(self):
        self.pg_pool = create_connection_pool()

    def submit_item(self, cursor, item: PageItem):
        insert_sql = \
            f'''
            -- (_title text, _host text, _path text, _publish_date date, _link_count integer, _content text)
            
            CALL public.submit_page(%s, %s, %s, %s, %s, %s);
            '''

        host, path = divide_url(item['url'])
        cursor.execute(insert_sql,
                       (item['title'], host, path, item['publish_time'], item['link_count'], item['content']))

    SPACES_PATTERN = re.compile(r'\n\n*')

    def process_item(self, item: PageItem, spider: scrapy.Spider):
        if item and isinstance(item, PageItem):
            ''' Extract main content from html. '''

            def clean_p(s: str) -> str:
                return s.replace('\xa0', ' ').strip()

            def clean_all(s: str) -> str:
                s = self.SPACES_PATTERN.sub('\n\n', s)
                s = s.strip()
                return s

            page = etree.HTML(item['content'])
            paragraphs = [clean_p(p.xpath('string(.)')) for p in page.xpath('//p')]

            item['publish_time'] = try_parse_date(item['url'])
            item['content'] = clean_all('\n'.join(paragraphs))
            self.pg_pool.runInteraction(self.submit_item, item)
        else:
            return item
