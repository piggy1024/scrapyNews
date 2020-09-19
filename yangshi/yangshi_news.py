# -*- coding:utf8 -*-
import datetime
import json
import random
import re
import requests
from lxml import etree
# 正文内容存在两种结构  一种带视频 一种不带视频
class Scrap_News(object):
    def __init__(self):
        self.origin_url = []
        # 保存标题  央视新闻网-新闻
        self.titles = []
        # 保存时间
        self.dates = []
        # 保存内容
        self.contents = []
        # 保存来源
        self.sources = []
        # 保存含标签的内容
        self.contentWithLabel = []
        # 保存页码
        self.page = 0

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
        html = etree.HTML(response.content)
        return html

    # 发送请求(直接获取json数据)
    def send_request1(self, url):
        response = requests.get(url, headers=self.headers)
        data = response.content.decode()
        return data

    # 获取页码
    def get_page(self):
        index = 1
        while index > 0:
            response = requests.get(
                "https://news.cctv.com/2019/07/gaiban/cmsdatainterface/page/news_" + str(
                    index) + ".jsonp?cb=t&cb=news",
                headers=self.headers)
            if response.status_code == 404:
                break
            else:
                index = index + 1
        self.page = index

    # 获取央视新闻网的url
    def get_yangshi_urls(self):

        # 包含可以提取新闻url 的 数据源
        url_lists = []

        for index in range(1, self.page):
            url_lists.append(
                "https://news.cctv.com/2019/07/gaiban/cmsdatainterface/page/news_" + str(
                    index) + ".jsonp?cb=t&cb=news")

        # 新闻
        for x in url_lists:
            data = self.send_request1(x)
            pattern = re.compile(r'url":"(.*?).shtml')
            jsonData = pattern.findall(data)
            for url in jsonData:
                self.origin_url.append(url + ".shtml")

        content_url_list = self.origin_url
        # --------增量爬取操作-------------
        # 保存此次数据源中能够得到的url(可能包括之前爬过)
        need_to_scrapy_url = content_url_list
        # 清空content_url_list 保存未爬取过的url
        content_url_list = []
        # 放之前爬过的url
        result = []  # 从文件中读取得到
        file_read = open('yangshi_news_url.txt', 'r')
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
        with open('yangshi_news_url.txt', "a", encoding='utf-8') as file:
            file.write(list_str + '\n')
        file.close()

        # 拿到未爬取过的url复制给全局变量
        self.origin_url = content_url_list


    # 获取央视新闻网-新闻的具体文章内容函数
    def get_yangshi_news_news_data(self):
        url_news = self.origin_url
        for url in url_news:
            try:
                html = self.send_request(url)
                titles = html.xpath("//div[@class='title_area']//h1/text()")
                content = html.xpath("//div[@class='content_area']//p/text()")
                content_imgs = html.xpath("//div[@class='content_area']//p/img/@src")
                date = html.xpath("//div[@class='info1']/text()")
                origin_source = html.xpath("//div[@class='info1']/text()")
                self.titles.append(titles[0])
                # 文本内容后面接所有图片的src
                self.contents.append("".join(content) + " ".join(content_imgs))
                real_date = re.sub(r'年|月', '-', date[0].split('|')[1])
                real_date = re.sub(r'日', '', real_date)
                real_date = real_date + ":00"
                self.dates.append(real_date)
                self.sources.append(origin_source[0].split('|')[0])
                contentWithLabel = html.xpath("//div[@class='content_area']")[0]
                contentWithLabel = etree.tostring(contentWithLabel, encoding='utf-8').decode('utf-8')
                contentWithLabel = re.sub(r'class=".*?"', '', contentWithLabel)
                contentWithLabel = re.sub(r'id=".*?"', '', contentWithLabel)
                # 带标签的内容
                contentWithLabel = re.sub(r'&#13;', '', contentWithLabel)
                self.contentWithLabel.append(contentWithLabel)
            except Exception as e:
                # print(e)
                print(url)
                pass
        # 保存拼接的每个完整的数据{...},{...}
        data_json_all = ''
        print(len(self.titles))
        for index in range(len(self.titles)):
            data_json = {
                "index": "gdzx_social_data",
                "source": {
                    "classsify": "",
                    "collectTime": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "content": self.contents[index],
                    "contentWithLable": self.contentWithLabel[index],
                    "dataDepart": "央视新闻网",
                    "originSource": self.sources[index],
                    "publishTime": self.dates[index],
                    "theme": "新闻",
                    "title": self.titles[index]
                },
                "type": "央视新闻网/新闻"
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
        # res = requests.post("http://inc.sworddata.cn:8883/es/api/addArticle", headers=headers, data=str)

        # print(res.status_code)
        # print(res.text)

    # 统一调度
    def start(self):

        # 央视新闻网-新闻-调用
        self.get_page()
        self.get_yangshi_urls() # 获取url
        self.get_yangshi_news_news_data()


Scrap_News().start()