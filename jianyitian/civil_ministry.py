# -*- coding:utf8 -*-
import datetime
import json
import random
import re
import requests
from lxml import etree
from lxml.html import tostring


class Scrap_News(object):
    def __init__(self):
        # 获取文章url的请求地址
        self.origin_url = []
        # 保存标题  民政部
        self.titles = []
        # 保存时间
        self.dates = []
        # 保存内容
        self.contents = []
        # 保存来源
        self.sources = []
        # 保存含标签的内容
        self.contentWithLabel = []

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
        # data = requests.get(url, headers=self.headers).content.decode()
        response = requests.get(url, headers=self.headers)
        self.code = response.encoding
        # print(self.code)
        html = etree.HTML(response.content)

        return html

    #  获取民政部里的url里获取具体的文章的url
    def get_civil_ministry_url(self):
        # 获取页码
        html = self.send_request('http://www.mca.gov.cn/article/gk/jytabljggk/zxwyta/')
        all_page = html.xpath("//ul[@class='alist_ul']//script//text()")
        pattern = re.compile(r'totalpage = "(.*?)"')
        last_page = pattern.findall(all_page[0])
        # 保存所有可分析dom获取url的网址(保存了第一个url数据源)
        url_lists = ["http://www.mca.gov.cn/article/gk/jytabljggk/zxwyta/"]
        # 从第二个开始取数据源
        for i in range(2, int(last_page[0])+1):
            url_lists.append("http://www.mca.gov.cn/article/gk/jytabljggk/zxwyta/?" + str(i))
        self.origin_url = url_lists


    # 获取民政部文章的具体url  加上内容 (新url)
    def get_civil_ministry_data(self):
        content_url_list = []
        # 获取拼接得到文章的url
        for url in self.origin_url:
            html = self.send_request(url)
            half_contents_urls_lists = html.xpath("//ul[@class='alist_ul']//table[@class='article']//tr//td//a/@href")
            # 由于获取的url为相对路径  并且有两种url, 所有要对url进行匹配拼接
            for x in half_contents_urls_lists:
                content_url_list.append("http://www.mca.gov.cn" + x)

        # --------增量爬取操作-------------
        # 保存此次数据源中能够得到的url(可能包括之前爬过)
        need_to_scrapy_url = content_url_list
        # 清空content_url_list 保存未爬取过的url
        content_url_list = []
        # 放之前爬过的url
        result = []  # 从文件中读取得到
        file_read = open('civil_ministry_url.txt', 'r')
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
        with open('civil_ministry_url.txt', "a", encoding='utf-8') as file:
            file.write(list_str + '\n')
        file.close()


        # 遍历获取所需的内容
        for url_of_content in content_url_list:
            try:
                content_url = url_of_content
                content_html = self.send_request(content_url)
                # 标题\日期\来源  均放在script中
                info = content_html.xpath("//body//script/text()")
                # 标题
                pattern_title = re.compile(r"atitle = '(.*?)';")
                title = pattern_title.findall(info[0])
                # 日期
                pattern_date = re.compile(r"tm = '(.*?)';")
                date = pattern_date.findall(info[0])
                # 来源
                pattern_source = re.compile(r"source = '(.*?)';")
                origin_source = pattern_source.findall(info[0])
                # 带标签的内容
                content = content_html.xpath("//div[@class='content']//text()")
                contentWithLabel = content_html.xpath("//div[@class='content']")[0]
                contentWithLabel = etree.tostring(contentWithLabel, encoding='gbk').decode('gbk')
                contentWithLabel = re.sub(r'class=".*?"', '', contentWithLabel)
                contentWithLabel = re.sub(r'id=".*?"', '', contentWithLabel)
                contentWithLabel = re.sub(r'&#13;', '', contentWithLabel)

                # 存储每一条所需的新闻信息
                self.titles.append(title[0])
                self.contents.append("".join(content))
                self.dates.append(date[0])
                self.sources.append(origin_source[0])
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
                    "dataDepart": "中华人民共和国民政部",
                    "originSource": self.sources[index],
                    "publishTime": self.dates[index],
                    "theme": "建议提案答复",
                    "title": self.titles[index]
                },
                "type": "中华人民共和国民政部/建议提案答复"
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
        # 中华人民共和国民政部-调用
        self.get_civil_ministry_url()
        self.get_civil_ministry_data()


Scrap_News().start()