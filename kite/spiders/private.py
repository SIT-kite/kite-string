import re

import scrapy

from ..aes import *
from ..items import OaAnnouncementItem


def get_formdata(response):
    lt = response.xpath('/html/body/div[2]/div[2]/div[2]/div/div[3]/div/form/input[1]/@value').getall()[0]
    dllt = response.xpath('/html/body/div[2]/div[2]/div[2]/div/div[3]/div/form/input[2]/@value').getall()[0]
    execution = response.xpath('/html/body/div[2]/div[2]/div[2]/div/div[3]/div/form/input[3]/@value').getall()[0]
    eventId = response.xpath('/html/body/div[2]/div[2]/div[2]/div/div[3]/div/form/input[4]/@value').getall()[0]
    rmShowm = response.xpath('/html/body/div[2]/div[2]/div[2]/div/div[3]/div/form/input[5]/@value').getall()[0]

    username = 'user'

    key = response.xpath('/html/body/div[2]/div[2]/div[2]/div/div[3]/div/form/input[6]/@value').getall()[0]
    iv = rds(16)
    encrypt = Encrypt(key=key, iv=iv)
    password = encrypt.aes_encrypt(rds(64) + 'password')

    formdata = {
        'username': username,
        'password': password,
        'lt': lt,
        'dllt': dllt,
        'execution': execution,
        '_eventId': eventId,
        'rmShown': rmShowm,
    }
    return formdata


def get_links(response):
    link_list0 = [(a_node.xpath('.//text()').get(), a_node.attrib['href'])
                  for a_node in response.css('li a[href]') if
                  a_node.xpath('.//text()').get() and a_node.attrib['href'] != '#']
    link_list1 = [(a_node.xpath('.//text()').get(), a_node.attrib['href'])
                  for a_node in response.css('td>a[href]') if
                  a_node.xpath('.//text()').get() and a_node.attrib['href'] != '#']
    link_list = link_list1 + link_list0
    return link_list


def get_pages(response):
    pages = response.xpath('//div[@class="pagination-info clearFix"]/span/text()').get()
    lpage = pages.split('/')
    pages = lpage[1]
    return int(pages)


def str_spaceremove(oldstr):
    return re.sub('[ \n\t\r]', '', oldstr)


class OaannouncementSpider(scrapy.Spider):
    name = 'oAannouncement'
    login_url = 'https://authserver.sit.edu.cn/authserver/login?service=http%3A%2F%2Fmyportal.sit.edu.cn%2Findex.portal/'
    announcement_directory = [('学生事务',
                               'http://myportal.sit.edu.cn/detach.portal?pageIndex={}&groupid=&action=bulletinsMoreView&.ia=false&pageSize=&.pmn=view&.pen=pe2362'),
                              ('学习课堂',
                               'http://myportal.sit.edu.cn/detach.portal?pageIndex={}&groupid=&action=bulletinsMoreView&.ia=false&pageSize=&.pmn=view&.pen=pe2364'),
                              ('二级学院通知',
                               'http://myportal.sit.edu.cn/detach.portal?pageIndex={}&groupid=&action=bulletinsMoreView&.ia=false&pageSize=&.pmn=view&.pen=pe2368'),
                              ('校园文化',
                               'http://myportal.sit.edu.cn/detach.portal?pageIndex={}&groupid=&action=bulletinsMoreView&.ia=false&pageSize=&.pmn=view&.pen=pe2366'),
                              ('公告信息',
                               'http://myportal.sit.edu.cn/detach.portal?pageIndex={}&groupid=&action=bulletinsMoreView&.ia=false&pageSize=&.pmn=view&.pen=pe2367'),
                              ('生活服务',
                               'http://myportal.sit.edu.cn/detach.portal?pageIndex={}&groupid=&action=bulletinsMoreView&.ia=false&pageSize=&.pmn=view&.pen=pe2365'),
                              ('文件下载专区',
                               'http://myportal.sit.edu.cn/detach.portal?pageIndex={}&groupid=&action=bulletinsMoreView&.ia=false&pageSize=&.pmn=view&.pen=pe2382')]

    def start_requests(self):
        yield scrapy.Request(url=self.login_url,
                             dont_filter=True,
                             callback=self.post_login,
                             meta={'cookiejar': 1})

    def post_login(self, response):
        formdata = get_formdata(response)

        yield scrapy.FormRequest.from_response(
            response=response,
            url=self.login_url,
            method='POST',
            formdata=formdata,
            dont_filter=True,
            meta={'handle_httpstatus_list': [301, 302],
                  'cookiejar': response.meta['cookiejar']},
            callback=self.after_login
        )

    def after_login(self, response):
        for directory in self.announcement_directory:
            yield scrapy.Request(url=directory[1].format(1),
                                 dont_filter=True,
                                 meta={'cookiejar': response.meta['cookiejar']},
                                 callback=self.get_pages)

    def get_pages(self, response):
        pages = get_pages(response)
        for i in range(1, pages + 1):
            url = self.announcement_directory[0][1].format(i)
            yield scrapy.Request(url=url,
                                 dont_filter=True,
                                 meta={'cookiejar': response.meta['cookiejar']},
                                 callback=self.parse,
                                 cb_kwargs={'filesource': url})

    def parse(self, response, **kwargs):
        item = OaAnnouncementItem()
        item['fileurl'] = response.url
        item['filesource'] = kwargs['filesource']

        meta_type = response.headers.get('Content-Type').decode('utf-8')
        if 'text/html' in meta_type:
            if response.xpath('//div[@class="bulletin-title"]/text()').getall():
                item['filename'] = str_spaceremove(
                    response.xpath('//div[@class="bulletin-title"]/text()').getall()[0]) + '.html'
                item['body'] = response.text
                yield item

            links_list = get_links(response)
            for name, url in links_list:
                url = response.urljoin(url)
                yield scrapy.Request(
                    url=url,
                    meta={'cookiejar': response.meta['cookiejar']},
                    callback=self.parse,
                    dont_filter=True,
                    cb_kwargs={
                        'filesource': response.url,
                        'filename': name})
        else:
            item['filename'] = kwargs['filename']
            item['filebody'] = response.body
            yield item
