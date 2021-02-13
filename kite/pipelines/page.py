# -*- coding: utf-8 -*-
# @Time    : 2021/2/11 17:15
# @Author  : sunnysab
# @File    : page.py

import re
from typing import List

import chardet
import scrapy
from gne import GeneralNewsExtractor

from . import open_database, get_database
from .. import divide_url
from ..items import PageItem

DATE_PATTERN = re.compile(r'^(\d{4}-\d{1,2}-\d{1,2})$')
DATE_SEP_WORDS = re.compile(r'[年月/]')


def validate_date(date_str: str) -> str or None:
    """
    Validate a date string.
    :param date_str: date string like '2020-1-1', '2020年1月1日'...
    :return: None if failed. Otherwise returns a valid date string.
    """
    if date_str:
        date_str = DATE_SEP_WORDS.sub('-', date_str).replace('日', '')
        if DATE_PATTERN.match(date_str):
            return date_str
    return None


PAGE_DATE_PATTERN = re.compile(r'(?:(?:发布)?(?:时间|日期)[:：]\s?)(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}(日)?)\s')


def find_out_publish_date(html: str) -> str or None:
    """
    Find publish date by regex in html, used to replace the parser in Gne library.
    :param html: html
    :return:
    """
    r = PAGE_DATE_PATTERN.search(html)
    if r:
        return r.group(1)


def merge_paragraph(p_list: List[str]) -> List[str]:
    """
    Merge some single character to paragraph.
    Some characters in a paragraph are in different <span> tags. Gne library usually separates them into
    multiple paragraphs. This function is used to merge them.
    :param p_list: Paragraph list
    :return: Processed paragraph list
    """
    if len(p_list) <= 1:
        return p_list

    i, n = 1, len(p_list)
    result = [p_list[1]]

    while i < n:
        if len(p_list[i]) < 5:
            # Strip last paragraph and append current to it.
            result[-1] = p_list[-1].rstrip() + p_list[i]
        else:
            # Copy src to dst
            result.append(p_list[i])
        i += 1
    return result


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
                public.pages (title, host, path, publish_date, link_count, content)
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
            content = content.decode(encoding, errors='replace')
            try:
                result = self.gne_extractor.extract(content)
            except Exception as e:
                print(e)
                return
            item['title'] = result['title'] or item['title']
            item['publish_time'] = validate_date(find_out_publish_date(content))
            item['content'] = '\n'.join(merge_paragraph(result['content'].split('\n')))

            self.submit_item(item, spider)
        else:
            return item
