# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

import os


def mymakedir(path):
    if not os.path.exists(path):
        os.makedirs(path)


class SitprojectPipeline:
    def process_item(self, item, spider):
        #   save .html
        if 'html_url' in item and item['html_url']:
            if not os.path.isfile(r'E:\File\sit_html\{}.html'.format(item['html_uuid'])):
                with open(r'E:\File\sit_html\{}.html'.format(item['html_uuid']), 'wb') as html_body:
                    html_body.write(item['html_body'])
        #    save .rar .xsl .doc
        if 'file_url' in item and item['file_url']:
            if not os.path.isfile(r'E:\File\sit_html\{}.{}'.format(item['file_name'], item['file_form'])):
                with open(r'E:\File\sit_html\{}.{}'.format(item['file_name'], item['file_form']), 'wb') as file_body:
                    file_body.write(item['file_body'])
