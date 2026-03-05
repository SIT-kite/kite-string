# -*- coding: utf-8 -*-
# @Time    : 2021/2/14 12:32
# @Author  : sunnysab
# @File    : dupfilters.py

import hashlib

import scrapy
from pybloom_live import ScalableBloomFilter
from scrapy.dupefilters import BaseDupeFilter

from kite import get_database, divide_url


class PageDupeFilter(BaseDupeFilter):
    """
    PageDupeFilter

    The filter uses a bloom filter inside.
    It load processed page url from postgresql
    """

    def __init__(self, load_existing_urls: bool = True):
        self.__load_existing_urls = load_existing_urls
        self.__pg_client = get_database() if load_existing_urls else None
        self.__filter = ScalableBloomFilter(initial_capacity=2 * 10e5)

    @classmethod
    def from_settings(cls, settings):
        # Keep compatibility with old Scrapy code path.
        return cls._from_settings(settings)

    @classmethod
    def from_crawler(cls, crawler):
        return cls._from_settings(crawler.settings)

    @classmethod
    def _from_settings(cls, settings):
        load_existing_urls = settings.getbool('KITE_DUPEFILTER_LOAD_EXISTING_URLS', True)
        return cls(load_existing_urls=load_existing_urls)

    def request_seen(self, request: scrapy.Request) -> bool:
        host, path = divide_url(request.url)
        # Foot print = sha1(host + path)
        fp_s = (host + path).encode()
        fp = hashlib.sha1(fp_s).hexdigest()
        if fp in self.__filter:
            return True

        self.__filter.add(fp)
        return False

    def open(self):
        if not self.__load_existing_urls or self.__pg_client is None:
            return

        size = 100
        sql = 'SELECT DISTINCT host || path FROM public.pages'
        with self.__pg_client.cursor() as cursor:
            cursor.execute(sql)
            b_continue = True

            while b_continue:
                result = cursor.fetchmany(size)
                for r in result:
                    fp_s = (r[0]).encode()
                    fp = hashlib.sha1(fp_s).hexdigest()
                    self.__filter.add(fp)
                if len(result) < size:
                    b_continue = False

        self.__pg_client.close()
        self.__pg_client = None

    def close(self, reason):
        pass

    def log(self, request, spider):
        pass
