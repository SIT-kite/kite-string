# -*- coding: utf-8 -*-
# @Time    : 2021/2/21 19:10
# @Author  : sunnysab
# @File    : notice.py

import re

import scrapy
from lxml import etree

from . import create_connection_pool
from ..items import NoticeItem

UUID_PATTERN = re.compile(r'bulletinId=([0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12})')


def _parse_uuid_from_url(url: str) -> str:
    r = UUID_PATTERN.search(url)
    if r:
        return r.group(1)


class NoticePipeline:
    SPACES_PATTERN = re.compile(r'\n\n*')

    def __init__(self):
        self.pg_pool = create_connection_pool()

    def submit_item(self, cursor, item: NoticeItem):
        insert_sql = \
            '''
            -- (_id uuid, _title text, _publish_time timestamp with time zone, _department text, _publisher text, 
                _content text)
            
            CALL public.submit_notice(%s, %s, %s, %s, %s, %s);
            '''
        notice_id = _parse_uuid_from_url(item['id'])
        cursor.execute(insert_sql,
                       (notice_id, item['title'], item['publish_time'], item['department'], item['publisher'],
                        item['content']))

    def process_item(self, item: NoticeItem, spider: scrapy.Spider):
        if item and isinstance(item, NoticeItem):
            ''' Extract main content from html. '''

            def clean_p(s: str) -> str:
                return s.replace('\xa0', ' ').strip()

            def clean_all(s: str) -> str:
                s = self.SPACES_PATTERN.sub('\n\n', s)
                s = s.strip()
                return s

            page = etree.HTML(item['content'])
            paragraphs = [clean_p(p.xpath('string(.)')) for p in page.xpath('//p')]

            item['content'] = clean_all('\n'.join(paragraphs))
            self.pg_pool.runInteraction(self.submit_item, item)
        else:
            return item
