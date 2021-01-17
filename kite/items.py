# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class FileItem(scrapy.Item):
    # Name of the file to save
    filename = scrapy.Field()
    # URL.
    url = scrapy.Field()
    # File content
    content = scrapy.Field()
    # Meta type, from the 'Content-Type' in response header
    meta_type = scrapy.Field()
    # File name. For example, the url is 'www.baidu.com/index.html',
    # the file name is 'index.html'
    title = scrapy.Field()


class AttachmentItem(FileItem):
    size = scrapy.Field()


class PageItem(FileItem):
    # Publish time
    publish_time = scrapy.Field()
    # Link count. Used to analyze whether the page is an article or not.
    link_count = scrapy.Field()
