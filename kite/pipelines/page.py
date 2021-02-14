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


def merge_paragraph(p_list: List[str]) -> List[str]:
    """
    Merge some single character to paragraph.
    Some characters in a paragraph are in different <span> tags. Gne library usually separates them into
    multiple paragraphs. This function is used to merge them.
    :param p_list: Paragraph list
    :return: Processed paragraph list
    """

    def is_chinese_count_ge(s: str, c: int) -> bool:
        __count = 0
        for ch in s:
            if u'\u4e00' < ch < u'\u9fa5':
                __count += 1
                if __count == c:
                    return True
        return False

    if len(p_list) <= 1:
        return p_list

    i, n = 1, len(p_list)
    result = [p_list[0]]

    while i < n:
        if is_chinese_count_ge(p_list[i], 2):
            # Copy src to dst
            result.append(p_list[i])
        else:
            # Strip last paragraph and append current to it.
            result[-1] = result[-1].rstrip() + p_list[i]
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
            item['publish_time'] = try_parse_date(item['url'])
            item['content'] = '\n'.join(merge_paragraph(result['content'].split('\n')))

            self.submit_item(item, spider)
        else:
            return item
