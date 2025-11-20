#!/usr/bin/env python3
"""上海旅游景点实时数据爬取器 - 简化版"""

import os
import requests
import json
import oss2
from datetime import datetime

# 配置
OSS_ACCESS_KEY_ID = os.getenv('OSS_ACCESS_KEY_ID')
OSS_ACCESS_KEY_SECRET = os.getenv('OSS_ACCESS_KEY_SECRET')
OSS_ENDPOINT = os.getenv('OSS_ENDPOINT', 'oss-cn-shanghai.aliyuncs.com')
OSS_BUCKET_NAME = os.getenv('OSS_BUCKET_NAME', 'shanghai-tourist-traffic')
API_URL = 'https://tourist.whlyj.sh.gov.cn/api/statistics/getViewTourist'

class TouristCrawler:
    def __init__(self):
        if not all([OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET, OSS_BUCKET_NAME]):
            raise ValueError("缺少必要的OSS配置项")
        
        auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
        self.bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://tourist.whlyj.sh.gov.cn/'
        }
    
    def fetch_data(self):
        try:
            response = requests.get(API_URL, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get('code') != 200:
                print(f"API返回错误: {data.get('msg', '未知错误')}")
                return None
            
            print(f"成功获取数据，共 {data.get('total', 0)} 条记录")
            return data
        except Exception as e:
            print(f"获取数据失败: {e}")
            return None
    
    def append_to_oss(self, path, content):
        try:
            if self.bucket.object_exists(path):
                head_result = self.bucket.head_object(path)
                position = head_result.content_length
                result = self.bucket.append_object(path, position, content.encode('utf-8'))
            else:
                result = self.bucket.append_object(path, 0, content.encode('utf-8'))
            
            if result.status == 200:
                print(f"数据追加成功: {path}")
                return True
            return False
        except Exception as e:
            print(f"追加数据失败: {e}")
            return False
    
    def upload_data(self, data):
        now = datetime.now()
        
        # 按日期存储
        daily_path = f"tourist_data/{now.strftime('%Y/%m/%d')}.jsonl"
        daily_record = json.dumps({
            'timestamp': now.isoformat(),
            'data': data
        }, ensure_ascii=False) + '\n'
        
        daily_success = self.append_to_oss(daily_path, daily_record)
        
        # 按景点存储
        spot_success = True
        if 'rows' in data:
            for spot in data['rows']:
                spot_name = spot.get('NAME', '未知景点')
                safe_name = spot_name.replace('/', '_').replace('\\', '_')
                spot_path = f"tourist_data/{now.strftime('%Y/%m/')}{safe_name}.jsonl"
                spot_record = json.dumps({
                    'timestamp': now.isoformat(),
                    'spot': spot
                }, ensure_ascii=False) + '\n'
                
                if not self.append_to_oss(spot_path, spot_record):
                    spot_success = False
        
        return daily_success and spot_success
    
    def run(self):
        print("开始爬取数据...")
        
        data = self.fetch_data()
        if not data:
            return False
        
        success = self.upload_data(data)
        
        if success:
            now = datetime.now()
            print("数据上传成功！")
            print(f"- 按日期存储：tourist_data/{now.strftime('%Y/%m/%d')}.jsonl")
            print(f"- 按景点存储：tourist_data/{now.strftime('%Y/%m/')}<景点名>.jsonl")
            print("- 使用追加写入，节省OSS费用")
        else:
            print("数据上传失败")
        
        return success

def main():
    try:
        crawler = TouristCrawler()
        success = crawler.run()
        exit(0 if success else 1)
    except Exception as e:
        print(f"程序运行失败: {e}")
        exit(1)

if __name__ == '__main__':
    main()
