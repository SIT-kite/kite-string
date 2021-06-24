import re
import scrapy

from ..items import BookItem


def get_links(response):
    book_links = response.xpath('//span[@class="bookmetaTitle"]/a/@href').getall()
    list_links = response.xpath('//div[@class="meneame"][1]/a/@href').getall()
    return book_links + list_links


def get_title(response):
    title = response.xpath('//h2/text()').get()
    if title is None:
        title = response.xpath('//tr/td[@class="rightTD"]/a[@href]/text()').get().strip()
    return title


def get_isbn_and_price(response, num):
    isbn_and_price_without_deal = response.xpath('//tr[{}]/td[@class="rightTD"]'.format(num))
    isbn_and_price = isbn_and_price_without_deal.xpath('string(.)').get().replace('\n', '').replace('\r', '')\
        .replace('\t', '').strip()
    isbn_or_none = re.search(r"(\d-?){13}|(\d-?){10}", isbn_and_price)
    if isbn_or_none is not None:
        isbn = isbn_or_none.group()
    else:
        isbn = ''
    price_with_word = re.search(r"价格：[\sa-zA-Z0-9.]+", isbn_and_price)
    if price_with_word is not None:
        price = re.sub('[价格：]', '', price_with_word.group())
    else:
        price = ''
    return isbn, price


def get_language(response, num):
    language_without_deal = response.xpath('//tr[{}]/td[@class="rightTD"]'.format(num))
    language = language_without_deal.xpath('string(.)').get().replace('\n', '').replace('\r', '').replace('\t', '')\
        .strip()
    return language


def get_author(response, num):
    author_and_book_without_deal = response.xpath('//tr[{}]/td[@class="rightTD"]'.format(num))
    author_and_book = author_and_book_without_deal.xpath('string(.)').get().replace('\n', '').replace('\r', '')\
        .replace('\t', '').strip()
    author_with_symbol = re.search(r"/[a-zA-Z\u4e00-\u9fa5().,·\s]+", author_and_book)
    if author_with_symbol is not None:
        author = re.sub('[/]', '', author_with_symbol.group())
    else:
        author = ''
    return author


def get_publish(response, num):
    publish_without_process = response.xpath('//tr[{}]/td[@class="rightTD"]'.format(num))
    publish = publish_without_process.xpath('string(.)').get().replace('\n', '').replace('\r', '').replace('\t', '').strip()
    publisher_place_without_deal = re.search('出版地：[\u4e00-\u9fa5]+', publish)
    if publisher_place_without_deal is not None:
        if publisher_place_without_deal.group() == '出版地：出版社':
            publisher_place = ''
        else:
            publisher_place = re.sub('[出版地：]', '', publisher_place_without_deal.group())
    else:
        publisher_place = ''

    publishing_house_without_deal = response.xpath('//tr[{}]/td[@class="rightTD"]/a/text()'.format(num)).get()
    publishing_house = publishing_house_without_deal.replace('\n', '').replace('\r', '').replace('\t', '').strip()

    publication_date_without_deal = re.search(r'\d.+', publish)
    if publication_date_without_deal is not None:
        publication_date = publication_date_without_deal.group()
    else:
        publication_date = ''
    return publisher_place, publishing_house, publication_date


def get_form(response, num):
    form = "".join(response.xpath('//tr[{}]/td[@class="rightTD"]/text()'.format(num)).get().strip().split())
    return form


def get_summary(response, num):
    summary = response.xpath('//tr[{}]/td[@class="rightTD"]/text()'.format(num)).get().strip()
    return summary


def get_theme(response, num):
    theme_without_deal = response.xpath('//tr[{}]/td[@class="rightTD"]'.format(num))
    theme = theme_without_deal.xpath('string(.)').get().replace('\n', '').replace('\r', '').replace('\t', '').strip()
    return theme


def get_classification_and_edition(response, num):
    classification_edition_without_deal = response.xpath('//tr[{}]/td[@class="rightTD"]'.format(num))
    classification_edition = classification_edition_without_deal.xpath('string(.)').get().replace('\n', '')\
        .replace('\r', '').replace('\t', '').strip()
    classification_or_none = re.search(r"[a-zA-Z0-9.:-]+", classification_edition)
    if classification_or_none is not None:
        classification = classification_or_none.group()
    else:
        classification = ''
    edition_with_word = re.search(r"版次：[\d]+", classification_edition)
    if edition_with_word is not None:
        edition = re.sub('[版次：]', '', edition_with_word.group())
    else:
        edition = ''
    return classification, edition


