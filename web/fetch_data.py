#!/usr/bin/env python3
"""
从阿里云OSS下载数据到本地web项目
用于GitHub Actions构建静态网站
"""

import os
import json
import oss2
from datetime import datetime, timedelta
from pathlib import Path

# OSS配置 - 从环境变量获取
OSS_ACCESS_KEY_ID = os.getenv('OSS_ACCESS_KEY_ID')
OSS_ACCESS_KEY_SECRET = os.getenv('OSS_ACCESS_KEY_SECRET')
OSS_ENDPOINT = os.getenv('OSS_ENDPOINT', 'oss-cn-shanghai.aliyuncs.com')
OSS_BUCKET_NAME = os.getenv('OSS_BUCKET_NAME', 'shanghai-tourist-traffic')

DATA_BY_DATE_PREFIX = 'tourist_data/by_date/'
DATA_BY_NAME_PREFIX = 'tourist_data/by_name/'

class DataFetcher:
    """从OSS获取数据"""

    def __init__(self, output_dir='public/data'):
        if not all([OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET, OSS_BUCKET_NAME]):
            raise ValueError("缺少必要的OSS配置项")

        # 初始化OSS客户端
        auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
        self.bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)

        # 输出目录
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 景点数据目录
        self.spots_dir = self.output_dir / 'spots'
        self.spots_dir.mkdir(exist_ok=True)

    def fetch_last_n_days(self, n=5):
        """获取最近n天的数据"""
        print(f"开始获取最近 {n} 天的数据...")

        success_count = 0
        for i in range(n):
            date = datetime.now() - timedelta(days=i)
            date_str = date.strftime('%Y/%m/%d')
            file_date_str = date.strftime('%Y-%m-%d')

            object_key = f"{DATA_BY_DATE_PREFIX}{date_str}/data.json"
            output_file = self.output_dir / f"{file_date_str}.json"

            try:
                if self.bucket.object_exists(object_key):
                    result = self.bucket.get_object(object_key)
                    content = result.read().decode('utf-8')

                    # 保存到本地
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(content)

                    print(f"✓ 已下载: {file_date_str}")
                    success_count += 1
                else:
                    print(f"✗ 文件不存在: {date_str}")
            except Exception as e:
                print(f"✗ 下载失败 {date_str}: {e}")

        print(f"日期数据下载完成: {success_count}/{n}")
        return success_count > 0

    def get_all_spot_codes(self):
        """从最近的日期数据中获取所有景点代码"""
        print("获取景点列表...")

        spot_codes = set()

        # 尝试读取最近几天的数据获取景点列表
        for i in range(5):
            date = datetime.now() - timedelta(days=i)
            file_date_str = date.strftime('%Y-%m-%d')
            data_file = self.output_dir / f"{file_date_str}.json"

            if data_file.exists():
                try:
                    with open(data_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    if 'data' in data:
                        for record in data['data']:
                            if 'rows' in record:
                                for spot in record['rows']:
                                    if spot.get('CODE'):
                                        spot_codes.add(spot['CODE'])
                except Exception as e:
                    print(f"读取文件失败 {file_date_str}: {e}")

        print(f"找到 {len(spot_codes)} 个景点")
        return list(spot_codes)

    def fetch_spot_data(self, spot_code, spot_name=None):
        """获取单个景点的数据，支持按月份存储的新格式"""
        # 尝试多种可能的文件名格式
        possible_names = []

        if spot_name:
            # 清理景点名称
            safe_name = self.sanitize_filename(spot_name)
            possible_names.append(safe_name)

        # 也尝试用代码查找
        possible_names.append(spot_code)

        # 尝试获取最近几个月的数据
        months_to_try = []
        current_date = datetime.now()
        for i in range(3):  # 尝试最近3个月
            month_date = current_date.replace(day=1) - timedelta(days=i*30)
            month_str = month_date.strftime('%Y-%m')
            months_to_try.append(month_str)

        all_data = []
        found_any = False

        for name in possible_names:
            for month in months_to_try:
                object_key = f"{DATA_BY_NAME_PREFIX}{name}/{month}.json"

                try:
                    if self.bucket.object_exists(object_key):
                        result = self.bucket.get_object(object_key)
                        content = result.read().decode('utf-8')
                        month_data = json.loads(content)
                        
                        # 添加月份信息到数据中
                        month_data['month'] = month
                        all_data.append(month_data)
                        found_any = True
                        
                except Exception as e:
                    continue

        if found_any:
            # 合并所有月份的数据
            combined_data = {
                'spot_code': spot_code,
                'spot_name': spot_name,
                'last_updated': datetime.now().isoformat(),
                'months_data': all_data
            }
            
            # 保存到本地 - 使用景点代码作为文件名
            output_file = self.spots_dir / f"{spot_code}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(combined_data, f, ensure_ascii=False, indent=2)

            return True

        return False

    def fetch_all_spots(self):
        """获取所有景点的数据"""
        print("开始下载景点数据...")

        # 获取景点代码列表
        spot_codes = self.get_all_spot_codes()

        if not spot_codes:
            print("未找到任何景点代码")
            return False

        # 构建景点代码到名称的映射
        spot_map = {}
        for i in range(5):
            date = datetime.now() - timedelta(days=i)
            file_date_str = date.strftime('%Y-%m-%d')
            data_file = self.output_dir / f"{file_date_str}.json"

            if data_file.exists():
                try:
                    with open(data_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    if 'data' in data:
                        for record in data['data']:
                            if 'rows' in record:
                                for spot in record['rows']:
                                    code = spot.get('CODE')
                                    name = spot.get('NAME')
                                    if code and name:
                                        spot_map[code] = name
                except Exception as e:
                    pass

        # 下载每个景点的数据
        success_count = 0
        for spot_code in spot_codes:
            spot_name = spot_map.get(spot_code)
            if self.fetch_spot_data(spot_code, spot_name):
                print(f"✓ 已下载景点: {spot_code} - {spot_name or '未知'}")
                success_count += 1
            else:
                print(f"✗ 下载失败: {spot_code} - {spot_name or '未知'}")

        print(f"景点数据下载完成: {success_count}/{len(spot_codes)}")
        return success_count > 0

    def sanitize_filename(self, filename):
        """清理文件名中的特殊字符"""
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename.strip() or 'unknown'

    def run(self):
        """执行完整的数据获取流程"""
        print("=" * 50)
        print("开始从OSS下载数据")
        print("=" * 50)

        # 获取最近5天的数据
        dates_success = self.fetch_last_n_days(5)

        # 获取所有景点数据
        spots_success = self.fetch_all_spots()

        if dates_success and spots_success:
            print("\n" + "=" * 50)
            print("数据下载完成!")
            print("=" * 50)
            return True
        else:
            print("\n" + "=" * 50)
            print("数据下载部分失败")
            print("=" * 50)
            return False

def main():
    """主函数"""
    try:
        fetcher = DataFetcher()
        success = fetcher.run()
        exit(0 if success else 1)
    except Exception as e:
        print(f"程序运行失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == '__main__':
    main()
