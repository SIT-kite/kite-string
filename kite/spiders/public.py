from typing import List, Tuple

import scrapy

from .. import divide_url
from ..items import AttachmentItem, PageItem


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


def get_links(response: scrapy.http.Response) -> List[Tuple[str or None, str]]:
    """
    Get links in the page.
    :param response: A scrapy.http.Response that contains the page
    :return: A list of tuple (title, url)
    """
    link_list = [(a_node.xpath('.//text()').get(), a_node.attrib['href'])  # Make a tuple of title, href
                 for a_node in response.css('a[href]')]
    return filter_links(link_list)


def guess_link_type(path: str) -> str:
    """
    Guess link type by path
    :param path: Path in url.
    :return: 'page' if it seems like a page.
             'attachment' if it seems like an attachment.
             'unknown' if we don't know.
    """

    page_postfix_set = {
        'asp', 'aspx', 'jsp', 'do', 'htm', 'html', 'php', 'cgi', '/', 'portal', 'action'
    }

    attachment_postfix_set = {
        '7z', 'zip', 'rar',
        'xls', 'xlsx', 'doc', 'docx', 'ppt', 'pptx', 'pdf'
    }

    for each_postfix in page_postfix_set:
        if path.endswith(each_postfix):
            return 'page'

    for each_postfix in attachment_postfix_set:
        if path.endswith(each_postfix):
            return 'attachment'

    return 'unknown'


class PublicPageSpider(scrapy.Spider):
    name = 'public'
    allowed_domains = []
    start_urls = 'https://www.sit.edu.cn/14256/list.htm'

    def start_requests(self):
        """"
        Handler to the initial process.
        """
        yield scrapy.Request(url=self.start_urls, callback=self.parse, cb_kwargs={'title': None})

    def parse(self, response: scrapy.http.Response, **kwargs):
        """
        Page parser.
        :param response: Page and response object.
        :param kwargs: A dict of parameters.
        :return: None
        """

        # Note: response.headers is a caseless dict.
        this_page = PageItem()
        this_page['link_count'] = len(response.css('a[href]'))
        this_page['title'] = response.xpath('//title/text()').get() or kwargs['title']
        this_page['url'] = response.url
        this_page['publish_time'] = response.headers.get('Last-Modified')
        this_page['content'] = response.body

        # Submit the this_page to pipeline.
        yield this_page

        # Get other links from the page and append them to url list
        link_list = get_links(response)
        for title, url in link_list:
            url = response.urljoin(url)
            if '.sit.edu.cn' not in url:
                continue

            """
            Separate pages from attachments.
            We may fetch the url and see what server say in 'Content-Type' but it can't be done in parse
            function. Actually, it's the simplest way to distinguish pages and attachments without fetching. 
            """
            _, path = divide_url(url)
            link_type = guess_link_type(path)
            if link_type == 'page':
                # Fetch next page
                yield scrapy.Request(url=url, callback=self.parse, cb_kwargs={'title': title})

            elif link_type == 'attachment':  # link_type may equal to 'attachment'
                item = AttachmentItem()

                item['url'] = url
                item['title'] = title  # Take file title from last page.
                yield item
