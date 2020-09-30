from scrapy.cmdline import execute #导入scrapymd运行模块

import sys,os

#显示出当前文件目录的绝对路径
#print(os.path.dirname(os.path.abspath(__file__)))
#把当前文件目录放到python的搜索路径中去
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

execute(["scrapy","crawl","jobbole"]) #运行\ArticleSpider\ArticleSpider目录下的jobbole.py 文件

