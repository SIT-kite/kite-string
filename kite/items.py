# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class StoreItem(scrapy.Item):
    """ Base class for attachment and page item. """

    ''' Operating related information '''
    is_continuing = scrapy.Field()

    ''' Basic information '''
    # URL.
    url = scrapy.Field()
    # File name. For example, the url is 'www.baidu.com/index.html',
    # the file name is 'index.html'
    title = scrapy.Field()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self['is_continuing'] = True


class AttachmentItem(StoreItem):
    """ Attachment item """

    # Size
    size = scrapy.Field()
    # Checksum
    checksum = scrapy.Field()
    # File path
    path = scrapy.Field()


class PageItem(StoreItem):
    """ Page item """

    # File content
    content = scrapy.Field()
    # Publish time
    publish_time = scrapy.Field()
    # Link count. Used to analyze whether the page is an article or not.
    link_count = scrapy.Field()
