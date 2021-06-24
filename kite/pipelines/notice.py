# -*- coding: utf-8 -*-
# @Time    : 2021/2/21 19:10
# @Author  : sunnysab
# @File    : notice.py

import re

import scrapy
from lxml import etree
from readability import Document

from . import create_connection_pool
from .. import divide_url
from ..items import NoticeItem

UUID_PATTERN = re.compile(r'bulletinId=([0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12})')
DATE_PATTERN = re.compile(r'发布时间：(\d{4}年\d{1,2}月\d{1,2}日 \d{2}:\d{2})')
DEPT_PATTERN = re.compile(r'发布部门：(.*?) [<|]')
AUTHOR_PATTERN = re.compile(r'title="点击查看相关信息">(.*?)</a>')


def _reformat_publish_time(time_string: str) -> str:
    return time_string \
        .replace('年', '-') \
        .replace('月', '-') \
        .replace('日', '')


def _find_publish_time(html: str) -> str:
    r = DATE_PATTERN.search(html)
    if r:
        return _reformat_publish_time(r.group(1))


def _find_department(html: str) -> str:
    r = DEPT_PATTERN.search(html)
    if r:
        return r.group(1).strip()


def _find_author(html: str) -> str:
    r = AUTHOR_PATTERN.search(html)
    if r:
        return r.group(1).strip()


class NoticePipeline:
    SPACES_PATTERN = re.compile(r'([\r\n]+\s*)+')

    def __init__(self):
        self.pg_pool = create_connection_pool()

    def submit_item(self, cursor, item: NoticeItem):
        insert_sql = \
            '''
            -- (_url text, _title text, _publish_time timestamp with time zone, _department text, _author text, _sort text, 
            -- _content text)
            
            CALL public.submit_notice(%s, %s, %s, %s, %s, %s, %s);
            '''
        host, path = divide_url(item['url'])
        url = host + path
        cursor.execute(insert_sql,
                       (url, item['title'], item['publish_time'], item['department'], item['author'], item['sort'],
                        item['content']))

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
            content = item['content'].decode('utf-8', 'replace')

            item['author'] = _find_author(content)
            item['department'] = _find_department(content)
            item['publish_time'] = _find_publish_time(content)

            article = Document(content, handle_failures=None)
            page = etree.HTML(article.summary())
            paragraphs = [clean_p(p.xpath('string(.)')) for p in page.xpath('//p')]
            item['content'] = clean_all('\n'.join(paragraphs))
            self.pg_pool.runInteraction(self.submit_item, item)
        else:
            return item
