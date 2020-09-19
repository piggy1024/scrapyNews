# -*- coding:utf8 -*-
import datetime
import json
import random
import re
import requests
from lxml import etree
# 特点: 内容都是文字; url 从script中取; 内容一天一更
class Scrap_News(object):
    def __init__(self):
        self.url_yw = []
        # 保存标题  政协网-要闻
        self.titles_yw = []
        # 保存时间
        self.dates_yw = []
        # 保存内容
        self.contents_yw = []
        # 保存来源
        self.origin_sources_yw = []
        # 保存含标签的内容
        self.contentWithLabel = []

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

    # 政协网-要闻
    def get_url_yw(self):
        # 要闻  ---- script[3]
        url_yw = "http://www.cppcc.gov.cn/zxww/newcppcc/zxyw/index.shtml"
        # 要闻-url获取
        data_yw = self.send_request(url_yw)
        script_yw = data_yw.xpath("//script/text()")
        pattern1 = re.compile(r'http://(.*?).shtml')
        all_urls_yw = pattern1.findall(script_yw[3])
        base_url_q = "http://"
        base_url_h = ".shtml"
        # 拼接得到文章的url
        url_lists_yw = []
        for x in all_urls_yw:
            complete_urls = base_url_q + x + base_url_h
            url_lists_yw.append(complete_urls)

        # --------增量爬取操作-------------
        # 保存此次数据源中能够得到的url(可能包括之前爬过)
        need_to_scrapy_url = url_lists_yw
        # 清空url_lists_yw 保存未爬取过的url
        url_lists_yw = []
        # 放之前爬过的url
        result = []  # 从文件中读取得到
        file_read = open('zhengxie_yw_url.txt', 'r')
        for line in file_read.readlines():
            result.append(line.strip('\n'))
        file_read.close()
        # print(result)
        # 过滤掉之前爬过的url得到未爬取的url
        for new_url in need_to_scrapy_url:
            if new_url not in result:
                url_lists_yw.append(new_url)

        # 将新的url追加保存进文本文件
        list_str = "\n".join(url_lists_yw)
        with open('zhengxie_yw_url.txt', "a", encoding='utf-8') as file:
            file.write(list_str + '\n')
        file.close()


        #   赋值给全局的url保存
        self.url_yw = url_lists_yw

    # 获取全国政协网-要闻-具体文章函数
    def get_zhengxie_yw_content(self):
        url_yw = self.url_yw
        for url in url_yw:
            html = self.send_request(url)
            # 标题
            titles = html.xpath("//div[@class='cnt_box']//h3/text()")
            # 不包标签的内容
            content = html.xpath("//div[@class='con']//p/text()")
            # 发布日期
            date = html.xpath("//div[@class='infobox']//i/text()")
            # 来源
            origin_source = html.xpath("//div[@class='infobox']//em/text()")
            # 带标签的内容
            contentWithLabel = html.xpath("//div[@class='cnt_box']//div[@class='con']")[0]
            contentWithLabel = etree.tostring(contentWithLabel, encoding='utf-8').decode('utf-8')
            contentWithLabel = re.sub(r'class=".*?"', '', contentWithLabel)
            contentWithLabel = re.sub(r'&#13;', '', contentWithLabel)
            try:
                self.titles_yw.append(''.join(titles))
                self.contents_yw.append(''.join(content))
                self.dates_yw.append(date[0])
                self.origin_sources_yw.append(origin_source[1])
                self.contentWithLabel.append(contentWithLabel)
            except Exception as e:
                # print(e)
                self.origin_sources_yw.append("")
                self.contentWithLabel.append("")

        # 保存拼接的每个完整的数据{...},{...}
        data_json_all = ''
        for index in range(len(self.titles_yw)):
            data_json = {
                "index": "gdzx_social_data",
                "source": {
                    "classsify": "",
                    "collectTime": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "content": self.contents_yw[index],
                    "contentWithLable": self.contentWithLabel[index],
                    "dataDepart": "全国政协网",
                    "originSource": self.origin_sources_yw[index],
                    "publishTime": self.dates_yw[index]+" 00:00:00",
                    "theme": "要闻",
                    "title": self.titles_yw[index]
                },
                "type": "全国政协网/要闻"
            }
            # dict -> json(字符串类型)  (麻烦)gbk需要根据情况变化
            data_json = json.dumps(data_json).encode().decode('utf-8')
            # 每个完整的数据用,拼接起来
            data_json_all = data_json + ',' + data_json_all
        #  去掉最后一个逗号
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
        # 全国政协网-要闻-调用
        self.get_url_yw() # 获取url
        self.get_zhengxie_yw_content()

Scrap_News().start()