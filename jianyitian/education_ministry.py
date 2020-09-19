# -*- coding:utf8 -*-
import datetime
import json
import math
import random
import re
import requests
from lxml import etree

class Scrap_News(object):
    def __init__(self):
        # 获取文章url的请求地址
        self.origin_url = []
        # 保存标题  教育部
        self.titles = []
        # 保存时间
        self.dates = []
        # 保存内容
        self.contents = []
        # 保存来源
        self.sources = []
        # 保存含标签的内容
        self.contentWithLabel = []

        # 获取25页之后文章url的请求地址
        self.origin_url_old = []
        # 保存标题  教育部
        self.titles_old = []
        # 保存时间
        self.dates_old = []
        # 保存内容
        self.contents_old = []
        # 保存来源
        self.sources_old = []
        # 保存含标签的内容
        self.contentWithLabel_old = []

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

    def get_page(self):
        url = 'http://www.moe.gov.cn/jyb_xxgk/xxgk_jyta/'
        html = self.send_request(url)
        # 获取总条数和每页数量的脚本内容
        page_pagesize = html.xpath("//head//script/text()")
        # 获取总条数
        pattern_allcount = re.compile(r'recordCount = (.*?);')
        allcount = pattern_allcount.findall(page_pagesize[0])
        # print(allcount)
        # 获取每页条数
        pattern_pagesize = re.compile(r'pageSize = (.*?);')
        pagesize = pattern_pagesize.findall(page_pagesize[0])
        # print(pagesize)
        self.page = math.ceil(int(allcount[0]) / int(pagesize[0]))


    #  获取教育部里的url里获取具体的文章的url
    def get_education_ministry_url(self):
        # 保存所有可分析dom获取url的网址
        url_lists = ["http://www.moe.gov.cn/jyb_xxgk/xxgk_jyta/"]
        # 获取其它数据源url

        # 前24页的获取文章url的页面结构跟后面的不一样
        for i in range(1, 25):  # 页码1- 24
            url_lists.append("http://www.moe.gov.cn/jyb_xxgk/xxgk_jyta/index_" + str(i) + ".html")
            # print(url_lists)
        self.origin_url = url_lists
        # print(len(self.origin_url))

        # 处理25页之后的结构问题  (25页之后变了一种请求)
        # for i in range(25, 168):  # 页码1- 167
        #     url_lists.append("http://www.moe.gov.cn/was5/web/search?channelid=254874&chnlid=2147438645&page=" + str(i))
        # print(url_lists)
        # self.origin_url = url_lists


    # 获取教育部文章的具体url  加上内容 (新url)
    def get_education_ministry_data(self):
        content_url_list = []
        # 获取并拼接得到url(25页之前的)
        for url in self.origin_url:
            html = self.send_request(url)

            half_contents_urls_lists = html.xpath("//ul[@id='list']//li//a/@href")
            # 因为日期不放在正文url中， 需所以在获取url时一起拿日期
            dates = html.xpath("//ul[@id='list']//li//span/text()")
            self.dates = self.dates + dates
            # 由于获取的url为相对路径  并且有两种url, 所有要对url进行匹配拼接
            for x in half_contents_urls_lists:
                content_url_list.append(x.replace("./", "http://www.moe.gov.cn/jyb_xxgk/xxgk_jyta/"))


        # --------增量爬取操作-------------
        # 保存此次数据源中能够得到的url(可能包括之前爬过)
        need_to_scrapy_url = content_url_list
        # 清空content_url_list 保存未爬取过的url
        content_url_list = []
        # 放之前爬过的url
        result = []  # 从文件中读取得到
        file_read = open('education_ministry_url.txt', 'r')
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
        with open('education_ministry_url.txt', "a", encoding='utf-8') as file:
            file.write(list_str + '\n')
        file.close()

        # 遍历获取所需的内容
        for url_of_content in content_url_list:
            try:
                content_url = url_of_content
                content_html = self.send_request(content_url)
                # 标题
                title = content_html.xpath("//div[@id='content_body']//h1//text()")
                # 来源
                origin_source = content_html.xpath("//p[@id='content_fwzh']/text()")
                # 正文内容
                content = content_html.xpath("//div[@class='TRS_Editor']//text()")
                # 带标签的正文内容
                contentWithLabel = content_html.xpath("//div[@class='TRS_Editor']")[0]
                contentWithLabel = etree.tostring(contentWithLabel, encoding='gbk').decode('gbk')
                contentWithLabel = re.sub(r'class=".*?"', '', contentWithLabel)
                contentWithLabel = re.sub(r'id=".*?"', '', contentWithLabel)
                contentWithLabel = re.sub(r'&#13;', '', contentWithLabel)

                # 存储每一条新闻信息
                self.titles.append(title[0])
                self.contents.append("".join(content))
                self.contentWithLabel.append(contentWithLabel)
                self.sources.append(origin_source[0])

            except Exception as e:
                # print(e)   # 22页之后开始是没有来源的  会报错  所以上面讲来源放在最后一个存储信息
                self.sources.append("")
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
                    "dataDepart": "中华人民共和国教育部",
                    "originSource": self.sources[index],
                    "publishTime": self.dates[index] + " 00:00:00",
                    "theme": "建议提案答复",
                    "title": self.titles[index]
                },
                "type": "中华人民共和国教育部/建议提案答复"
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

    #  获取教育部里的url里获取具体的文章的url
    def get_education_ministry_url_old(self):
        # 保存所有可分析dom获取url的网址
        url_lists = []
        # 获取其它数据源url

        # 处理25页之后的结构问题  (25页之后变了一种请求)
        for i in range(25, self.page+1):  # 页码1- 167
            url_lists.append("http://www.moe.gov.cn/was5/web/search?channelid=254874&chnlid=2147438645&page=" + str(i))
        # print(url_lists)
        self.origin_url_old = url_lists

    # 获取教育部文章的具体url
    def get_education_ministry_data_old(self):
        content_url_list = []

        # 获取25之后的文章url以及日期
        for url in self.origin_url_old:
            html = self.send_request(url)
            page_url_list = html.xpath("//li//a/@href")
            dates = html.xpath("//li//span/text()")
            self.dates_old = self.dates_old + dates
            content_url_list = content_url_list + page_url_list

        # --------增量爬取操作-------------
        # 保存此次数据源中能够得到的url(可能包括之前爬过)
        need_to_scrapy_url = content_url_list
        # 清空content_url_list 保存未爬取过的url
        content_url_list = []
        # 放之前爬过的url
        result = []  # 从文件中读取得到
        file_read = open('education_ministry_url.txt', 'r')
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
        with open('education_ministry_url.txt', "a", encoding='utf-8') as file:
            file.write(list_str + '\n')
        file.close()

        # 遍历获取所需的内容
        for url_of_content in content_url_list:
            try:
                content_url = url_of_content
                content_html = self.send_request(content_url)
                # 标题
                title = content_html.xpath("//div[@id='content_body']//h1//text()")
                # 来源
                origin_source = content_html.xpath("//p[@id='content_fwzh']/text()")
                # 正文内容
                content = content_html.xpath("//div[@class='TRS_Editor']//text()")
                # 带标签的正文内容
                contentWithLabel = content_html.xpath("//div[@class='TRS_Editor']")[0]
                contentWithLabel = etree.tostring(contentWithLabel, encoding='gbk').decode('gbk')
                contentWithLabel = re.sub(r'class=".*?"', '', contentWithLabel)
                contentWithLabel = re.sub(r'id=".*?"', '', contentWithLabel)
                contentWithLabel = re.sub(r'&#13;', '', contentWithLabel)

                # 存储每一条新闻信息
                self.titles_old.append(title[0])
                self.contents_old.append("".join(content))
                self.contentWithLabel_old.append(contentWithLabel)
                self.sources_old.append(origin_source[0])

            except Exception as e:
                # print(e)
                self.sources_old.append("")
        # 保存拼接的每个完整的数据{...},{...}
        data_json_all = ''
        for index in range(len(self.titles_old)):
            data_json = {
                "index": "gdzx_social_data",
                "source": {
                    "classsify": "",
                    "collectTime": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "content": self.contents_old[index],
                    "contentWithLable": self.contentWithLabel_old[index],
                    "dataDepart": "中华人民共和国教育部",
                    "originSource": self.sources_old[index],
                    "publishTime": self.dates_old[index] + " 00:00:00",
                    "theme": "建议提案答复",
                    "title": self.titles_old[index]
                },
                "type": "中华人民共和国教育部/建议提案答复"
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

    # 统一调度
    def start(self):
        # 中华人民共和国教育部-调用
        self.get_page()
        self.get_education_ministry_url()
        self.get_education_ministry_data()

        #  25页之后 中华人民共和国教育部-调用
        self.get_education_ministry_url_old()
        self.get_education_ministry_data_old()

Scrap_News().start()