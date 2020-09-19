# -*- coding:utf8 -*-
import datetime
import json
import random
import re
import requests
from lxml import etree

class Scrap_News(object):
    def __init__(self):
        # 获取文章url的请求地址
        # 文章url有两种  一种新的一种是旧的
        self.old_origin_url = []
        self.new_origin_url = []
        # 保存标题  农业农村部-
        self.titles = []
        # 保存时间
        self.dates = []
        # 保存内容
        self.contents = []
        # 保存来源
        self.sources = []
        # 保存含标签的内容
        self.contentWithLabel = []
        # 摘要
        self.abstract = []
        # 变化url的页码
        self.change_page = 0
        # 总页码
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
        # 获取总页码
        html = self.send_request("http://www.moa.gov.cn/gk/jyta/index.htm")
        change_date = html.xpath("//div[@class='next']//script//text()")
        # print(change_date)
        pattern = re.compile(r'countPage = (.*?)/')
        x = pattern.findall(change_date[0])
        self.page = int(x[0])
        # print(self.page)


        # 获取文章url开始变化的页码
        index = 1
        # 判断是否退出循环
        flag = 0
        while index > 0:
            html = self.send_request("http://www.moa.gov.cn/gk/jyta/index_" + str(index) + ".htm")
            change_date = html.xpath("//div[@class='gknr_content1']//ul//li//span//text()")
            for date in change_date:
                if date == '2020-04-17':
                    self.change_page = index
                    flag = 1
            # 每次循环都要判断是否找到2020-04-17,找到则记录页码退出循环
            if flag:
                break
            index = index +1
        # print(self.change_page)



    # 获取农业农村部文章的具体url  加上内容 (旧url新结构)
    def get_old_rural_ministry_data(self):
        # 从数据源url取出需要拼接部分的url
        old_half_url_list = []  # 存储旧类型的需要拼接部分的url
        # 利用正则匹配从数据源的页面获取类型的需要拼接部分的url
        for url in self.old_origin_url:
            html = self.send_request(url)
            contents_urls_lists = html.xpath("//div[@class='gknr_content1']//ul//li//a/@href")
            # 由于获取的url为相对路径  并且有两种url, 所有要对url进行匹配拼接
            for x in contents_urls_lists:
                # 先匹配新型的url  '../../govpublic/nybzzj1/202009/t20200904_6351571.htm'    旧型 './202004/t20200426_6342356.htm'
                patten = re.compile(r'.(.*?).htm')  # 会包含../../govpublic/nybzzj1/202009/t20200904_6351571.htm
                old_half_url_list = old_half_url_list + patten.findall(x)

        # 拼接出真正的文章url
        real_contents_urls_list = []
        for half_url in old_half_url_list:
            real_contents_urls_list.append("http://www.moa.gov.cn/gk/jyta" + half_url + ".htm")

        # 查看旧新闻url类型的条数
        print('旧新闻url条数:')
        print(len(real_contents_urls_list))

        # --------增量爬取操作-------------
        # 保存此次数据源中能够得到的url(可能包括之前爬过)
        need_to_scrapy_url = real_contents_urls_list
        # 清空real_contents_urls_list 保存未爬取过的url
        real_contents_urls_list = []
        # 放之前爬过的url
        result = []  # 从文件中读取得到
        file_read = open('rural_ministry_url.txt', 'r')
        for line in file_read.readlines():
            result.append(line.strip('\n'))
        file_read.close()
        # print(result)
        # 过滤掉之前爬过的url
        for new_url in need_to_scrapy_url:
            if new_url not in result:
                real_contents_urls_list.append(new_url)

        # 将新的url追加保存进文本文件
        list_str = "\n".join(real_contents_urls_list)
        with open('rural_ministry_url.txt', "a", encoding='utf-8') as file:
            file.write(list_str + '\n')
        file.close()

        # 遍历得到所需的内容
        for url_of_content in real_contents_urls_list:
            content_url = url_of_content
            content_html = self.send_request(content_url)
            # 先判断标题是否取到内容,如果取到则是新结构,否则为旧结构
            flag = content_html.xpath("//div[@class='ctitle']//h2/text()")
            if len(flag) == 0:
                try:
                    # 标题
                    title = content_html.xpath("//h1[@class='bjjMTitle']/text()")
                    # 正文
                    content = content_html.xpath("//div[@class='arc_body mg_auto w_855 pd_b_35']//p//text()")
                    # 日期
                    date = content_html.xpath(
                        "//div[@class='bjjMAuthorBox']//span[@class='dc_2']//span[@class='dc_3']/text()")
                    # 带标签的正文
                    contentWithLabel = content_html.xpath("//div[@class='arc_body mg_auto w_855 pd_b_35']")[0]
                    contentWithLabel = etree.tostring(contentWithLabel, encoding='gbk').decode('gbk')
                    contentWithLabel = re.sub(r' class=".*?"', '', contentWithLabel)
                    # 去掉正文里面的<style></style>
                    contentWithLabel = re.sub(r'<style(([\s\S])*?)</style>', '', contentWithLabel)
                    # 存储每一条新闻信息
                    self.titles.append(title[0])
                    self.contents.append("".join(content))
                    self.dates.append(date[0] + ":00")
                    self.contentWithLabel.append(contentWithLabel)
                    self.abstract.append("")
                except Exception as e:
                    print(e)
                    print(content_url)
            else:
                try:
                    # 标题
                    title = content_html.xpath("//div[@class='ctitle']//h2/text()")
                    # 摘要
                    abstract = content_html.xpath("//div[@class='content_head mhide']")[0]
                    abstract = etree.tostring(abstract, encoding='gbk').decode('gbk')
                    # 内容
                    content = content_html.xpath("//div[@class='gsj_htmlcon_bot']//p//span/text()")
                    # 日期
                    date = content_html.xpath(
                        "//div[@class='ctitle']//div[@class='subtitle']//p[@class='pubtime']/text()")
                    # 带标签的内容
                    contentWithLabel = content_html.xpath("//div[@class='gsj_htmlcon_bot']")[0]
                    contentWithLabel = etree.tostring(contentWithLabel, encoding='gbk').decode('gbk')
                    contentWithLabel = re.sub(r'class=".*?"', '', contentWithLabel)
                    contentWithLabel = re.sub(r'id=".*?"', '', contentWithLabel)
                    contentWithLabel = re.sub(r'&#13;', '', contentWithLabel)

                    # 存储每一条新闻信息
                    self.titles.append(title[0])
                    self.abstract.append(abstract)
                    self.contents.append("".join(content))
                    # 处理日期格式 date = ['发布时间：2020年09月04日']
                    real_date = date[0].split("：")[1]
                    real_date = re.sub(r'年|月', "-", real_date)
                    real_date = re.sub(r'日', " ", real_date)
                    self.dates.append(real_date + ":00")
                    self.contentWithLabel.append(contentWithLabel)
                except Exception as e:
                    print(e)
        print("旧标题爬取到的数据条数:")
        print(len(self.titles))
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
                    "dataDepart": "中华人民共和国农业农村部",
                    "originSource": "",
                    "publishTime": self.dates[index],
                    "theme": "建议提案答复",
                    "title": self.titles[index],
                    "abstract": self.abstract[index]
                },
                "type": "中华人民共和国农业农村部/建议提案答复"
            }
            # dict -> json(字符串类型)
            data_json = json.dumps(data_json).encode().decode('utf-8')
            # 每个完整的数据用,拼接起来
            data_json_all = data_json + ',' + data_json_all
        # 拼接并向接口发送数据
        data_json_all = data_json_all[:-1]
        str = "[" + data_json_all + "]"
        # print(str)
        # 设置上传信息的请求头
        headers = {'content-type': "application/json", 'apikey': 'c4ce1c0958261e1dea72afc0665f9c68'}
        # 向接口发送数据
        res = requests.post("http://inc.sworddata.cn:8883/es/api/addArticle", headers=headers, data=str)

        print(res.status_code)
        print(res.text)
    #  获取农业农村部里的url里获取具体的文章的url(新类型)
    def get_old_rural_ministry_url(self):
        # 保存所有可分析dom获取url的网址
        old_url_lists = []
        # 从日期为2020-04-17那天的新闻之后的新闻url
        for i in range(self.change_page+1, self.page+1):
            old_url_lists.append("http://www.moa.gov.cn/gk/jyta/index_" + str(i) + ".htm")
        self.old_origin_url = old_url_lists


    #  获取农业农村部里的url里获取具体的文章的url(新类型)
    def get_rural_ministry_url(self):
        # 保存所有可分析dom获取url的网址
        new_url_lists = ["http://www.moa.gov.cn/gk/jyta/index.htm"]
        # 从日期为2020-04-17那天的新闻之后文章url变了新网址
        for i in range(1, self.change_page+1):
            new_url_lists.append("http://www.moa.gov.cn/gk/jyta/index_" + str(i) + ".htm")
        self.new_origin_url = new_url_lists
    # 获取农业农村部文章的具体url  加上内容 (新url)
    def get_rural_ministry_data(self):
        # 从数据源url取出需要拼接部分的url
        new_half_url_list = [] # 存储新类型的需要拼接部分的url
        # 利用正则匹配从数据源的页面获取类型的需要拼接部分的url
        for url in self.new_origin_url:
            html = self.send_request(url)
            contents_urls_lists = html.xpath("//div[@class='gknr_content1']//ul//li//a/@href")
            # 由于获取的url为相对路径  并且有两种url, 所有要对url进行匹配拼接
            for x in contents_urls_lists:
                # 先匹配新型的url  '../../govpublic/nybzzj1/202009/t20200904_6351571.htm'    旧型 './202004/t20200426_6342356.htm'
                patten = re.compile(r'govpublic(.*?).htm')
                new_half_url_list = new_half_url_list + patten.findall(x)

        # 拼接出真正的文章url
        real_contents_urls_list = []
        for half_url in new_half_url_list:
            real_contents_urls_list.append("http://www.moa.gov.cn/govpublic" + half_url + ".htm")

        # 查看新新闻url类型的条数
        print("新url条数:")
        print(len(real_contents_urls_list))

        # --------增量爬取操作-------------
        # 保存此次数据源中能够得到的url(可能包括之前爬过)
        need_to_scrapy_url = real_contents_urls_list
        # 清空real_contents_urls_list 保存未爬取过的url
        real_contents_urls_list = []
        # 放之前爬过的url
        result = []  # 从文件中读取得到
        file_read = open('rural_ministry_url.txt', 'r')
        for line in file_read.readlines():
            result.append(line.strip('\n'))
        file_read.close()
        # print(result)
        # 过滤掉之前爬过的url
        for new_url in need_to_scrapy_url:
            if new_url not in result:
                real_contents_urls_list.append(new_url)

        # 将新的url追加保存进文本文件
        list_str = "\n".join(real_contents_urls_list)
        with open('rural_ministry_url.txt', "a", encoding='utf-8') as file:
            file.write(list_str + '\n')
        file.close()

        for url_of_content in real_contents_urls_list:
            try:
                content_url = url_of_content
                content_html = self.send_request(content_url)
                # 标题
                title = content_html.xpath("//div[@class='ctitle']//h2/text()")
                # 摘要
                abstract = content_html.xpath("//div[@class='content_head mhide']")[0]
                abstract = etree.tostring(abstract, encoding='gbk').decode('gbk')
                # 内容
                content = content_html.xpath("//div[@class='gsj_htmlcon_bot']//p//span/text()")
                # 日期
                date = content_html.xpath("//div[@class='ctitle']//div[@class='subtitle']//p[@class='pubtime']/text()")
                # 带标签的内容
                contentWithLabel = content_html.xpath("//div[@class='gsj_htmlcon_bot']")[0]
                contentWithLabel = etree.tostring(contentWithLabel, encoding='gbk').decode('gbk')
                contentWithLabel = re.sub(r'class=".*?"', '', contentWithLabel)
                contentWithLabel = re.sub(r'id=".*?"', '', contentWithLabel)
                contentWithLabel = re.sub(r'&#13;', '', contentWithLabel)

                # 存储每一条新闻信息
                self.titles.append(title[0])
                self.abstract.append(abstract)
                self.contents.append("".join(content))
                # 处理日期格式 date = ['发布时间：2020年09月04日']
                real_date = date[0].split("：")[1]
                real_date = re.sub(r'年|月', "-", real_date)
                real_date = re.sub(r'日', " ", real_date)
                self.dates.append(real_date + " 00:00:00")
                self.contentWithLabel.append(contentWithLabel)
            except Exception as e:
                print(e)
        # 保存拼接的每个完整的数据{...},{...}
        data_json_all = ''
        print("新url实际爬取条数:")
        print(len(self.titles))
        for index in range(len(self.titles)):
            data_json = {
                "index": "gdzx_social_data",
                "source": {
                    "classsify": "",
                    "collectTime": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "content": self.contents[index],
                    "contentWithLable": self.contentWithLabel[index],
                    "dataDepart": "中华人民共和国农业农村部",
                    "originSource": "",
                    "publishTime": self.dates[index],
                    "theme": "建议提案答复",
                    "title": self.titles[index],
                    "abstract": self.abstract[index]
                },
                "type": "中华人民共和国农业农村部/建议提案答复"
            }
            # dict -> json(字符串类型)
            data_json = json.dumps(data_json).encode().decode('utf-8')
            # 每个完整的数据用,拼接起来
            data_json_all = data_json + ',' + data_json_all
        data_json_all = data_json_all[:-1]
        str = "[" + data_json_all + "]"
        # print(str)
        # 设置上传信息的请求头
        # headers = {'content-type': "application/json", 'apikey': 'c4ce1c0958261e1dea72afc0665f9c68'}
        # 向接口发送数据
        # res = requests.post("http://inc.sworddata.cn:8883/es/api/addArticle", headers=headers, data=str)

        # print(res.status_code)
        # print(res.text)



    # 统一调度
    def start(self):
        # 中华人民共和国国家卫生健康委员会-调用
        self.get_page()

        # 之后爬取只需要调用下面两个函数
        self.get_rural_ministry_url() # 获取新类型url
        self.get_rural_ministry_data() # 获取新类型url的文章内容

        # 旧文章url数据的爬取
        self.get_old_rural_ministry_url()  # 获取旧类型url
        self.get_old_rural_ministry_data()  # 获取旧类型url的文章内容

Scrap_News().start()