# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.pipelines.files import FilesPipeline 
import os
import hashlib
import datetime
import re
import mysql.connector

class LawpdfScrapingPipeline():
    def process_item(self, item, spider):
        pass
        adapter = ItemAdapter(item)
        
        original_date = adapter.get('release_date')
        if 'release_date' in item and isinstance(item['release_date'], str):
            split_date = original_date.split(" ")
            thai_months = {
                'ม.ค.': '01',
                'ก.พ.': '02',
                'มี.ค.': '03',
                'เม.ย.': '04',
                'พ.ค.': '05',
                'มิ.ย.': '06',
                'ก.ค.': '07',
                'ส.ค.': '08',
                'ก.ย.': '09',
                'ต.ค.': '10',
                'พ.ย.': '11',
                'ธ.ค.': '12'
            }

            if len(split_date) == 3 :
                month = thai_months.get(split_date[1])
                day = split_date[0]
                year = split_date[2]
            else:
                month = thai_months.get(split_date[2])
                day = split_date[1]
                year = split_date[3]

            date = f"{year}{month}{day}"
            print('##################')
            print(date)
            date = datetime.datetime.strptime(date, "%Y%m%d").date()
            item['release_date'] = date

        return item

class DownloadFilesPipeline(FilesPipeline):
    def file_path(self, request, response=None, info=None):
        file_name: str = request.url.split("/")[-1].split("&")[0]
        return file_name
    
class SaveToMySQL():
    def __init__(self):
        self.conn = mysql.connector.connect(
            host = 'localhost',
            user = 'root',
            database = 'scrape_db',
            password = ''
        )

        self.cur = self.conn.cursor()
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS lawpdf(
            id int NOT NULL auto_increment, 
            name text,
            file_urls text,
            law_type VARCHAR(10),
            release_date DATE,
            PRIMARY KEY (id)
        )
        """)

    def process_item(self, item, spider):
        self.cur.execute("SELECT * FROM lawpdf WHERE file_urls = %s", (item['file_urls'][0],))
        result = self.cur.fetchone()

        if result:
            spider.logger.warn("file urls already in database: %s" % item['file_urls'])
        else:
            self.cur.execute("""
                        INSERT INTO lawpdf (name , file_urls , law_type , release_date) 
                        VALUES (%s,%s,%s,%s)
            """,(item['name'],item['file_urls'][0],item['law_type'],item['release_date']))
            self.conn.commit()
        return item
    
    def close_spider(self,spider):
        self.cur.close()
        self.conn.close()