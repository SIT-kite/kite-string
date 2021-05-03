import scrapy


def get_links(response):
    return response.xpath('''//div[@class='meneame'][1]/a/@href''').getall()


class LibraryPageSpider(scrapy.Spider):
    name = 'library'
    home_url = 'http://210.35.66.106/opac/browse/cls'
    cookie = ''

    book_sort = [
        ('A', '马列主义、毛泽东思想、邓小平理论'), ('B', '哲学、宗教'), ('C', '社会科学总论'), ('D', '政治、法律'),
        ('E', '军事'), ('F', '经济'), ('G', '文化、科学、教育、体育'), ('H', '语言、文字'),
        ('I', '文学'), ('J', '艺术'), ('K', '历史、地理'), ('N', '自然科学总论'),
        ('O', '数理科学与化学'), ('P', '天文学、地球科学'), ('Q', '生物科学'), ('R', '医药、卫生'),
        ('S', '农业科学'), ('T', '工业技术'), ('U', '交通运输'), ('U', '交通运输'),
        ('X', '环境科学,安全科学'), ('Z', '综合性图书')
    ]

    @staticmethod
    def _get_sort_page_url(sort_code: str, index: str):
        return f'http://210.35.66.106/opac/search?q={index}&searchType=standard&isFacet=false&view=simple&' \
               f'searchWay=class&rows=10&sortWay=score&sortOrder=desc&searchWay0=marc&logical0=AND&page=1'

    def start_requests(self):
        '''
        for index, sort_code in self.book_sort:
            url = self._get_sort_page_url(sort_code, index)
            yield scrapy.Request(url=url,
                                 callback=self.parse)
        '''
        url = 'http://210.35.66.106/opac/search?q=A&searchType=standard&isFacet=false&view=simple&' \
              'searchWay=class&rows=1000&page=1'
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
        if 'opac/book/' in response.url:
            return self.parse_book_detail(response, **kwargs)
        else:
            # Unexpected page, maybe from detail page
            pass

    def parse_book_detail(self, response, **kwargs):
        title = response.xpath('//h2/text()').get()
        url = response.url
        print(title, url, sep='   ')

    def parse_book_list(self, response, **kwargs):
        link_list = get_links(response)
        for url in link_list:
            url = response.urljoin(url)
            print(url)
            yield scrapy.Request(url=url,
                                 callback=self.parse,
                                 cb_kwargs=kwargs)
