import scrapy


from . import create_connection_pool
from ..items import BookItem


class BookPipeline:
    def __init__(self):
        self.pg_pool = create_connection_pool()

    def submit_item(self, cursor, item: BookItem):
        insert_sql = \
            '''--(_title text, _book_id integer, _isbn text, _price text, _languages text, 
            --_author text, --_publisher_place text, _publishing_house text, _publication_date text, _form text, 
            --_summary text, --_theme text, _classification text, _edition text) 
            
            CALL library.submit_book(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            '''

        cursor.execute(insert_sql,
                       (item['title'], item['book_id'], item['isbn'], item['price'], item['language'],
                        item['author'], item['publisher_place'], item['publishing_house'], item['publication_date'],
                        item['form'], item['summary'], item['theme'], item['classification'], item['edition']))

    def process_item(self, item: BookItem, spider: scrapy.Spider):
        if item and isinstance(item, BookItem):
            ''' Extract main content from html. '''

            self.pg_pool.runInteraction(self.submit_item, item)
        else:
            return item
