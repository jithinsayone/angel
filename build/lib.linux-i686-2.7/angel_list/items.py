# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class AngelListItem(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field()
    description=scrapy.Field()
    stage = scrapy.Field()
    location=scrapy.Field()
    market = scrapy.Field()
    founder=scrapy.Field()
    employe_num = scrapy.Field()


