from typing import List, Tuple

import scrapy

from ..items import FileItem


def get_links(response) -> List[Tuple[str or None, str]]:
    """
    Get links in the page.
    :param response: A scrapy.HttpResponse object that contains the page
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

    return [(title, url) for title, url in link_list if not is_forbidden_url(url)]


class PublicFileSpider(scrapy.Spider):
    name = 'public'
    allowed_domains  = []
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
        item = FileItem()

        # Note: response.headers is a caseless dict.
        item['meta_type'] = response.headers.get('Content-Type')
        item['url'] = response.url
        item['content'] = response.body
        item['title'] = kwargs['title'] or response.xpath('//title/text()').get()

        # Submit the item to pipeline.
        yield item

        # Check meta type, if current item is a html file, get other links from the page and append them to url list.
        if item['meta_type'] == b'text/html':
            # Add the other links to the link list.
            link_list = get_links(response)
            link_list = filter_links(link_list)

            for title, url in link_list:
                url = response.urljoin(url)
                yield scrapy.Request(url=url, callback=self.parse, cb_kwargs={'title': title})
