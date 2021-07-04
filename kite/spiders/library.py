import re
import scrapy

from ..items import BookItem


def init_item(item):
    item['title'] = ''
    item['url'] = ''
    item['book_id'] = ''
    item['isbn'] = ''
    item['price'] = ''
    item['language'] = ''
    item['author'] = ''
    item['publisher_place'] = ''
    item['publication_date'] = ''
    item['publishing_house'] = ''
    item['form'] = ''
    item['summary'] = ''
    item['theme'] = ''
    item['classification'] = ''
    item['edition'] = ''


def add_item(item, _kv: dict, d_i: dict):
    for key, value in d_i.items():
        if key in _kv:
            item[value] = _kv[key]


def get_links(response):
    book_links = response.xpath('//span[@class="bookmetaTitle"]/a/@href').getall()
    list_links = response.xpath('//div[@class="meneame"][1]/a/@href').getall()
    return book_links + list_links


def get_title(_kv: dict, response):
    title = response.xpath('//h2/text()').get()
    if title is None:
        title = response.xpath('//tr/td[@class="rightTD"]/a[@href]/text()').get().strip()
    _kv['标题'] = title


def get_isbn_and_price(_kv: dict, response):
    isbn_and_price = response.xpath('string(.)').get().replace('\n', '').replace('\r', '') \
        .replace('\t', '').strip()
    isbn_or_none = re.search(r"(\d-?){13}|(\d-?){10}|(\d-?){8}", isbn_and_price)
    if isbn_or_none is not None:
        isbn = isbn_or_none.group()
    else:
        isbn = ''
    price_with_word = re.search(r"价格：[\sa-zA-Z0-9.]+", isbn_and_price)
    if price_with_word is not None:
        price = re.sub('[价格：]', '', price_with_word.group())
    else:
        price = ''
    _kv['ISBN'] = isbn
    _kv['价格'] = price


def get_language(_kv: dict, response):
    language = response.xpath('string(.)').get().replace('\n', '').replace('\r', '').replace('\t', '').strip()
    _kv['语种'] = language


def get_author(_kv: dict, response):
    author_and_book = response.xpath('string(.)').get().replace('\n', '').replace('\r', '').replace('\t', '').strip()
    author_with_symbol = re.search(r"/[a-zA-Z\u4e00-\u9fa5().,·\s]+", author_and_book)
    if author_with_symbol is not None:
        author = re.sub('[/]', '', author_with_symbol.group())
    else:
        author = ''
    _kv['作者'] = author


def get_publish(_kv: dict, response):
    publish = response.xpath('string(.)').get().replace('\n', '').replace('\r', '').replace('\t', '').strip()
    publisher_place_without_deal = re.search('出版地：[\u4e00-\u9fa5]+', publish)
    if publisher_place_without_deal is not None:
        if publisher_place_without_deal.group() == '出版地：出版社':
            publisher_place = ''
        else:
            publisher_place = re.sub('[出版地：]', '', publisher_place_without_deal.group())
    else:
        publisher_place = ''

    publishing_house_without_deal = response.xpath('a/text()').get()
    publishing_house = publishing_house_without_deal.replace('\n', '').replace('\r', '').replace('\t', '').strip()

    publication_date_without_deal = re.search(r'\d.+', publish)
    if publication_date_without_deal is not None:
        publication_date = publication_date_without_deal.group()
    else:
        publication_date = ''
    _kv['出版地'] = publisher_place
    _kv['出版社'] = publishing_house
    _kv['出版日期'] = publication_date


def get_form(_kv: dict, response):
    form = "".join(response.xpath('string(.)').get().strip().split())
    _kv['载体形态'] = form


def get_summary(_kv: dict, response):
    summary = response.xpath('string(.)').get().strip()
    _kv['摘要'] = summary


def get_theme(_kv: dict, response):
    theme = response.xpath('string(.)').get().replace('\n', '').replace('\r', '').replace('\t', '').strip()
    if '主题' not in _kv:
        _kv['主题'] = theme


def get_classification_and_edition(_kv: dict, response):
    classification_edition = response.xpath('string(.)').get().replace('\n', '').replace('\r', '').replace('\t',
                                                                                                           '').strip()
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
    _kv['分类'] = classification
    _kv['版次'] = edition


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
            # Test single book's url
            # url = 'http://210.35.66.106/opac/book/618270'
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
        # Store the key and value in dictionary
        all_element = response.xpath('//tr')
        match_element = []
        kv = dict()
        for each_element in all_element:
            left_or_None = each_element.xpath('td[@class="leftTD"]/div[@align="left"]/text()').get()
            right = each_element.xpath('td[@class="rightTD"]')
            if left_or_None is not None:
                left = left_or_None.strip()
                match_element.append((left, right))

        # The function to analysis the web
        functions = {
            'ISBN:': get_isbn_and_price,
            'ISSN:': get_isbn_and_price,
            '语种:': get_language,
            '题名/责任者:': get_author,
            '著者:': get_author,
            '出版发行:': get_publish,
            '载体形态:': get_form,
            '摘要:': get_summary,
            '主题:': get_theme,
            '相关主题:': get_theme,
            '中图分类:': get_classification_and_edition,
            '科图分类:': get_classification_and_edition
        }

        # The dictionary's key to item's label
        dict_item = {
            '标题': 'title',
            'url': 'url',
            '书号': 'book_id',
            'ISBN': 'isbn',
            '价格': 'price',
            '语种': 'language',
            '作者': 'author',
            '出版地': 'publisher_place',
            '出版日期': 'publication_date',
            '出版社': 'publishing_house',
            '载体形态': 'form',
            '摘要': 'summary',
            '主题': 'theme',
            '分类': 'classification',
            '版次': 'edition'
        }

        # Analysis the web
        get_title(kv, response)
        kv['url'] = response.url
        book_id = int(response.url.replace('http://210.35.66.106/opac/book/', ''))
        kv['书号'] = book_id

        for k, v in match_element:
            key = k
            value = v
            if key in functions:
                function = functions[k]
                function(kv, value)

        # Write the item by dictionary's value
        item = BookItem()
        init_item(item)
        add_item(item, kv, dict_item)
        yield item

    def parse_book_list(self, response, **kwargs):
        link_list = get_links(response)
        for url in link_list:
            url = response.urljoin(url)

            yield scrapy.Request(url=url,
                                 callback=self.parse,
                                 cb_kwargs=kwargs)
