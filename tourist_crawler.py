#!/usr/bin/env python3
"""
上海旅游景点实时数据爬取器 - 简化版
支持按日期和按景点名称两种存储方式，数据追加到阿里云OSS
"""

import os
import requests
import json
import oss2
from datetime import datetime
from typing import Dict, List, Optional

# 配置
OSS_ACCESS_KEY_ID = os.getenv('OSS_ACCESS_KEY_ID')
OSS_ACCESS_KEY_SECRET = os.getenv('OSS_ACCESS_KEY_SECRET')
OSS_ENDPOINT = os.getenv('OSS_ENDPOINT', 'oss-cn-shanghai.aliyuncs.com')
OSS_BUCKET_NAME = "shanghai-tourist-traffic"

DATA_BY_DATE_PREFIX = 'tourist_data/by_date/'
DATA_BY_NAME_PREFIX = 'tourist_data/by_name/'
API_URL = 'https://tourist.whlyj.sh.gov.cn/api/statistics/getViewTourist'
REQUEST_TIMEOUT = 30

class TouristCrawler:
    """上海旅游景点数据爬取器"""
    
    def __init__(self):
        # 验证配置
        if not all([OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET, OSS_BUCKET_NAME]):
            raise ValueError("缺少必要的OSS配置项")
        
        # 初始化OSS客户端
        auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
        self.bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)
        
        # 设置请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://tourist.whlyj.sh.gov.cn/'
        }
    
    def fetch_data(self) -> Optional[Dict]:
        """获取旅游景点数据"""
        try:
            print(f"开始获取数据: {API_URL}")
            
            response = requests.get(API_URL, headers=self.headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('code') != 200:
                print(f"API返回错误: {data.get('msg', '未知错误')}")
                return None
            
            # 添加获取时间戳
            data['fetch_time'] = datetime.now().isoformat()
            
            print(f"成功获取数据，共 {data.get('total', 0)} 条记录")
            return data
            
        except Exception as e:
            print(f"获取数据失败: {e}")
            return None
    
    def get_existing_data(self, object_key: str) -> List[Dict]:
        """获取OSS中已存在的数据"""
        try:
            if not self.bucket.object_exists(object_key):
                return []
            
            result = self.bucket.get_object(object_key)
            content = result.read().decode('utf-8')
            existing_data = json.loads(content)
            
            if isinstance(existing_data, list):
                return existing_data
            elif isinstance(existing_data, dict) and 'data' in existing_data:
                return existing_data['data']
            else:
                return [existing_data]
                
        except Exception as e:
            print(f"获取已存在数据失败: {e}")
            return []
    
    def upload_data(self, object_key: str, data: Dict) -> bool:
        """上传数据到OSS"""
        try:
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            result = self.bucket.put_object(object_key, json_data.encode('utf-8'))
            
            if result.status == 200:
                print(f"数据上传成功: {object_key}")
                return True
            else:
                print(f"数据上传失败: {object_key}, 状态码: {result.status}")
                return False
                
        except Exception as e:
            print(f"上传数据失败: {e}")
            return False
    
    def upload_by_date(self, data: Dict) -> bool:
        """按日期存储数据"""
        try:
            current_date = datetime.now().strftime('%Y/%m/%d')
            object_key = f"{DATA_BY_DATE_PREFIX}{current_date}/tourist_data.json"
            
            existing_data = self.get_existing_data(object_key)
            existing_data.append(data)
            
            complete_data = {
                'date': current_date,
                'last_updated': datetime.now().isoformat(),
                'total_records': len(existing_data),
                'data': existing_data
            }
            
            return self.upload_data(object_key, complete_data)
            
        except Exception as e:
            print(f"按日期存储数据失败: {e}")
            return False
    
    def sanitize_filename(self, filename: str) -> str:
        """清理文件名中的特殊字符"""
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename.strip() or 'unknown'
    
    def upload_by_name(self, tourist_spots: List[Dict]) -> bool:
        """按景点名称存储数据"""
        success_count = 0
        
        for spot in tourist_spots:
            try:
                spot_name = spot.get('NAME', '未知景点')
                safe_name = self.sanitize_filename(spot_name)
                object_key = f"{DATA_BY_NAME_PREFIX}{safe_name}/data.json"
                
                existing_data = self.get_existing_data(object_key)
                existing_data.append(spot)
                
                complete_data = {
                    'spot_name': spot_name,
                    'spot_code': spot.get('CODE'),
                    'district': spot.get('DNAME'),
                    'last_updated': datetime.now().isoformat(),
                    'total_records': len(existing_data),
                    'data': existing_data
                }
                
                if self.upload_data(object_key, complete_data):
                    success_count += 1
                    
            except Exception as e:
                print(f"存储景点 {spot.get('NAME', '未知')} 数据失败: {e}")
        
        print(f"按名称存储完成: {success_count}/{len(tourist_spots)} 个景点成功")
        return success_count == len(tourist_spots)
    
    def run(self) -> bool:
        """执行完整的爬取和上传流程"""
        print("=" * 50)
        print("开始执行数据爬取任务")
        
        # 获取数据
        data = self.fetch_data()
        if not data:
            print("获取数据失败")
            return False
        
        # 按日期存储
        date_success = self.upload_by_date(data)
        
        # 按名称存储
        name_success = False
        if 'rows' in data and data['rows']:
            name_success = self.upload_by_name(data['rows'])
        else:
            print("没有景点数据可按名称存储")
        
        # 检查结果
        if date_success and name_success:
            print("数据上传完成，所有存储方式都成功")
            success = True
        else:
            print(f"数据上传部分失败 - 按日期: {date_success}, 按名称: {name_success}")
            success = False
        
        print("数据爬取任务完成")
        print("=" * 50)
        
        return success

def main():
    """主函数"""
    try:
        crawler = TouristCrawler()
        success = crawler.run()
        exit(0 if success else 1)
    except Exception as e:
        print(f"程序运行失败: {e}")
        exit(1)

if __name__ == '__main__':
    main()
