#!/usr/bin/env python3
"""OSS历史数据迁移脚本 - 将旧数据结构迁移到新结构"""

import os
import oss2
import json
from datetime import datetime
from collections import defaultdict

# 配置
OSS_ACCESS_KEY_ID = os.getenv('OSS_ACCESS_KEY_ID')
OSS_ACCESS_KEY_SECRET = os.getenv('OSS_ACCESS_KEY_SECRET')
OSS_ENDPOINT = os.getenv('OSS_ENDPOINT', 'oss-cn-shanghai.aliyuncs.com')
OSS_BUCKET_NAME = os.getenv('OSS_BUCKET_NAME', 'shanghai-tourist-traffic')

class OSSDataMigrator:
    def __init__(self, dry_run=True):
        """
        初始化迁移器

        Args:
            dry_run: 如果为True，只打印操作不实际执行
        """
        if not all([OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET, OSS_BUCKET_NAME]):
            raise ValueError("缺少必要的OSS配置项")

        auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
        self.bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)
        self.dry_run = dry_run

    def list_old_data_files(self, prefix='tourist_data/'):
        """列出所有旧的数据文件"""
        print(f"\n正在扫描 {prefix} 下的文件...")
        files = []

        for obj in oss2.ObjectIterator(self.bucket, prefix=prefix):
            # 跳过已经是新格式的文件 (YYYY/MM/DD.jsonl 或 YYYY/MM/景点名.jsonl)
            path_parts = obj.key.replace(prefix, '').split('/')

            # 新格式: tourist_data/2025/11/20.jsonl 或 tourist_data/2025/11/景点名.jsonl
            if len(path_parts) == 3 and path_parts[0].isdigit() and path_parts[1].isdigit():
                print(f"  跳过（已是新格式）: {obj.key}")
                continue

            files.append(obj.key)
            print(f"  发现旧文件: {obj.key}")

        return files

    def parse_old_file(self, file_path):
        """读取并解析旧文件内容"""
        try:
            print(f"\n读取文件: {file_path}")
            result = self.bucket.get_object(file_path)
            content = result.read().decode('utf-8')

            records = []

            # 尝试解析为单个JSON对象（旧格式）
            try:
                data = json.loads(content)

                # 处理 by_date 格式：包含 date、last_updated、data 字段
                if 'data' in data and isinstance(data['data'], list):
                    # by_date 格式
                    if 'date' in data:
                        for item in data['data']:
                            if 'fetch_time' in item:
                                # 转换为新格式
                                records.append({
                                    'timestamp': item['fetch_time'],
                                    'data': item
                                })
                    # by_name 格式：包含 spot_name、month、data 字段
                    elif 'spot_name' in data:
                        spot_name = data['spot_name']
                        for item in data['data']:
                            # 使用 TIME 字段作为时间戳
                            time_str = item.get('TIME', '')
                            if time_str:
                                # 转换时间格式：2025-11-07 15:42 -> 2025-11-07T15:42:00
                                try:
                                    timestamp = datetime.strptime(time_str, '%Y-%m-%d %H:%M').isoformat()
                                except:
                                    timestamp = time_str

                                records.append({
                                    'timestamp': timestamp,
                                    'spot': item
                                })
                # 处理其他格式
                elif isinstance(data, dict) and 'records' in data:
                    records = data['records']
                elif isinstance(data, list):
                    records = data
                else:
                    # 直接使用这个数据对象
                    records = [data]

                print(f"  成功解析 {len(records)} 条记录")
                return records
            except json.JSONDecodeError:
                # 如果不是单个JSON，尝试按行解析（JSONL格式）
                for line_num, line in enumerate(content.strip().split('\n'), 1):
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                        records.append(record)
                    except json.JSONDecodeError as e:
                        print(f"  警告: 第 {line_num} 行JSON解析失败: {e}")
                        continue

                print(f"  成功解析 {len(records)} 条记录")
                return records

        except Exception as e:
            print(f"  错误: 读取文件失败 - {e}")
            return []

    def group_records_by_date_and_spot(self, records):
        """
        将记录按日期和景点分组

        Returns:
            daily_groups: {(year, month, day): [records]}
            spot_groups: {(year, month, spot_name): [records]}
        """
        daily_groups = defaultdict(list)
        spot_groups = defaultdict(list)

        for record in records:
            # 解析时间戳
            timestamp_str = record.get('timestamp', '')
            if not timestamp_str:
                print(f"  警告: 记录缺少timestamp，跳过")
                continue

            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except Exception as e:
                print(f"  警告: 时间戳解析失败 ({timestamp_str}): {e}")
                continue

            year = timestamp.strftime('%Y')
            month = timestamp.strftime('%m')
            day = timestamp.strftime('%d')

            # 按日期分组
            daily_key = (year, month, day)
            daily_groups[daily_key].append(record)

            # 按景点分组
            data = record.get('data', {})
            if 'rows' in data:
                for spot in data['rows']:
                    spot_name = spot.get('NAME', '未知景点')
                    safe_name = spot_name.replace('/', '_').replace('\\', '_')
                    spot_key = (year, month, safe_name)

                    spot_record = {
                        'timestamp': timestamp_str,
                        'spot': spot
                    }
                    spot_groups[spot_key].append(spot_record)
            elif 'spot' in record:
                # 如果记录本身就是景点数据
                spot = record.get('spot', {})
                spot_name = spot.get('NAME', '未知景点')
                safe_name = spot_name.replace('/', '_').replace('\\', '_')
                spot_key = (year, month, safe_name)
                spot_groups[spot_key].append(record)

        return daily_groups, spot_groups

    def write_to_new_path(self, path, records):
        """将记录写入新路径（追加模式）"""
        if not records:
            return True

        content = '\n'.join(json.dumps(r, ensure_ascii=False) for r in records) + '\n'

        if self.dry_run:
            print(f"  [DRY RUN] 将写入 {len(records)} 条记录到: {path}")
            return True

        try:
            if self.bucket.object_exists(path):
                # 追加到已有文件
                head_result = self.bucket.head_object(path)
                position = head_result.content_length
                result = self.bucket.append_object(path, position, content.encode('utf-8'))
            else:
                # 创建新文件
                result = self.bucket.append_object(path, 0, content.encode('utf-8'))

            if result.status == 200:
                print(f"  ✓ 成功写入 {len(records)} 条记录到: {path}")
                return True
            else:
                print(f"  ✗ 写入失败 (status {result.status}): {path}")
                return False
        except Exception as e:
            print(f"  ✗ 写入失败: {path} - {e}")
            return False

    def backup_old_file(self, old_path):
        """备份旧文件到 _backup 目录"""
        backup_path = old_path.replace('tourist_data/', 'tourist_data/_backup/')

        if self.dry_run:
            print(f"  [DRY RUN] 将备份: {old_path} -> {backup_path}")
            return True

        try:
            self.bucket.copy_object(OSS_BUCKET_NAME, old_path, backup_path)
            print(f"  ✓ 备份成功: {backup_path}")
            return True
        except Exception as e:
            print(f"  ✗ 备份失败: {e}")
            return False

    def delete_old_file(self, old_path):
        """删除旧文件"""
        if self.dry_run:
            print(f"  [DRY RUN] 将删除: {old_path}")
            return True

        try:
            self.bucket.delete_object(old_path)
            print(f"  ✓ 删除成功: {old_path}")
            return True
        except Exception as e:
            print(f"  ✗ 删除失败: {e}")
            return False

    def migrate_file(self, old_file_path):
        """迁移单个文件"""
        print(f"\n{'='*60}")
        print(f"开始迁移: {old_file_path}")
        print('='*60)

        # 1. 读取旧文件
        records = self.parse_old_file(old_file_path)
        if not records:
            print("没有有效记录，跳过")
            return False

        # 2. 按日期和景点分组
        print("\n分组记录...")
        daily_groups, spot_groups = self.group_records_by_date_and_spot(records)
        print(f"  日期分组: {len(daily_groups)} 个")
        print(f"  景点分组: {len(spot_groups)} 个")

        # 3. 写入按日期分组的数据
        print("\n写入按日期分组的数据...")
        daily_success = True
        for (year, month, day), day_records in sorted(daily_groups.items()):
            new_path = f"tourist_data/{year}/{month}/{day}.jsonl"
            if not self.write_to_new_path(new_path, day_records):
                daily_success = False

        # 4. 写入按景点分组的数据
        print("\n写入按景点分组的数据...")
        spot_success = True
        for (year, month, spot_name), spot_records in sorted(spot_groups.items()):
            new_path = f"tourist_data/{year}/{month}/{spot_name}.jsonl"
            if not self.write_to_new_path(new_path, spot_records):
                spot_success = False

        # 5. 如果成功，备份并删除旧文件
        if daily_success and spot_success:
            print("\n处理旧文件...")
            if self.backup_old_file(old_file_path):
                self.delete_old_file(old_file_path)
            return True
        else:
            print("\n迁移失败，保留旧文件")
            return False

    def run(self):
        """执行迁移"""
        print("="*60)
        print("OSS数据迁移工具")
        print("="*60)
        print(f"模式: {'DRY RUN（仅预览）' if self.dry_run else '实际执行'}")
        print()

        # 列出所有旧文件
        old_files = self.list_old_data_files()

        if not old_files:
            print("\n没有发现需要迁移的旧文件")
            return

        print(f"\n共发现 {len(old_files)} 个需要迁移的文件")

        if self.dry_run:
            print("\n这是预览模式，不会实际修改数据")
            print("如需执行迁移，请使用: --execute 参数")

        # 确认
        if not self.dry_run:
            print("\n警告：即将开始迁移数据！")
            response = input("确认继续？(yes/no): ")
            if response.lower() != 'yes':
                print("已取消")
                return

        # 迁移每个文件
        success_count = 0
        fail_count = 0

        for old_file in old_files:
            if self.migrate_file(old_file):
                success_count += 1
            else:
                fail_count += 1

        # 总结
        print("\n" + "="*60)
        print("迁移完成")
        print("="*60)
        print(f"成功: {success_count}")
        print(f"失败: {fail_count}")
        print(f"总计: {len(old_files)}")

def main():
    import argparse

    parser = argparse.ArgumentParser(description='OSS数据迁移工具')
    parser.add_argument('--execute', action='store_true',
                       help='实际执行迁移（默认为预览模式）')
    parser.add_argument('--prefix', default='tourist_data/',
                       help='OSS路径前缀（默认: tourist_data/）')

    args = parser.parse_args()

    try:
        migrator = OSSDataMigrator(dry_run=not args.execute)
        migrator.run()
    except Exception as e:
        print(f"\n错误: {e}")
        exit(1)

if __name__ == '__main__':
    main()
