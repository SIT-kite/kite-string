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
        path = 'E://File//sit_html//' + item['name']
        mymakedir(path)
        with open(path + '//' + item['name'] + '.html', 'wb') as html_text:
            html_text.write(item['html_text'])
        if 'html_zip' in item:
            with open(path + '//' + item['zip_name'] + '.rar', 'wb')as html_zip:
                html_zip.write(item['html_zip'])
        print('OK')
