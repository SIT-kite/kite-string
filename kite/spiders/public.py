from readability import Document

from . import *
from .. import divide_url
from ..items import AttachmentItem, PageItem


class PublicPageSpider(scrapy.Spider):
    name = 'public'
    allowed_domains = []
    start_urls = 'https://www.sit.edu.cn/'

    def start_requests(self):
        """"
        Handler to the initial process.
        """
        yield scrapy.Request(url=self.start_urls, callback=self.parse)

    def parse(self, response: scrapy.http.Response, **kwargs):
        """
        Page parser.
        :param response: Page and response object.
        :param kwargs: A dict of parameters.
        :return: None
        """

        content_type: bytes = response.headers.get('Content-Type')
        if not content_type.startswith(b'text/html'):
            return None

        # Note: response.headers is a caseless dict.
        this_page = PageItem()
        article = Document(response.text, handle_failures=None)
        this_page['link_count'] = len(response.css('a[href]'))
        this_page['title'] = article.title()
        this_page['url'] = response.url
        this_page['content'] = article.summary()

        # Submit the this_page to pipeline.
        yield this_page

        # Get other links from the page and append them to url list
        link_list = get_links(response)
        for title, url in link_list:
            title = title.strip() if title else ''
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
                yield scrapy.Request(url=url, callback=self.parse)

            elif link_type == 'attachment':  # link_type may equal to 'attachment'
                item = AttachmentItem()

                item['referer'] = response.url  # Url of current web page
                item['url'] = url  # Url of attachment
                item['title'] = title.replace('\xa0', '').replace(' ', '')  # Take file title from last page.
                yield item
