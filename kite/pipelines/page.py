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
TEXT_DATE_PATTERNS = (
    re.compile(r'发布(?:日期|时间)\s*[：:]\s*(20\d{2})[-./年](\d{1,2})[-./月](\d{1,2})'),
    re.compile(r'时间\s*[：:]\s*(20\d{2})[-./年](\d{1,2})[-./月](\d{1,2})'),
)


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


def try_parse_date_from_text(text: str) -> str | None:
    if not text:
        return None

    for pattern in TEXT_DATE_PATTERNS:
        matched = pattern.search(text)
        if not matched:
            continue

        year, month, day = matched.groups()
        return f'{year}-{int(month):02d}-{int(day):02d}'

    return None


class PagePipeline:
    SPACES_PATTERN = re.compile(r'\n\n*')
    PRIMARY_CONTENT_XPATHS = (
        '//*[@id="vsb_content"]',
        '//*[contains(concat(" ", normalize-space(@class), " "), " v_news_content ")]',
        '//*[contains(concat(" ", normalize-space(@class), " "), " wp_articlecontent ")]',
        '//*[contains(concat(" ", normalize-space(@class), " "), " article-content ")]',
        '//*[contains(concat(" ", normalize-space(@class), " "), " article_content ")]',
        '//*[contains(concat(" ", normalize-space(@class), " "), " Article_Content ")]',
    )

    def __init__(self):
        self.pg_pool = create_connection_pool()

    def submit_item(self, cursor, item: PageItem):
        insert_sql = \
            '''
            -- (_title text, _host text, _path text, _publish_date date, _link_count integer, _content text)
            
            CALL public.submit_page(%s, %s, %s, %s, %s, %s);
            '''

        host, path = divide_url(item['url'])
        cursor.execute(insert_sql,
                       (item['title'], host, path, item['publish_date'], item['link_count'], item['content']))

    def process_item(self, item: PageItem):
        if item and isinstance(item, PageItem):
            ''' Extract main content from html. '''

            def clean_p(s: str) -> str:
                return s.replace('\xa0', ' ').strip()

            def clean_all(s: str) -> str:
                s = self.SPACES_PATTERN.sub('\n\n', s)
                s = s.strip()
                return s

            def extract_text_from_node(node) -> str:
                return clean_all(node.xpath('string(.)'))

            def extract_main_content(page) -> str:
                for xpath in self.PRIMARY_CONTENT_XPATHS:
                    nodes = page.xpath(xpath)
                    for node in nodes:
                        text = extract_text_from_node(node)
                        if text:
                            return text

                paragraphs = [clean_p(p.xpath('string(.)')) for p in page.xpath('//p')]
                paragraph_text = clean_all('\n'.join(paragraphs))
                if paragraph_text:
                    return paragraph_text

                return clean_all(page.xpath('string(//body)'))

            page = etree.HTML(item['content'])
            full_text = clean_all(page.xpath('string(//body)')) if page is not None else ''

            item['publish_date'] = try_parse_date(item['url']) or try_parse_date_from_text(full_text)
            item['content'] = extract_main_content(page) if page is not None else ''
            self.pg_pool.runInteraction(self.submit_item, item)
        else:
            return item
