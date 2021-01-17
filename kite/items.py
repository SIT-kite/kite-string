# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class FileItem(scrapy.Item):
    # File name. For example, the url is 'www.baidu.com/index.html',
    # the file name is 'index.html'
    title = scrapy.Field()
    # Saved name
    filename = scrapy.Field()
    # URL.
    url = scrapy.Field()
    # File content
    content = scrapy.Field()
    # Meta tyoe, from the 'Content-Type' in response header
    meta_type = scrapy.Field()

