# -*- coding: utf-8 -*-
# @Time    : 2021/1/17 14:57:30
# @Author  : sunnysab
# @File    : caching.py

import scrapy
from scrapy.pipelines.files import FilesPipeline

from kite.items import StoreItem


class FileCachingPipeline(FilesPipeline):
    """
    Write files into disk cache, based on FilesPipeline in scrapy.
    """

    def get_media_requests(self, item: StoreItem, info):
        if not item:
            return None

        if 'cookies' in item:
            yield scrapy.Request(item['url'], meta={'title': item['title']}, cookies=item['cookies'])
        else:
            yield scrapy.Request(item['url'], meta={'title': item['title']})

    def media_downloaded(self, response, request, info, *, item=None):
        result = super().media_downloaded(response, request, info, item=item)
        if item is not None:
            item['size'] = len(response.body)
        return result

    def item_completed(self, results, item: StoreItem, info):
        # Use for statement to replace 'if let'
        for b_result, result_info in results:
            if b_result:
                item['checksum'] = result_info['checksum']
                item['path'] = result_info['path']
                if 'size' not in item:
                    item['size'] = -1
                return item
