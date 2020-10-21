# -*- coding:utf8 -*-
import datetime
import json
import random
import re

import requests
from bs4 import BeautifulSoup
from lxml.html import tostring
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import selenium.webdriver.support.ui as ui
from lxml import etree


half_origin_content_url_list = []
half_content_url_list = []

browser = webdriver.Firefox(executable_path="C:\Program Files\Mozilla Firefox\geckodriver.exe")

def is_visible(locator, timeout = 10):
    try:
        ui.WebDriverWait(browser, timeout).until(EC.visibility_of_element_located((By.XPATH, locator)))
        return True
    except TimeoutException:
        return False

browser.get("http://www.nhc.gov.cn/zwgk/tian/ejlist.shtml")
#browser.get("http://www.nhc.gov.cn/yjb/pqt/new_list.shtml")
is_visible("//ul[@class='zwgklist']//li//h3//a")
html = browser.page_source
content = BeautifulSoup(html, "lxml")

# print(content.encode('gbk'))
html1 = etree.HTML(content.encode('gbk'))
# print(html1)


first_origin_urls = html1.xpath("//ul[@class='zwgklist']//li//h3//a/@href")
# 获取页码
page_content = html1.xpath("//ul[@class='zwgklist']//script//text()")
page_pattern = re.compile(r"page_div',(.*?),")
page = page_pattern.findall(page_content[0])
# print(page) # ['57']
half_origin_content_url_list = half_origin_content_url_list + first_origin_urls
# print(first_origin_urls)

for i in range(2,int(page[0])):
    browser.get("http://www.nhc.gov.cn/zwgk/tian/ejlist_" + str(i) + ".shtml")
    is_visible("//ul[@class='zwgklist']//li//h3//a")
    html = browser.page_source
    # print(html)
    content = BeautifulSoup(html, "lxml")
    # print(content.encode('gbk'))
    html1 = etree.HTML(content.encode('gbk'))
    # print(html1)


    origin_urls = html1.xpath("//ul[@class='zwgklist']//li//h3//a/@href")
    # print(origin_urls) # ['../../zwgk/tian/201801/8110f8529a144da2b4ba3a7985ad167c.shtml', '../../zwgk/tian/201801/82c186d5ac714f729a72d6e8e98cd966.shtml']
    half_origin_content_url_list = half_origin_content_url_list + origin_urls


for handle_url in half_origin_content_url_list:
    patten = re.compile(r'zwgk(.*?).shtml')
    half_content_url_list = half_content_url_list + patten.findall(handle_url)
# print(half_content_url_list)

real_content_url_list = []

for half_url in half_content_url_list:
    real_content_url_list.append("http://www.nhc.gov.cn/zwgk" + half_url + ".shtml")
# print(real_content_url_list)

# --------增量爬取操作-------------
# 保存此次数据源中能够得到的url(可能包括之前爬过)
need_to_scrapy_url = real_content_url_list
# real_content_url_list 保存未爬取过的url
real_content_url_list = []
# 放之前爬过的url
result = []  # 从文件中读取得到
file_read = open('health_ministry_url.txt', 'r')
for line in file_read.readlines():
    result.append(line.strip('\n'))
file_read.close()
# print(result)
# 过滤掉之前爬过的url
for new_url in need_to_scrapy_url:
    if new_url not in result:
        real_content_url_list.append(new_url)

# 将新的url追加保存进文本文件
list_str = "\n".join(real_content_url_list)
with open('health_ministry_url.txt', "a", encoding='utf-8') as file:
    file.write(list_str + '\n')
file.close()

a_titles = []
a_contents = []
a_dates = []
a_contentWithLabel = []

for url_of_content in real_content_url_list:
    browser.get(url_of_content)
    # is_visible("/html/body/div[@class='content']")
    html = browser.page_source
    content = BeautifulSoup(html, "lxml")

    # print(content.encode('gbk'))
    html_dom = etree.HTML(content.encode('gbk'))
    # print(html_dom)
    title = html_dom.xpath("//div[@class='title']/text()")
    # print(title)
    date = html_dom.xpath("//span[@class='time']/text()")
    # print(date[0].split('：')[1])
    content = html_dom.xpath("//div[@class='content']//text()")
    # print(content)
    contentWithLabel = html_dom.xpath("//div[@class='content']")[0]
    contentWithLabel = etree.tostring(contentWithLabel, encoding='gbk').decode('gbk')
    contentWithLabel = re.sub(r'class=".*?"', '', contentWithLabel)
    contentWithLabel = re.sub(r'id=".*?"', '', contentWithLabel)
    # 带标签的内容
    contentWithLabel = re.sub(r'&#13;', '', contentWithLabel)
    # print(contentWithLabel)

    a_titles.append(title[0])
    # print(content)
    a_contents.append("".join(content))
    # print(contentWithLabel)
    a_contentWithLabel.append(contentWithLabel)
    # print(date.split('：')[1])
    a_dates.append(date[0].split('：')[1])
    # break
# 保存拼接的每个完整的数据{...},{...}
data_json_all = ''
for index in range(len(a_titles)):
    data_json = {
        "index": "gdzx_social_data",
        "source": {
            "classsify": "",
            "collectTime": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "content": a_contents[index],
            "contentWithLable": a_contentWithLabel[index],
            "dataDepart": "中华人民共和国国家卫生健康委员会",
            "originSource": "",
            "publishTime": a_dates[index] + " 00:00:00",
            "theme": "建议提案答复",
            "title": a_titles[index]
        },
        "type": "中华人民共和国卫生健康委员会/建议提案答复"
    }
    # dict -> json(字符串类型)
    # print(data_json)
    data_json = json.dumps(data_json).encode().decode('utf-8')
    # 每个完整的数据用,拼接起来
    data_json_all = data_json + ',' + data_json_all
data_json_all = data_json_all[:-1]
str = "[" + data_json_all + "]"
# print(str)
# 设置上传信息的请求头
headers = {'content-type': "application/json", 'apikey': 'c4ce1c0958261e1dea72afc0665f9c68'}
# 向接口发送数据
res = requests.post("http://inc.sworddata.cn:8883/es/api/addArticle", headers=headers, data=str)

print(res.status_code)
print(res.text)

