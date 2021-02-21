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
DATE_PATTERN = re.compile(r'发布时间：(\d{4}年\d{1,2}月\d{1,2}日 \d{2}:\d{2})')


def _reformat_publish_time(time_string: str) -> str:
    return time_string \
        .replace('年', '-') \
        .replace('月', '-') \
        .replace('日', '')


def _find_publish_time(html: str) -> str:
    r = DATE_PATTERN.search(html)
    if r:
        return _reformat_publish_time(r.group(1))


def _parse_uuid_from_url(url: str) -> str:
    r = UUID_PATTERN.search(url)
    if r:
        return r.group(1)


class NoticePipeline:
    SPACES_PATTERN = re.compile(r'([\r\n]+\s*)+')

    def __init__(self):
        self.pg_pool = create_connection_pool()

    def submit_item(self, cursor, item: NoticeItem):
        insert_sql = \
            '''
            -- (_id uuid, _title text, _publish_time timestamp with time zone, _department text, _publisher text, 
            --  _content text)
            
            CALL public.submit_notice(%s, %s, %s, %s, %s, %s);
            '''
        notice_id = _parse_uuid_from_url(item['url'])
        cursor.execute(insert_sql,
                       (notice_id, item['title'], item['publish_time'], '', '', item['content']))

    def process_item(self, item: NoticeItem, spider: scrapy.Spider):
        if item and isinstance(item, NoticeItem):
            ''' Extract main content from html. '''

            def clean_p(s: str) -> str:
                return s.replace('\xa0', ' ').strip()

            def clean_all(s: str) -> str:
                s = self.SPACES_PATTERN.sub('\n', s)
                s = s.strip()
                return s

            """ Expel non-UTF8 characters. """
            content = item['content'].encode('utf-8')
            content = content.decode('utf-8', 'replace')

            item['publish_time'] = _find_publish_time(content)
            page = etree.HTML(content)
            paragraphs = [clean_p(p.xpath('string(.)')) for p in page.xpath('//p')]
            item['content'] = clean_all('\n'.join(paragraphs))
            self.pg_pool.runInteraction(self.submit_item, item)
        else:
            return item
