# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

import os
import sqlite3
import uuid


def mymakedir(path):
    if not os.path.exists(path):
        os.makedirs(path)


class SitprojectPipeline:
    def process_item(self, item, spider):
        if 'url' in item and item['url']:
            if item['Type'] == 'html':
                file_name = uuid.uuid5(uuid.NAMESPACE_URL, item['url'])
            else:
                file_name = item['name']
            if not os.path.isfile(r'E:\File\sit_file\{}.{}'.format(file_name, item['Type'])):
                with open(r'E:\File\sit_file\{}.{}'.format(file_name, item['Type']), 'wb')as file_body:
                    file_body.write(item['body'])

            file_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, item['url']))
            with open(r'E:\File\sit_file\data_sheet.txt', 'a+', encoding='utf-8')as data:
                data.writelines('url:{}  uuid:{}  name:{}\n'.format(item['url'], file_uuid, item['name']))
