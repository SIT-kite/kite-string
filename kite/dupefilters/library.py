# -*- coding: utf-8 -*-
# @Time    : 2021/7/11 7:18
# @Author  : sunnysab
# @File    : book.py

import logging
import re
from typing import Set

import scrapy
from scrapy.dupefilters import RFPDupeFilter

from kite import get_database


class LibraryDupeFilter(RFPDupeFilter):
    """
    LibraryDupeFilter

    This filter works on Book spider.
    It pull books already store in database and cached here.
    """

    __PATTERN_BOOK_URL = re.compile(r'/opac/book/(\d+)')

    def __init__(self, path=None, debug=False):
        super().__init__(path, debug)

        self.__pg_client = get_database()
        self.__filter: Set[int] = set()
        self.logger = logging.getLogger(__name__)

    def request_seen(self, request: scrapy.Request) -> bool:
        book_id = self._parse_book_url(request.url)
        # If we want to request the book detail page
        if book_id != 0:
            if book_id in self.__filter:
                return True

            self.__filter.add(book_id)

        return super().request_seen(request)

    def open(self):
        super().open()

        batch_size = 100
        book_count = 0
        sql = 'SELECT book_id FROM public.book;'

        with self.__pg_client.cursor() as cursor:
            cursor.execute(sql)
            b_continue = True

            while b_continue:
                results = cursor.fetchmany(batch_size)
                for r in results:
                    book_id = int(r[0])
                    self.__filter.add(book_id)

                book_count += len(results)
                if len(results) < batch_size:
                    b_continue = False

        self.__pg_client.close()
        self.__pg_client = None
        self.logger.info(f'Load {book_count} books\' id from database.')

    def _parse_book_url(self, url: str) -> int:
        result = self.__PATTERN_BOOK_URL.search(url)
        if result:
            return int(result[1])
        return 0