class LibraryPageSpider(scrapy.Spider):
    name = 'library'
    home_url = 'http://210.35.66.106/opac/browse/cls'
    cookie = ''

    book_sort = [
        ('A', '马列主义、毛泽东思想、邓小平理论'), ('B', '哲学、宗教'), ('C', '社会科学总论'), ('D', '政治、法律'),
        ('E', '军事'), ('F', '经济'), ('G', '文化、科学、教育、体育'), ('H', '语言、文字'),
        ('I', '文学'), ('J', '艺术'), ('K', '历史、地理'), ('N', '自然科学总论'),
        ('O', '数理科学与化学'), ('P', '天文学、地球科学'), ('Q', '生物科学'), ('R', '医药、卫生'),
        ('S', '农业科学'), ('T', '工业技术'), ('U', '交通运输'),
        ('X', '环境科学,安全科学'), ('Z', '综合性图书')
    ]

    @staticmethod
    def _get_sort_page_url(sort_code: str):
        return f'http://210.35.66.106/opac/search?q={sort_code}&searchType=standard&isFacet=false&view=simple&' \
               f'searchWay=class&rows=10&sortWay=score&sortOrder=desc&searchWay0=marc&logical0=AND&page=1'

    def start_requests(self):
        """
        for index, sort_code in self.book_sort:
            url = self._get_sort_page_url(sort_code, index)
            yield scrapy.Request(url=url,
                                 callback=self.parse)
        """
        for sort, _ in self.book_sort:
            # url = 'http://210.35.66.106/opac/book/573381' 59808 246377
            url = self._get_sort_page_url(sort)
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response, **kwargs):
        # There are two types of pages will be transferred to, and parsed in parse function
        # Book list:
        # http://210.35.66.106/opac/search?
        # Book detail:
        # http://210.35.66.106/opac/book/
        # So it's necessary to check it before anything else.

        print(response.url)
        if 'opac/search' in response.url:
            return self.parse_book_list(response, **kwargs)
        if 'opac/book/' in response.url:
            return self.parse_book_detail(response, **kwargs)
        else:
            # Unexpected page, maybe from detail page
            pass

    def parse_book_detail(self, response, **kwargs):
        all_element = response.xpath('//tr').getall()
        num = len(all_element)
        i = 0
        item = BookItem()
        item['title'] = ''
        item['url'] = ''
        item['book_id'] = ''
        item['isbn'] = ''
        item['language'] = ''
        item['author'] = ''
        item['publisher_place'] = ''
        item['publication_date'] = ''
        item['price'] = ''
        item['publishing_house'] = ''
        item['form'] = ''
        item['summary'] = ''
        item['theme'] = ''
        item['classification'] = ''
        item['edition'] = ''
        while i < num:
            item['title'] = get_title(response)
            item['url'] = response.url
            book_id = int(response.url.replace('http://210.35.66.106/opac/book/', ''))
            item['book_id'] = book_id
            if response.xpath('//tr[{}]/td[@class="leftTD"]/div[@align="left"]/text()'.format(i)).get() is not None:
                if response.xpath(
                        '//tr[{}]/td[@class="leftTD"]/div[@align="left"]/text()'.format(i)).get().strip() == 'ISBN:':
                    item['isbn'], item['price'] = get_isbn_and_price(response, i)
                if response.xpath(
                        '//tr[{}]/td[@class="leftTD"]/div[@align="left"]/text()'.format(i)).get().strip() == '语种:':
                    item['language'] = get_language(response, i)
                if response.xpath(
                        '//tr[{}]/td[@class="leftTD"]/div[@align="left"]/text()'.format(i)).get().strip() == '题名/责任者:':
                    item['author'] = get_author(response, i)
                if response.xpath(
                        '//tr[{}]/td[@class="leftTD"]/div[@align="left"]/text()'.format(i)).get().strip() == '出版发行:':
                    item['publisher_place'], item['publishing_house'], item['publication_date'] = get_publish(response,
                                                                                                              i)
                if response.xpath(
                        '//tr[{}]/td[@class="leftTD"]/div[@align="left"]/text()'.format(i)).get().strip() == '载体形态:':
                    item['form'] = get_form(response, i)
                if response.xpath(
                        '//tr[{}]/td[@class="leftTD"]/div[@align="left"]/text()'.format(i)).get().strip() == '摘要:':
                    item['summary'] = get_summary(response, i)
                if response.xpath(
                        '//tr[{}]/td[@class="leftTD"]/div[@align="left"]/text()'.format(i)).get().strip() == '主题:'\
                        or response.xpath(
                        '//tr[{}]/td[@class="leftTD"]/div[@align="left"]/text()'.format(i)).get().strip() == '相关主题:':
                    item['theme'] = get_theme(response, i)
                if response.xpath(
                        '//tr[{}]/td[@class="leftTD"]/div[@align="left"]/text()'.format(i)).get().strip() == '中图分类:' \
                        or response.xpath(
                        '//tr[{}]/td[@class="leftTD"]/div[@align="left"]/text()'.format(i)).get().strip() == '科图分类:':
                    item['classification'], item['edition'] = get_classification_and_edition(response, i)
            i += 1
        yield item

    def parse_book_list(self, response, **kwargs):
        link_list = get_links(response)
        for url in link_list:
            url = response.urljoin(url)

            yield scrapy.Request(url=url,
                                 callback=self.parse,
                                 cb_kwargs=kwargs)
