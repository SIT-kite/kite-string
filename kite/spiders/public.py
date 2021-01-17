from typing import List, Tuple

import scrapy

from ..items import AttachmentItem, PageItem


def get_links(response: scrapy.http.Response) -> List[Tuple[str or None, str]]:
    """
    Get links in the page.
    :param response: A scrapy.http.Response that contains the page
    :return: A list of tuple (title, url)
    """
    link_list = [(a_node.xpath('.//text()').get(), a_node.attrib['href'])  # Make a tuple of title, href
                 for a_node in response.css('a[href]')]
    return link_list


def filter_links(link_list: List[Tuple]) -> List[Tuple]:
    """
    Filter links which starts with 'javascript:' and so on.
    :param link_list: Original list to filter.
    :return: A filtered link list.
    """
    forbidden_link_prefix_set = {
        # Some are from https://developer.mozilla.org/zh-CN/docs/Web/HTML/Element/a
        '#', 'javascript:', 'mailto:', 'file:', 'ftp:', 'blob:', 'data:'
    }

    def is_forbidden_url(url: str) -> bool:
        for prefix in forbidden_link_prefix_set:
            if url.startswith(prefix):
                return True
        return False

    def is_allowed(url: str) -> bool:
        return not is_forbidden_url(url) and '.sit.edu.cn' in url

    return [(title, url) for title, url in link_list if is_allowed(url)]


class PublicFileSpider(scrapy.Spider):
    name = 'public'
    allowed_domains = []
    start_urls = 'https://www.sit.edu.cn/'

    def start_requests(self):
        """"
        Handler to the initial process.
        """
        yield scrapy.Request(url=self.start_urls, callback=self.parse, cb_kwargs={'title': None})

    def parse(self, response: scrapy.http.Response, **kwargs):
        """
        Page parser.
        :param response: Page response object.
        :param kwargs: A dictionary of parameters.
        :return: None
        """

        # Note: response.headers is a caseless dict.
        meta_type = response.headers.get('Content-Type').decode('utf-8')  # bytes to str
        if 'text/html' in meta_type:
            item = PageItem()

            item['link_count'] = len(response.css('a[href]'))
            item['title'] = response.xpath('//title/text()').get()

        else:
            item = AttachmentItem()

            item['title'] = kwargs['title']  # Take file title from last page.
            item['size'] = int(response.headers.get('Content-Length') or 0)

        item['meta_type'] = meta_type
        item['url'] = response.url
        item['publish_time'] = response.headers.get('Last-Modified')
        item['content'] = response.body

        # Submit the item to pipeline.
        yield item

        # Get other links from the page and append them to url list if current item is a html file.
        if 'text/html' in meta_type:
            # Add the other links to the link list.
            link_list = get_links(response)
            link_list = filter_links(link_list)

            for title, url in link_list:
                url = response.urljoin(url)
                yield scrapy.Request(url=url, callback=self.parse, cb_kwargs={'title': title})
