import uuid
from typing import List, Tuple

import scrapy

from ..items import SitprojectItem


class SitEduSpider(scrapy.Spider):
    name = 'sit_edu'
    allowed_domains = []
    extensions = ['rar', 'xls', 'xlsx', 'doc', 'docx', 'zip', 'exe', 'pdf']
    start_urls = 'https://gs.sit.edu.cn/2020/1110/c5706a190002/page.htm'

    def start_requests(self):
        yield scrapy.Request(url=self.start_urls, callback=self.parse)

    def parse(self, response, **kwargs):
        item = SitprojectItem()

        content_type = response.headers.get('Content-Type')
        if content_type == 'text/html':
            item['html_url'] = response.url
            item['html_name'] = response.xpath('//title/text()').get()
            item['html_uuid'] = uuid.uuid5(uuid.NAMESPACE_URL, item['html_url'])
            item['html_body'] = response.body

            # Add the other links to the link list.
            link_list = self.get_links(response)
            for title, url in link_list:
                if '.sit.edu.cn' in url:
                    yield scrapy.Request(url=response.urljoin(url), callback=self.parse, cb_kwargs={'title': title})

        else:  # Save attachment
            item['file_url'] = response.url
            item['file_name'] = kwargs['meta']['title']
            item['file_body'] = response.body
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
