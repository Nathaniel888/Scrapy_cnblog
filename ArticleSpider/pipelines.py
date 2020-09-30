# Define your item pipelines here
#导入scrapy的图片处理模块
from scrapy.pipelines.images import ImagesPipeline
#导入文件编码模块
import codecs
import json
#导入数据库连接客户端
import MySQLdb
#导入json内置的json文件导出模块
from scrapy.exporters import JsonItemExporter

# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class ArticlespiderPipeline:
    def process_item(self, item, spider):
        return item


#同步方法写入数据库
class MysqlPipeline(object):
    def __init__(self):
        #连接数据库 数据库地址，账号，密码，数据库名称，指定编码utf8,使用unicode编码
        self.conn = MySQLdb.connect("124.70.130.75",'root','root','article_spider',charset="utf8",use_unicode=True)
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        #先定义一个sql语句 ON DUPLICATE KEY UPDATE comment_nums=VALUES(comment_nums) 表示数据又相同主键的时候更新'comment_nums'数据，用当前'comment_nums'写入数据覆盖，防止sql报错
        insert_sql = """
        insert into jobble_article(title,url,url_object_id,front_image_url,parise_nums,comment_nums,fav_nums,content,create_date,front_image_path,tags)
        values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE comment_nums=VALUES(comment_nums)
        """
        #先创建一个空列表
        params = list()
        #把需要添加的item值添加到列表中,入股哦title没有值则会报错用get获取可以避免错误
        #params.append(item['title'])
        params.append(item.get('title',""))
        params.append(item.get('url', ""))
        params.append(item.get('url_object_id', ""))
        #通过.join方法把front_image_url转换成一个字符串，mysql不能插入列表
        front_image = ",".join(item.get('front_image_url', []))
        params.append(front_image)
        #点赞数类型是int数字类型，可以直接写默认值为0
        params.append(item.get('parise_nums', 0))
        params.append(item.get('comment_nums', 0))
        params.append(item.get('fav_nums', 0))
        params.append(item.get('content', ""))
        #时间默认不能为空，mysql识别不出会报错 设置默认时间为1970-07-01 字符串形式传递
        params.append(item.get('create_date', "1970-07-01"))
        params.append(item.get('front_image_path', ""))
        params.append(item.get('tags', ""))
        #str_tags = ",".join(item.get('tags', []))
        #params.append(str_tags)

        #封装数据库语句,把params转换成tuple元组，就是一种不能修改的list
        #self.cursor.execute(insert_sql,tuple(params))
        self.cursor.execute(insert_sql,params)

        #执行插入数据库语句
        self.conn.commit()

        return item


#异步方法写入数据,导入twisted的adbapi模块 异步写入
from twisted.enterprise import adbapi
class MysqlTwistedPipeline(object):
    def __init__(self,dbpool):
        self.dbpool = dbpool

    #定义类方法,会在类之前执行的代码，跟初始化差不多
    @classmethod
    def from_settings(cls,settings):
        #从MySQLdb导入DictCursor模块
        from MySQLdb.cursors import DictCursor
        #从settings.py文件读取数据库配置
        dbparms = dict(
            host = settings["MYSQL_HOST"],
            db = settings["MYSQL_DBNAME"],
            user = settings["MYSQL_USER"],
            passwd = settings["MYSQL_PASSWORD"],
            charset='utf8',
            cursorclass=DictCursor,
            use_unicode=True,
        )
        #使用adbapi创建一个数据库连接池
        dbpool = adbapi.ConnectionPool("MySQLdb", **dbparms)
        return cls(dbpool)

    #调用do_insert并检查有无错误，有错误的话通过handle_error打印处理
    def process_item(self, item, spider):
        #使用twisted将mysql插入变成异步执行
        query = self.dbpool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error, item, spider) #处理异常
        return item
    #do_insert执行出错的时候调用的failure参数是自动传入的
    def handle_error(self, failure, item, spider):
        #处理异步插入的异常
        print (failure)


    #解析并写入数据库的具体逻辑代码
    def do_insert(self,cursor,item):
        # 先定义一个sql语句 ON DUPLICATE KEY UPDATE comment_nums=VALUES(comment_nums) 表示数据又相同主键的时候更新'comment_nums'数据，用当前'comment_nums'写入数据覆盖，防止sql报错
        insert_sql = """
                insert into jobble_article(title,url,url_object_id,front_image_url,parise_nums,comment_nums,fav_nums,content,create_date,front_image_path,tags)
                values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE comment_nums=VALUES(comment_nums)
                """
        # 先创建一个空列表
        params = list()
        # 把需要添加的item值添加到列表中,入股哦title没有值则会报错用get获取可以避免错误
        # params.append(item['title'])
        params.append(item.get('title', ""))
        params.append(item.get('url', ""))
        params.append(item.get('url_object_id', ""))
        # 通过.join方法把front_image_url转换成一个字符串，mysql不能插入列表
        front_image = ",".join(item.get('front_image_url', []))
        params.append(front_image)
        # 点赞数类型是int数字类型，可以直接写默认值为0
        params.append(item.get('parise_nums', 0))
        params.append(item.get('comment_nums', 0))
        params.append(item.get('fav_nums', 0))
        params.append(item.get('content', ""))
        # 时间默认不能为空，mysql识别不出会报错 设置默认时间为1970-07-01 字符串形式传递
        params.append(item.get('create_date', "1970-07-01"))
        params.append(item.get('front_image_path', ""))
        params.append(item.get('tags', ""))
        # str_tags = ",".join(item.get('tags', []))
        # params.append(str_tags)
        #写入数据到数据库中
        cursor.execute(insert_sql,tuple(params))
        return item

#将item转储为json文件
class JsonWithEncodingPipline(object):
    #自定义json文件的导出 导入文件编码模块 import codecs
    def __init__(self):
        #创建并打开article.json文件，w 覆盖模式 a 追加模式
        self.file = codecs.open('article.json','a',encoding='utf-8')
    #格式化item并写入
    def process_item(self, item, spider):
        #把item转换成json 字典格式 json.dumps 序列化时对中文默认使用的ascii编码.想输出真正的中文需要指定ensure_ascii=False：
        lines = json.dumps(dict(item),ensure_ascii=False)+"\n"
        #把lines写入article.json
        self.file.write(lines)
        return item
    #关闭文件
    def spider_closed(self,spider):
        self.file.close()


#使用scrapy内置的json导出模块,导出的是json列表
class JsonExporterpipeline(object):
    def __init__(self):
        # 创建并打开article.json文件，w 覆盖模式 a 追加模式
        self.file = codecs.open('articleexport.json', 'wb')
        #实例化JsonItemExporter类
        self.exporter = JsonItemExporter(self.file,encoding='utf-8',ensure_ascii=False)
        #启动JsonItemExporter导出模块
        self.exporter.start_exporting()
    #写入文件
    def process_item(self, item, spider):
        #把item写入文件
        self.exporter.export_item(item)
        return item
    #关闭文件
    def spider_closed(self,spider):
        #关闭文件写入模块
        self.exporter.finish_exporting()
        self.file.close()

#继承scrapy的图片处理模块,在settings中加入这个配置,把图片处理模块定义到ArticleImagePipeline函数
    #ITEM_PIPELINES = {
    #    'ArticleSpider.pipelines.ArticleImagePipeline': 1
    #}
class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        if "front_image_url" in item:
            #先设置一个空值，防止获取不到后续调用报错
            image_file_path = ""
            #先加一个异常
            try:
                for ok, value in results:
                    image_file_path = value['path']
            except:
                image_file_path = "None"
            item["front_image_path"] = image_file_path
        return item
