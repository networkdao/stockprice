# -*- coding: utf-8 -*-
"""
Version: 1.0
Author: John
Date: 2023-10-22
"""
import os
import sys
import csv
import json,urllib
import time
import logging
import requests
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import urlopen
from alibabacloud_dysmsapi20170525.client import Client as Dysmsapi20170525Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dysmsapi20170525 import models as dysmsapi_20170525_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient
from typing import List  # 导入 List 类型提示

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# nowapi获取黄金的 api
go_url = 'http://api.k780.com'
go_app = 'finance.gold_price'
# 仅仅获取 1053
goldid = os.getenv('GOLDID')
go_appkey = os.getenv('GO_APPKEY')
go_sign = os.getenv('GO_SIGN')

# 阿里云短信服务配置
access_key_id = os.getenv('ACCESS_KEY_ID')
access_key_secret = os.getenv('ACCESS_KEY_SECRET')
phone_numbers = os.getenv('PHONE_NUMBERS')
sign_name = os.getenv('SIGN_NAME')
template_code = os.getenv('TEMPLATE_CODE')
file_name_1 = 'gold_price.csv'
file_name_2 = 'sms_status.csv'



# 定义文件名和鹿筋，切换到 linux 后修改目录
file_name_1 = '/pythonenv/goldenv/data/gold_prices.csv'
file_name_2 = '/pythonenv/goldenv/data/sms_status.csv'

def ensure_header(file_name, header):
    """确保文件中存在表头，如果没有则写入表头"""
    file_exists = os.path.isfile(file_name)
    if file_exists:
        with open(file_name, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            first_row = next(reader, None)
            if first_row != header:
                with open(file_name, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(header)
    else:
        with open(file_name, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(header)

# 确保文件有表头
ensure_header(file_name_1, ['操作系统时间', '品类名字', 'API 获取时间', '买入价格', '卖出价格'])
ensure_header(file_name_2, ['操作系统时间', 'BizId', 'RequestId', '是否发送短信成功'])

# 获取黄金价格的函数
def get_gold_price():
    params = {
      'app' : go_app,
      # 仅仅获取 1053
      'goldid' : goldid,
      'appkey' : go_appkey,
      'sign' : go_sign,
      'format' : 'json',
    }
    params = urlencode(params)
    try:
        response = urllib.request.urlopen('%s?%s' % (go_url, params))
        data = response.read()
        data_result = json.loads(data)
        if data_result['success'] != '0':
            print(data_result['result'])
        else:
            print(data_result['msgid'] + ' ' + data_result['msg'] )
        return {
            'buy_price': data_result['result']['dtList']['1053']['buy_price'],
            'sell_price': data_result['result']['dtList']['1053']['sell_price'],
            'uptime': data_result['result']['dtList']['1053']['uptime']
        }
    
    except requests.RequestException as e:
        logging.error(f"Error fetching gold price: {e}")
        return None

gold_price = get_gold_price()   
print('gold_price :', gold_price) 

# 发送短信的函数
class Sample:
    @staticmethod
    def create_client() -> Dysmsapi20170525Client:
        config = open_api_models.Config(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret
        )
        config.endpoint = 'dysmsapi.aliyuncs.com'
        return Dysmsapi20170525Client(config)

# 发送短信的函数2
def send_sms(buy_price, uptime):    
    # Your code here
    client = Sample.create_client()
    send_sms_request = dysmsapi_20170525_models.SendSmsRequest(
        phone_numbers=phone_numbers,
        sign_name=sign_name,
        template_code=template_code,
        template_param=json.dumps({"time": uptime, "price": buy_price})  # 模板变量 
    )
    runtime = util_models.RuntimeOptions()
    try:
        response = client.send_sms_with_options(send_sms_request, runtime)
        response_data = response.body
        return {
            'BizId': response_data.biz_id,
            'RequestId': response_data.request_id,
            'sendmsg_status': response_data.code
        }
    except Exception as error:
        logging.error(f"Error sending SMS: {str(error)}")
        return {
            'BizId': '',
            'RequestId': '',
            'sendmsg_status': False
        }


# 主函数
def main():
    gold_price = get_gold_price()
    if gold_price:
        # 写入黄金价格 CSV
        with open(file_name_1, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([datetime.now().isoformat(), '黄金9999', gold_price['uptime'], gold_price['buy_price'], gold_price['sell_price']])
            print   (datetime.now().isoformat(), '黄金9999', gold_price['uptime'], gold_price['buy_price'], gold_price['sell_price'])
            # 判断是否需要发送短信
        if float(gold_price['buy_price']) < 630:
            response_data = send_sms(gold_price['buy_price'], gold_price['uptime'])
                
            # 写入短信状态 CSV, 操作系统时间, BizId, RequestId, 是否发送短信成功
            with open(file_name_2, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([datetime.now().isoformat(), response_data['BizId'], response_data['RequestId'], response_data['sendmsg_status']])
                print(datetime.now().isoformat(), response_data['BizId'], response_data['RequestId'], response_data['sendmsg_status'])
        # 等待 60 秒 临时改成 3600s，如果 python3 filename 运行的时候，就会发现这个程序，运行后挂起，不结束,每隔 3600s 执行一次

if __name__ == "__main__":
    main()
