# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class SitprojectItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    # title = scrapy.Field()
    html_name = scrapy.Field()
    html_url = scrapy.Field()
    html_body = scrapy.Field()
    html_uuid = scrapy.Field()
    file_name = scrapy.Field()
    file_url = scrapy.Field()
    file_body = scrapy.Field()
    file_form = scrapy.Field()
