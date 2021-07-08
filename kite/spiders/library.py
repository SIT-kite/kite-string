import re

import scrapy

from ..items import BookItem

WHITE_SPACE_PATTERN = re.compile(r'\s')


def remove_space(s: str) -> str:
    return WHITE_SPACE_PATTERN.sub(s, ' ')


def get_links(response):
    book_links = response.xpath('//span[@class="bookmetaTitle"]/a/@href').getall()
    list_links = response.xpath('//div[@class="meneame"][1]/a/@href').getall()
    return book_links + list_links


def get_title(_kv: dict, response):
    title = response.xpath('//h2/text()').get()
    if title is None:
        title = remove_space(response.xpath('//tr/td[@class="rightTD"]/a[@href]/text()').get())

    _kv['标题'] = title


def get_isbn_and_price(_kv: dict, response):
    isbn_and_price = remove_space(response.xpath('string(.)').get())
    isbn_or_none = re.search(r"(\d-?){13}|(\d-?){10}|(\d-?){8}", isbn_and_price)
    isbn = ''
    if isbn_or_none:
        isbn = isbn_or_none.group()
    price_with_word = re.search(r"价格：[\sa-zA-Z0-9.]+", isbn_and_price)
    price = ''
    if price_with_word:
        price = re.sub('[价格：]', '', price_with_word.group())
    if 'ISBN' not in _kv:
        _kv['ISBN'] = isbn
    if '价格' not in _kv:
        _kv['价格'] = price


def get_language(_kv: dict, response):
    language = remove_space(response.xpath('string(.)').get())
    _kv['语种'] = language


def get_author(_kv: dict, response):
    author_and_book = remove_space(response.xpath('string(.)').get())
    author_with_symbol = re.search(r"/[a-zA-Z\u4e00-\u9fa5().,·\s]+", author_and_book)
    author = ''
    if author_with_symbol:
        author = re.sub('[/]', '', author_with_symbol.group())

    _kv['作者'] = author


def get_publish(_kv: dict, response):
    publish = remove_space(response.xpath('string(.)').get())
    publisher_place_without_deal = re.search('出版地：[\u4e00-\u9fa5]+', publish)
    publisher_place = ''
    if publisher_place_without_deal:
        if publisher_place_without_deal.group() == '出版地：出版社':
            publisher_place = ''
        else:
            publisher_place = re.sub('[出版地：]', '', publisher_place_without_deal.group())

    publishing_house = remove_space(response.xpath('a/text()').get())

    publication_date_without_deal = re.search(r'\d.+', publish)
    publication_date = ''
    if publication_date_without_deal:
        publication_date = publication_date_without_deal.group()

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
    theme = remove_space(response.xpath('string(.)').get())
    if '主题' not in _kv:
        _kv['主题'] = theme


def get_classification_and_edition(_kv: dict, response):
    classification_edition = remove_space(response.xpath('string(.)').get())
    classification_or_none = re.search(r"[a-zA-Z0-9.:-]+", classification_edition)
    classification = ''
    if classification_or_none:
        classification = classification_or_none.group()
    edition_with_word = re.search(r"版次：[\d]+", classification_edition)
    edition = ''
    if edition_with_word:
        edition = re.sub('[版次：]', '', edition_with_word.group())

    _kv['分类'] = classification
    _kv['版次'] = edition


class LibraryPageSpider(scrapy.Spider):
    name = 'library'
    site = 'http://210.35.66.106'

    book_sort = [
        ('A', '马列主义、毛泽东思想、邓小平理论'),
        ('B', '哲学、宗教'),
        ('C', '社会科学总论'),
        ('D', '政治、法律'),
        ('E', '军事'),
        ('F', '经济'),
        ('G', '文化、科学、教育、体育'),
        ('H', '语言、文字'),
        ('I', '文学'),
        ('J', '艺术'),
        ('K', '历史、地理'),
        ('N', '自然科学总论'),
        ('O', '数理科学与化学'),
        ('P', '天文学、地球科学'),
        ('Q', '生物科学'),
        ('R', '医药、卫生'),
        ('S', '农业科学'),
        ('T', '工业技术'),
        ('U', '交通运输'),
        ('X', '环境科学,安全科学'),
        ('Z', '综合性图书')
    ]

    # The mapping of parser functions indexed by item key.
    functions = {
        'ISBN:': get_isbn_and_price,
        'ISSN:': get_isbn_and_price,
        '语种:': get_language,
        '题名/责任者:': get_author,
        '出版发行:': get_publish,
        '载体形态:': get_form,
        '摘要:': get_summary,
        '主题:': get_theme,
        '相关主题:': get_theme,
        '中图分类:': get_classification_and_edition,
        '科图分类:': get_classification_and_edition
    }

    # The mapping item in page in Chinese to storage key in English.
    dict_item = {
        '标题': 'title',
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

    def _make_sort_page_url(self, sort_code: str) -> str:
        return self.site + f'/opac/search?q={sort_code}&searchType=standard&view=simple&searchWay=class&rows=1000'

    def start_requests(self):
        """
        Make start urls for all sorts and append them to request queue.
        :return: None
        """
        for sort, _ in self.book_sort:
            url = self._make_sort_page_url(sort)
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response, **kwargs):
        # There are two types of pages will be transferred to, and parsed in parse function
        # Book list:
        # http://210.35.66.106/opac/search?
        # Book detail:
        # http://210.35.66.106/opac/book/
        # So it's necessary to check it before anything else.

        if 'opac/search' in response.url:
            return self.parse_book_list(response, **kwargs)
        elif 'opac/book/' in response.url:
            return self.parse_book_detail(response, **kwargs)
        else:
            # Unexpected page, maybe from detail page
            pass

    def parse_book_detail(self, response, **kwargs):
        # Parse detail items we want and put them into BookItem
        detail_nodes = []
        parsed_items = dict()

        """
        Because the bad design of book detail page, the developer return 10 identical HTML body and set 9 of them
        'display: none' to adapt different client. We only need to parse the first one.
        """
        # Get info table.
        table = response.xpath('//table[@id="bookInfoTable"]')[0]
        # Select items that has leftTD and rightTD at the same time.
        item_selector = '//tr[td/@class = "leftTD"][td/@class = "rightTD"]'
        for item_node in table.xpath(item_selector):
            # Get key and value
            left = item_node.xpath('string(td[@class="leftTD"])').get().strip()
            right = item_node.xpath('td[@class="rightTD"]')
            detail_nodes.append((left, right))

        # Analyse the page
        get_title(parsed_items, response)
        # Emm.. not canonical but it works.
        book_id = int(response.url.replace('http://210.35.66.106/opac/book/', ''))
        parsed_items['书号'] = book_id

        # Extract k and v from node, and standardize the fields.
        for k, v in detail_nodes:
            if k in self.functions:
                # Get and call the corresponding parser function
                parse_item_func = self.functions[k]
                parse_item_func(parsed_items, v)

        # Put detail items into a BookItem object.
        book_item = BookItem()
        for parsed_item_key in parsed_items.keys():
            storage_key = self.dict_item[parsed_item_key]
            book_item[storage_key] = parsed_items[parsed_item_key]

        yield book_item

    def parse_book_list(self, response, **kwargs):
        link_list = get_links(response)
        for url in link_list:
            url = response.urljoin(url)

            yield scrapy.Request(url=url, callback=self.parse)
