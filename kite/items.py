# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class StoreItem(scrapy.Item):
    """ Base class for attachment and page item. """

    # URL.
    url = scrapy.Field()
    # File name. For example, the url is 'www.baidu.com/index.html',
    # the file name is 'index.html'
    title = scrapy.Field()


class AttachmentItem(StoreItem):
    """ Attachment item """

    # Referer
    referer = scrapy.Field()
    # Size
    size = scrapy.Field()
    # Checksum
    checksum = scrapy.Field()
    # File path
    path = scrapy.Field()
    # Private flag
    private = scrapy.Field()
    # Cookies field, for the attachments from portal.
    cookies = scrapy.Field()


class PageItem(StoreItem):
    """ Page item """

    # File content
    content = scrapy.Field()
    # Publish date
    publish_date = scrapy.Field()
    # Link count. Used to analyze whether the page is an article or not.
    link_count = scrapy.Field()


class NoticeItem(StoreItem):
    """ Notice item in OA website. """

    # Author, the teacher publisher
    author = scrapy.Field()
    # Notice content
    content = scrapy.Field()
    # Publish time
    publish_time = scrapy.Field()
    # Sort
    sort = scrapy.Field()
    # Publish department
    department = scrapy.Field()


class BookItem(StoreItem):
    """Book item in library."""

    # Book id
    book_id = scrapy.Field()
    # Book isbn
    isbn = scrapy.Field()
    # Book price
    price = scrapy.Field()
    # Book language
    language = scrapy.Field()
    # Author of book
    author = scrapy.Field()
    # Publisher place
    publisher_place = scrapy.Field()
    # Publishing house
    publishing_house = scrapy.Field()
    # Publication date
    publication_date = scrapy.Field()
    # Book form
    form = scrapy.Field()
    # Summary of book
    summary = scrapy.Field()
    # Theme of book
    theme = scrapy.Field()
    # Chinese library book classification
    classification = scrapy.Field()
    # Edition of book
    edition = scrapy.Field()
