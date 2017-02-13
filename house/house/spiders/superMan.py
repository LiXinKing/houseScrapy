#coding=utf8
import scrapy
import traceback
import copy
import codecs
import csv
import os
import re


class superMan(scrapy.spiders.Spider):
    name = "superMan"
    start_urls = ["http://cd.fang.lianjia.com/loupan/", ]
    base_url = "http://cd.fang.lianjia.com"
    csv_name = "test.csv"
    total_page = 0
    cur_page = 1

    def init_file(self):
        if not os.path.exists(self.csv_name):
            with open(self.csv_name, 'wb') as f:
                f.write(codecs.BOM_UTF8)
                span_writer = csv.writer(f, dialect='excel')
                span_writer.writerow(["每平方的均价",
                                      "楼盘开盘时间",
                                      "户型情况",
                                      "户型面积",
                                      "是否在销售",
                                      "楼盘的位置",
                                      "楼盘折扣情况",
                                      "楼盘信息更新时间",
                                      "户型的朝向",
                                      "户型销售状态",
                                      "户型价格(万)",
                                      "住房类型",
                                      "户型更新时间"])

    def write_all_info(self, all_info_list):
        # 写表头
        self.init_file()

        with open(self.csv_name, 'ab+') as f:
            f.write(codecs.BOM_UTF8)
            span_writer = csv.writer(f, dialect='excel')
            for info_dict in all_info_list:
                span_writer.writerow([value.encode('utf-8') for value in info_dict.values()])

    def one_house_parse(self, response):
        x_path_base_info = '//div[@class="mod-banner"]/div[@class="banner-box"]/'
        x_path_open_time_info = x_path_base_info + 'div[@class="when-detail formis"]/div[@class="w-con"]/p'
        x_path_discount_info = x_path_base_info + 'div[@class="youhui-detail formis"]/div[@class="y-con"]/p'

        x_path_whole_info_base = x_path_base_info + 'div[@class="box-left"]/div[@class="box-left-top"]/'
        x_path_state_info = x_path_whole_info_base + 'div[@class="name-box"]/div[@class="state-div"]/span[@class="state"]'
        x_path_price_info = x_path_whole_info_base + 'p[@class="jiage"]/span[@class="junjia"]'
        x_path_update_info = x_path_whole_info_base + 'p[@class="update"]/span'

        x_path_project_info_base = x_path_base_info + 'div[@class="box-left"]/div[@class="box-left-bottom clickTargetBox"]/div[@class="bottom-info"]/'
        x_path_project_type = x_path_project_info_base + 'p[@class="small-tags"]/span[@class="popular"]'
        # x_path_car_status = x_path_project_info_base + 'p[@class="small-tags"]/span[@class="q70"]'
        x_path_address = x_path_project_info_base + 'p[@class="where"]/span'

        x_path_user_info_base = '//div[@class="mod-wrap"]/div[@class="clear mod-panel-houseonline mod-house-online"]/div/div[@class="houselist"]/ul[@class="clear house-det"]/li[@class="info-li"]/'
        x_path_user_info = x_path_user_info_base + 'p[@class="p1"]'
        x_path_user_area = x_path_user_info + '/span[not(contains(@class,"p1"))]'
        x_path_user_ori = x_path_user_info + '/span[@class="p1-orientation "]'
        x_path_user_status = x_path_user_info + '/span[@class="p1-state p1-green"]'
        x_path_user_cost = x_path_user_info_base + 'p[@class="p2"]/span[not(contains(@class,"p2-time"))]'
        x_path_user_update = x_path_user_info_base + 'p[@class="p2"]/span[@class="p2-time"]'

        # 所有的待抓取数据
        scrapy_xpath_whole_info = {
            "x_path_open_time_info": x_path_open_time_info,     # 楼盘开盘时间
            "x_path_discount_info": x_path_discount_info,       # 楼盘折扣情况
            "x_path_state_info": x_path_state_info,             # 是否在销售
            "x_path_price_info": x_path_price_info,             # 每平方的均价
            "x_path_update_info": x_path_update_info,           # 楼盘信息更新时间
            "x_path_project_type": x_path_project_type,         # 住房类型：普通住宅或者别墅
            # "x_path_car_status": x_path_car_status,           # 楼盘的车位情况
            "x_path_address": x_path_address,                   # 楼盘的位置
        }

        scrapy_xpath_user_info = {
            "x_path_user_info": x_path_user_info,           # 户型情况
            "x_path_user_area": x_path_user_area,           # 户型面积
            "x_path_user_ori": x_path_user_ori,             # 户型的朝向
            "x_path_user_status": x_path_user_status,       # 户型销售状态
            "x_path_user_cost": x_path_user_cost,           # 户型价格
            "x_path_user_update": x_path_user_update,       # 户型更新时间
        }

        # 保存楼盘全局信息
        all_info_list = []

        # 保存楼盘全局信息的字典
        whole_info_dict = {}

        # 读取整个楼盘的信息
        for key, value in scrapy_xpath_whole_info.items():
            # 可能有些信息某些楼盘没有
            whole_info_dict[key] = 'N/A'
            for line in response.xpath(value + '/text()').extract():
                if whole_info_dict[key] == 'N/A':
                    whole_info_dict[key] = line
                else:
                    whole_info_dict[key] += line

        # 户型信息
        user_info_dict = {}

        # 抓取每个户型的信息
        for key, value in scrapy_xpath_user_info.items():
            user_info_dict[key] = []
            for line in response.xpath(value + '/text()').extract():
                user_info_dict[key].append(line)

        try:
            for user_info_list in zip(*[value for key, value in user_info_dict.items()]):
                # 每个户型的全部信息
                all_info_per_user = copy.deepcopy(whole_info_dict)

                for i in range(len(user_info_list)):
                    all_info_per_user[scrapy_xpath_user_info.keys()[i]] = user_info_list[i]

                # 加入的全局信息结合
                all_info_list.append(all_info_per_user)
        except:
            traceback.print_exc()

        # 写入到文件中
        self.write_all_info(all_info_list)

    def parse(self, response):
        x_path = '//div[@class="wrapper"]/div[@class="main-box clear"]/div[@class="con-box"]/div[@class="list-wrap"]/ul/li/div[@class="pic-panel"]/a/@href'
        x_page_path= '//div[@class="page-box house-lst-page-box"]'

        for page in response.xpath(x_page_path).extract():
            m = re.search(r'.*totalPage":(.*),', page)
            self.total_page = int(m.group(1))

            m = re.search(r'.*curPage":(.*)\}', page)
            self.cur_page = int(m.group(1))

        for url in response.xpath(x_path).extract():
            yield scrapy.Request(self.base_url + url, callback = self.one_house_parse)

        # 下一页
        # 访问http://cd.fang.lianjia.com/loupan/pg2/
        self.cur_page += 1
        if self.cur_page <= self.total_page:
            yield scrapy.Request(self.base_url + "/loupan/pg%s/" % (self.cur_page), callback = self.parse)
