import uuid

import scrapy

from ..items import SitprojectItem


class SitEduSpider(scrapy.Spider):
    item = SitprojectItem()
    name = 'sit_edu'
    allowed_domains = []
    start_urls = ['http://www.sit.edu.cn/']
    url_list = []

    def start_requests(self):
        yield scrapy.Request(url=self.start_urls[0], callback=self.parse)

    def parse(self, response, **kwargs):

        for j in response.xpath('//a/@href').getall():
            if 'http' not in j:
                j = 'https://www.sit.edu.cn' + j
            self.url_list.append(j)

        for i in range(len(self.url_list)):
            if 'mailto:' not in self.url_list[i]:
                yield scrapy.Request(url=self.url_list[i], callback=self.get_datas)

    def get_datas(self, response):
        namespace = uuid.NAMESPACE_URL
        self.item['url'] = response.url
        self.item['name'] = response.xpath('//title/text()').get()
        self.item['name'] = str(uuid.uuid5(namespace, self.item['url']))
        self.item['html_text'] = response.body
        if response.xpath('''//a[contains(@href, '.rar')]//text()''').getall():
            zip_name_list = []
            zip_url_list = []
            for zip_name in response.xpath('''//a[contains(@href, '.rar')]//text()''').getall():
                zip_name_list.append(zip_name.lstrip())
            for zip_url in response.xpath('''//a[contains(@href, '.rar')]/@href''').getall():
                if 'http' not in zip_url:
                    zip_url = 'https://www.sit.edu.cn' + zip_url
                zip_url_list.append(zip_url)
            for i in range(len(zip_name_list)):
                yield scrapy.Request(url=zip_url_list[i], callback=self.zip_parse)
                self.item['zip_name'] = zip_name_list[i]
                yield self.item
        else:
            try:
                self.item.pop('zip_name')
                self.item.pop('html_zip')
            except KeyError:
                pass
            yield self.item

    def zip_parse(self, response):
        self.item['html_zip'] = response.body
