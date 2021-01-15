# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class SitprojectItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    # title = scrapy.Field()
    name = scrapy.Field()
    url = scrapy.Field()
    html_text = scrapy.Field()
    zip_name = scrapy.Field()
    html_zip = scrapy.Field()
