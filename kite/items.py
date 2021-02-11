# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class FileItem(scrapy.Item):
    """
    FileItem is for each link.
    """

    ''' Basic information '''
    # URL.
    url = scrapy.Field()
    # File name. For example, the url is 'www.baidu.com/index.html',
    # the file name is 'index.html'
    title = scrapy.Field()

    ''' Local file related information '''
    # Checksum
    checksum = scrapy.Field()
    # File path
    path = scrapy.Field()

    ''' Operating related information '''
    is_continuing: bool = True


class AttachmentItem(FileItem):
    pass


class PageItem(FileItem):
    # File content
    content = scrapy.Field()
    # Publish time
    publish_time = scrapy.Field()
    # Link count. Used to analyze whether the page is an article or not.
    link_count = scrapy.Field()
