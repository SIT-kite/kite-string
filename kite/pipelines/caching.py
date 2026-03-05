# -*- coding: utf-8 -*-
# @Time    : 2021/1/17 14:57:30
# @Author  : sunnysab
# @File    : caching.py

import logging

import scrapy
from scrapy.pipelines.files import FilesPipeline
from twisted.python.failure import Failure

from kite.items import StoreItem

logger = logging.getLogger(__name__)


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

    async def _check_media_to_download(self, request, info, item):
        try:
            self._modify_media_request(request)
            assert self.crawler.engine
            response = await self.crawler.engine.download_async(request)
            return self.media_downloaded(response, request, info, item=item)
        except Exception as exc:
            return self.media_failed(Failure(exc), request, info)

    def media_failed(self, failure, request, info):
        referer = request.headers.get('Referer', b'')
        if isinstance(referer, bytes):
            referer = referer.decode('latin1', errors='ignore')
        if not referer:
            referer = 'None'

        logger.warning(
            'File (download-failed): Error downloading file from %s referred in <%s>: %s',
            request,
            referer,
            failure.getErrorMessage(),
            extra={'spider': info.spider},
        )
        if self.crawler.stats:
            self.crawler.stats.inc_value('file_status_count/download-failed')
        return failure

    def item_completed(self, results, item: StoreItem, info):
        # Use for statement to replace 'if let'
        for b_result, result_info in results:
            if b_result:
                item['checksum'] = result_info['checksum']
                item['path'] = result_info['path']
                if 'size' not in item:
                    item['size'] = -1
                return item
