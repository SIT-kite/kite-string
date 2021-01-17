import scrapy
from typing import List, Tuple

from ..items import SitprojectItem


class SitEduSpider(scrapy.Spider):
    name = 'sit_edu'
    allowed_domains = []
    extensions = ['rar', 'xls', 'xlsx', 'doc', 'docx', 'zip', 'exe', 'pdf']
    start_urls = 'https://www.sit.edu.cn/'

    def start_requests(self):
        yield scrapy.Request(url=self.start_urls, callback=self.parse, cb_kwargs={'title': 'None'})

    def parse(self, response, **kwargs):
        item = SitprojectItem()

        content_type = response.headers.get('Content-Type')
        if content_type == b'text/html':
            item['url'] = response.url
            item['name'] = response.xpath('//title/text()').get()
            item['body'] = response.body
            item['Type'] = 'html'
            yield item

            # Add the other links to the link list.
            link_list = self.get_links(response)
            for title, url in link_list:
                url = response.urljoin(url)
                if 'sit.edu.cn' in url and 'mailto' not in url and '.js' not in url and '.css' not in \
                        url:
                    yield scrapy.Request(url=url, callback=self.parse, cb_kwargs={'title': title})

        else:  # Save attachment
            item['url'] = response.url
            item['name'] = response.cb_kwargs['title']
            item['body'] = response.body
            for Type in self.extensions:
                if Type in response.url:
                    item['Type'] = Type
                    yield item

    def get_links(self, response) -> List[Tuple[str or None, str]]:
        """
        Get links in the page.
        :param response: A scrapy.HttpResponse object that contains the page
        :return: A list of tuple (title, url)
        """
        link_list = [(a_node.xpath('.//text()').get(), a_node.attrib['href']) for a_node in response.css('a[href]')]
        return link_list

    def get_attachments(self, response) -> List[Tuple[str, str]]:

        def is_file_to_download(url: str) -> bool:
            sep_pos = url.rindex('.')
            extension = url[sep_pos:]

            return extension in self.extensions

        a_node_list = response.css('a')
        result = [(a_node.attrib['title'], a_node.attrib['href'])
                  for a_node in a_node_list
                  if is_file_to_download(a_node.attrib['href'])]

        return result
