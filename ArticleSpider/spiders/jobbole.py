import scrapy
from urllib import parse
import requests
from scrapy import Request
import re
import json
from ArticleSpider.utils import common
from ArticleSpider.items import JobBoleArticleItem

class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['news.cnblogs.com']
    start_urls = ['http://news.cnblogs.com/']

    def parse(self, response):
        '''
        parse 函数作用：
            一般用于写抓取url的策略，不做具体解析
            1、获取新闻列表一种的新闻url并交给scrapy进行下载后调用相应的解析方法
            2、获取下一页的url交给scrapy进行下载，下载完成后交给parse继续跟进


        #获取a标签下的值，并取第一个，如果列表为空，会抛异常
        #url = response.xpath('//*[@id="entry_674002"]/div[2]/h2/a/@href').extract()[0]
        # 获取a标签下的值，并取第一个，如果列表为空，会返回括号里面的空值，避免异常
        #url = response.xpath('//*[@id="entry_674002"]/div[2]/h2/a/@href').extract_first("")
        #查找所有属性id=news——list的div元素下属性class=news——entry的h2下a标签的href 是一个列表
        #url = response.xpath('//div[@id="news_list"]//h2[@class="news_entry"]/a/@href').extract()
        #同样标签用css选取
        #url = response.css('div#news_list h2 a::attr(href)').extract()
        #print(url)
        #/html/body/div[2]/div[2]/div[4]/div[1]/div[2]/h2/a/@href
        #='//*[@id="entry_674002"]/div[2]/h2/a'
        '''
        #1、获取新闻列表一种的新闻url并交给scrapy进行下载后调用相应的解析方法

        post_nodes = response.css('#news_list .news_block')
        for post_node in post_nodes:
            image_url = post_node.css('.entry_summary a img::attr(src)').extract_first("")
            if image_url.startswith('//'):
                image_url = 'https:'+image_url

            post_url = post_node.css('h2 a::attr(href)').extract_first("")
            #当下载完成后调用parse_detail  callback 用法还是不太清楚
            #parse.urljoin 由于爬取到的url是短链接所有通过urljoin方法自动补全
            #meta传递image_url 参数
            #yield 是异步的 只要把这个url 交出去了就继续执行，不等待结果
            yield Request(url=parse.urljoin(response.url,post_url),meta={"front_image_url":image_url},callback=self.parse_detail)

        #2、获取下一页的url交给scrapy进行下载，下载完成后交给parse继续跟进 css方法
        next_url = response.css("div.pager a:last-child::text").extract_first("")#获取属性为pager的div下的最后一个a标签文本的值
        if next_url == "Next >":#判断文本的值是否等于下一页
            next_url = response.css("div.pager a:last-child::attr(href)").extract_first("")#获取下一页的链接
            yield Request(url=parse.urljoin(response.url, next_url),callback=self.parse)#把获取到的下一页链接交给self.parse函数继续处理

        #2、获取下一页的url交给scrapy进行下载，下载完成后交给parse继续跟进  xpath方法
        #next_url = response.xpath("//a[contains(text(),'Next >')]/@href").extract_first("")#全局查找文本包含Next >的a标签提取href值
        #yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse)  # 把获取到的下一页链接交给self.parse函数继续处理





    def parse_detail(self,response):
        match_re = re.match(".*?(\d+)",response.url)
        if match_re:
            article_item = JobBoleArticleItem()
            title = response.css("#news_title a::text").extract_first("")
            #xpath 匹配
            #title = response.xpath("//*[@id='news_title']//a/text()").extract_first("")
            #create_date = response.css('#news_info .time::text').extract_first("")
            # xpath 匹配
            create_date = response.xpath('//*[@id="news_info"]//*[@class="time"]/text()').extract_first("")
            match_re_data = re.match(".*?(\d+.*)",create_date)
            if match_re_data:
                create_date = match_re_data.group(1)
            #提取新闻的内容部分,html格式
            content = response.css('#news_content').extract()[0]
            tag_list = response.css(".news_tags a::text").extract()
            tags = ",".join(tag_list)#把列表转换成字符串用,号隔开

            post_id = match_re.group(1)

            #赋值到item

            article_item["title"] = title
            article_item["create_date"] = create_date
            article_item["content"] = content
            article_item["tags"] = tags
            article_item["url"] = response.url
            #做一个判断，如果有图片url就传递，没有的话就直接传递一个空列表给scrapy
            if response.meta.get("front_image_url",""):
                #需要下载的图片url一定要传递list类型
                article_item["front_image_url"] = [response.meta.get("front_image_url","")]
            else:
                article_item["front_image_url"] = []

            #方法1、同步处理
            '''
            #请求一些动态加载数据，.format(post_id) 表示把post_id 这个变量放到前面的大括号里面 字符串前面/的话 response.url 为域名，不加路径 不带的话 带路径
            html = requests.get(parse.urljoin(response.url,"/NewsAjax/GetAjaxNewsInfo?contentId={}".format(post_id)))
            j_data = json.loads(html.text)
            praise_nums = j_data["DiggCount"]
            fav_nums = j_data["TotalView"]
            comment_nums = j_data["CommentCount"]
            '''
            #方法2、异步回调，效率高一点
            yield Request(parse.urljoin(response.url,"/NewsAjax/GetAjaxNewsInfo?contentId={}".format(post_id)),
                          meta={"article_item":article_item},callback=self.parse_nums)

    #方法2 的异步处理函数
    def parse_nums(self,response):
        j_data = json.loads(response.text)
        #由parse_detail函数传递下来
        article_item = response.meta.get("article_item","")


        praise_nums = j_data["DiggCount"]
        fav_nums = j_data["TotalView"]
        comment_nums = j_data["CommentCount"]

        article_item["praise_nums"] = praise_nums
        article_item["fav_nums"] = fav_nums
        article_item["comment_nums"] = comment_nums
        article_item["url_object_id"] = common.get_md5(article_item['url'])
        #yield 随时可以发出item,跟Request
        yield article_item




        pass