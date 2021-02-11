# -*- coding: utf-8 -*-
# @Time    : 2021/2/11 17:15
# @Author  : sunnysab
# @File    : page.py

import scrapy

from ..items import PageItem


class PagePipeline:
    def open_spider(self, spider: scrapy.Spider):
        pass

    def close_spider(self, spider: scrapy.Spider):
        pass

    def process_item(self, item: PageItem, spider: scrapy.Spider):
        if isinstance(item, PageItem):
            return item
