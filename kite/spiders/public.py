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

        content_type: bytes | None = response.headers.get('Content-Type')
        if not content_type:
            return None

        mime_type = content_type.split(b';', 1)[0].strip().lower()
        if mime_type != b'text/html':
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

        seen_asset_urls = set()

        # Get other links from the page and append them to url list
        link_list = get_links(response)
        for title, url in link_list:
            title = title.strip() if title else ''
            url = response.urljoin(url)
            host, _ = divide_url(url)
            if host != 'sit.edu.cn' and not host.endswith('.sit.edu.cn'):
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

            elif link_type in {'attachment', 'image'}:
                if url in seen_asset_urls:
                    continue
                seen_asset_urls.add(url)

                item = AttachmentItem()

                item['referer'] = response.url  # Url of current web page
                item['url'] = url  # Url of asset (attachment or image)
                item['title'] = title.replace('\xa0', '').replace(' ', '')  # Take file title from last page.
                if len(item['title']) == 0:
                    fallback_name = path.split('?', 1)[0].split('#', 1)[0].rsplit('/', 1)[-1]
                    item['title'] = fallback_name[:128]
                yield item

        # Crawl embedded images even if there is no anchor to them.
        image_list = get_images(response)
        for alt, url in image_list:
            url = response.urljoin(url)
            host, _ = divide_url(url)
            if host != 'sit.edu.cn' and not host.endswith('.sit.edu.cn'):
                continue

            _, path = divide_url(url)
            if guess_link_type(path) != 'image':
                continue
            if url in seen_asset_urls:
                continue
            seen_asset_urls.add(url)

            item = AttachmentItem()
            item['referer'] = response.url
            item['url'] = url
            item['title'] = (alt or '').replace('\xa0', '').replace(' ', '')
            if len(item['title']) == 0:
                fallback_name = path.split('?', 1)[0].split('#', 1)[0].rsplit('/', 1)[-1]
                item['title'] = fallback_name[:128]
            yield item
