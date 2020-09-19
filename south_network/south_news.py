# -*- coding:utf8 -*-
import datetime
import json
import random
import re
import requests
from lxml import etree

class Scrap_News(object):
    def __init__(self):
        self.origin_url = []
        # 保存标题  南方新闻网-经济
        self.titles = []
        # 保存时间
        self.dates = []
        # 保存内容
        self.contents = []
        # 保存来源
        self.sources = []
        # 保存含标签的内容
        self.contentWithLabel = []
        self.page = 0
        # 编码
        self.code = ""
        # 请求头的添加
        ua_list = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36 QIHU 360SE',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0']
        ua = random.choice(ua_list)
        self.headers = {'User-Agent': ua}

    # 发送请求  (获取dom结构)
    def send_request(self, url):
        response = requests.get(url, headers=self.headers)
        self.code = response.encoding
        html = etree.HTML(response.content)
        return html

    # 获取页码
    def get_page(self):
        index = 2
        while index > 0:
            response = requests.get(
                "http://news.southcn.com/community/default_" + str(
                    index) + ".htm",
                headers=self.headers)
            if response.status_code == 404:
                break
            else:
                index = index + 1
        self.page = index

    #  获取南方网里的url里获取具体的文章的url
    def get_southnetwork_url(self):

        # 保存所有可分析dom获取url的网址
        url_lists = ["http://news.southcn.com/community/default.htm"]

        for i in range(2, self.page):
            url_lists.append("http://news.southcn.com/community/default_" + str(i) + ".htm")
        self.origin_url = url_lists

    # 获取南方网文章的具体url  加上内容
    def get_south_data(self):
        content_url_list = []
        for url in self.origin_url:
            html = self.send_request(url)
            contents_urls_lists = html.xpath("//div[@class='pw']//h3//a/@href")
            content_url_list = content_url_list + contents_urls_lists

        # --------增量爬取操作-------------
        # 保存此次数据源中能够得到的url(可能包括之前爬过)
        need_to_scrapy_url = content_url_list
        # 清空content_url_list 保存未爬取过的url
        content_url_list = []
        # 放之前爬过的url
        result = []  # 从文件中读取得到
        file_read = open('south_news_url.txt', 'r')
        for line in file_read.readlines():
            result.append(line.strip('\n'))
        file_read.close()
        # print(result)
        # 过滤掉之前爬过的url
        for new_url in need_to_scrapy_url:
            if new_url not in result:
                content_url_list.append(new_url)

        # 将新的url追加保存进文本文件
        list_str = "\n".join(content_url_list)
        with open('south_news_url.txt', "a", encoding='utf-8') as file:
            file.write(list_str + '\n')
        file.close()

        # 爬取文章内容
        for url_of_content in content_url_list:
            try:
                content_url = url_of_content
                content_html = self.send_request(content_url)
                title = content_html.xpath("//div[@class='m-article']//h2/text()")
                content = content_html.xpath("//div[@class='content']//p/text()")
                date = content_html.xpath("//div[@class='fl']//span[@class='pub_time']/text()")
                origin_source = content_html.xpath("//div[@class='fl']//span[@id='source_baidu']/text()")
                contentWithLabel = content_html.xpath("//div[@class='content']")[0]
                contentWithLabel = etree.tostring(contentWithLabel, encoding='utf-8').decode('utf-8')
                contentWithLabel = re.sub(r'class=".*?"', '', contentWithLabel)
                contentWithLabel = re.sub(r'id=".*?"', '', contentWithLabel)
                # 带标签的内容
                contentWithLabel = re.sub(r'&#13;', '', contentWithLabel)

                # 无报错 存储每一条新闻信息
                # print(title)
                title[0] = re.sub(r'\r\n', "", title[0])
                self.titles.append(title[0])
                self.contents.append("".join(content))
                self.dates.append(date[0].split(" ")[0])
                self.sources.append(origin_source[0].split('：')[1])
                self.contentWithLabel.append(contentWithLabel)
            except Exception as e:
                # print(e)
                pass
        # 保存拼接的每个完整的数据{...},{...}
        data_json_all = ''
        for index in range(len(self.titles)):
            data_json = {
                "index": "gdzx_social_data",
                "source": {
                    "classsify": "",
                    "collectTime": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "content": self.contents[index],
                    "contentWithLable": self.contentWithLabel[index],
                    "dataDepart": "南方网",
                    "originSource": self.sources[index],
                    "publishTime": self.dates[index]+" 00:00:00",
                    "theme": "社会",
                    "title": self.titles[index]
                },
                "type": "南方网/社会"
            }
            # dict -> json(字符串类型)
            data_json = json.dumps(data_json).encode().decode('utf-8')
            # 每个完整的数据用,拼接起来
            data_json_all = data_json + ',' + data_json_all

        # 拼接并向接口发送数据
        data_json_all = data_json_all[:-1]
        str = "[" + data_json_all + "]"
        # 设置上传信息的请求头
        headers = {'content-type': "application/json", 'apikey': 'c4ce1c0958261e1dea72afc0665f9c68'}
        # 向接口发送数据
        res = requests.post("http://inc.sworddata.cn:8883/es/api/addArticle", headers=headers, data=str)

        print(res.status_code)
        print(res.text)

    # 统一调度  已解决差编码问题但放进utool中可解决
    def start(self):

        # 南方新闻网-社会-调用
        self.get_page()
        self.get_southnetwork_url() # 获取url
        self.get_south_data()


Scrap_News().start()