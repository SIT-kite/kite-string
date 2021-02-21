from scrapy.utils.project import get_project_settings

from . import *
from ..auth import login
from ..items import NoticeItem, AttachmentItem


class OaPageSpider(scrapy.Spider):
    name = 'private'
    home_url = 'http://myportal.sit.edu.cn/'

    notice_sort = [
        ('学生事务', 'pe2362'),
        ('学习课堂', 'pe2364'),
        ('二级学院通知', 'pe2368'),
        ('校园文化', 'pe2366'),
        ('公告信息', 'pe2367'),
        ('生活服务', 'pe2365'),
        ('文件下载专区', 'pe2382')
    ]

    @staticmethod
    def _get_sort_page(sort_code: str, index: int):
        return f'http://myportal.sit.edu.cn/detach.portal?pageIndex={index}&action=bulletinsMoreView&.pen={sort_code}'

    def start_requests(self):
        # Note: login is a synchronized method
        settings = get_project_settings()
        user = settings.get('OA_USER')
        passwd = settings.get('OA_PASSWD')
        login_result = login(user, passwd, redirect=self.home_url)
        if type(login_result) == str:
            self.logger.critical('Login failed on authserver: {}', login_result)
            return

        self.log("Login successfully.")
        cookies = login_result.get_dict('myportal.sit.edu.cn', '/')
        for sort, sort_code in self.notice_sort:
            url = self._get_sort_page(sort_code, 1)
            # Request lists of notice whose sort in self.notice_sort
            yield scrapy.Request(url=url, callback=self.parse, cookies=cookies, dont_filter=True,
                                 cb_kwargs={'sort': sort},
                                 meta={'cookies': cookies})  # Use meta to transfer cookies to parse function.

    def parse(self, response, **kwargs):
        # There are two types of pages will be transferred to, and parsed in parse function
        # Notice list:
        # http://myportal.sit.edu.cn/detach.portal?action=bulletinsMoreView
        # Notice detail:
        # http://myportal.sit.edu.cn/detach.portal?action=bulletinBrowser
        # So it's necessary to check it before anything else.

        if 'action=bulletinBrowser' in response.url:
            return self.parse_notice_detail(response, **kwargs)
        elif 'action=bulletinsMoreView' in response.url:
            return self.parse_notice_list(response, **kwargs)
        else:
            # Unexpected page, maybe from detail page
            pass

    def parse_notice_detail(self, response, **kwargs):
        title = response.xpath('//div[@class="bulletin-title"]/text()').get()
        item = NoticeItem()
        item['url'] = response.url
        item['title'] = title.strip() if title else ''
        item['content'] = response.body
        item['sort'] = kwargs['sort']
        yield item

        # Check attachment
        cookies = response.meta['cookies']
        attachments = [(x, y) for x, y in get_links(response)  # title, url
                       if y.startswith('attachmentDownload.portal')]
        for title, url in attachments:
            item = AttachmentItem()

            item['referer'] = response.url  # Url of current notice
            item['url'] = response.urljoin(url)  # Url of attachment
            item['title'] = title.replace('\xa0', '').replace(' ', '')  # Take file title from last page.
            item['cookies'] = cookies
            yield item

    def parse_notice_list(self, response, **kwargs):
        link_list = get_links(response)
        cookies = response.meta['cookies']

        for title, url in link_list:
            url = response.urljoin(url)
            yield scrapy.Request(url=url, cookies=cookies, meta={'cookies': cookies}, callback=self.parse,
                                 cb_kwargs=kwargs)
