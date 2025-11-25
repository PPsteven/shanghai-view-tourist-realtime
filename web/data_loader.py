import os
import json
import oss2
from datetime import datetime, timedelta
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 配置 OSS
OSS_ACCESS_KEY_ID = os.getenv('OSS_ACCESS_KEY_ID')
OSS_ACCESS_KEY_SECRET = os.getenv('OSS_ACCESS_KEY_SECRET')
OSS_ENDPOINT = os.getenv('OSS_ENDPOINT', 'oss-cn-shanghai.aliyuncs.com')
OSS_BUCKET_NAME = os.getenv('OSS_BUCKET_NAME', 'shanghai-tourist-traffic')

# 本地存储路径
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
SPOTS_DIR = os.path.join(DATA_DIR, 'spots')

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
if not os.path.exists(SPOTS_DIR):
    os.makedirs(SPOTS_DIR)

def get_bucket():
    if not all([OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET, OSS_BUCKET_NAME]):
        logging.error("缺少必要的OSS配置项 (OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET, OSS_BUCKET_NAME)")
        return None
    
    auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
    return oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)

def fetch_overview_jsonl_from_oss(bucket, object_key):
    """从OSS读取概览JSONL文件并返回解析后的景点列表（格式：data.rows）"""
    try:
        if not bucket.object_exists(object_key):
            logging.warning(f"文件不存在: {object_key}")
            return []
        
        obj = bucket.get_object(object_key)
        content = obj.read().decode('utf-8')
        lines = content.strip().split('\n')
        spots = []
        for line in lines:
            try:
                if line.strip():
                    record = json.loads(line)
                    # 概览数据结构：从 data.rows 中提取景点数据
                    if 'data' in record and 'rows' in record['data']:
                        spots.extend(record['data']['rows'])
            except json.JSONDecodeError:
                continue
        return spots
    except Exception as e:
        logging.error(f"读取概览文件失败 {object_key}: {e}")
        return []

def fetch_spot_detail_jsonl_from_oss(bucket, object_key):
    """从OSS读取景点详情JSONL文件并返回解析后的景点数据列表（格式：spot）"""
    try:
        if not bucket.object_exists(object_key):
            logging.warning(f"文件不存在: {object_key}")
            return []
        
        obj = bucket.get_object(object_key)
        content = obj.read().decode('utf-8')
        lines = content.strip().split('\n')
        spots = []
        for line in lines:
            try:
                if line.strip():
                    record = json.loads(line)
                    # 景点详情数据结构：从 spot 中提取景点数据
                    if 'spot' in record:
                        spots.append(record['spot'])
            except json.JSONDecodeError:
                continue
        return spots
    except Exception as e:
        logging.error(f"读取景点详情文件失败 {object_key}: {e}")
        return []

def process_overview_data(bucket):
    """处理最近5天的概览数据（包含趋势、Top10、Treemap）"""
    logging.info("开始处理概览数据...")
    
    today = datetime.now()
    # today = datetime(2025, 11, 20) # Debug
    
    # 1. 准备时间轴 buckets (09:00 - 23:00, 每30分钟)
    time_buckets = []
    start_time = datetime.strptime("09:00", "%H:%M")
    end_time = datetime.strptime("23:00", "%H:%M")
    current = start_time
    while current <= end_time:
        time_buckets.append(current.strftime("%H:%M"))
        current += timedelta(minutes=30)
    
    trend_series = []
    spot_stats = {} # {name: {max_num_5days: 0, district: "", latest_info: {}}}
    
    # 获取最近5天的数据
    for i in range(4, -1, -1):
        date = today - timedelta(days=i)
        date_str = date.strftime('%Y/%m/%d')
        short_date = date.strftime('%m-%d')
        object_key = f"tourist_data/{date_str}.jsonl"
        
        logging.info(f"正在获取: {object_key}")
        daily_records = fetch_overview_jsonl_from_oss(bucket, object_key)
        
        # --- 处理单日趋势 ---
        # 提取所有记录并按时间排序
        events = []
        for spot in daily_records:
            t_str = spot.get('TIME', '')
            # 尝试解析时间，格式可能是 "YYYY-MM-DD HH:mm" 或 "HH:mm"
            try:
                if len(t_str) > 10:
                    t_obj = datetime.strptime(t_str, "%Y-%m-%d %H:%M")
                else:
                    # 只有时间的情况，加上日期
                    t_obj = datetime.strptime(f"{date.strftime('%Y-%m-%d')} {t_str}", "%Y-%m-%d %H:%M")
                
                events.append({
                    'time': t_obj,
                    'name': spot.get('NAME'),
                    'num': int(spot.get('NUM', 0)),
                    'spot_data': spot
                })
            except Exception:
                continue
        
        events.sort(key=lambda x: x['time'])
        
        # 重放事件计算每个 bucket 的总人数
        daily_trend_data = []
        current_spot_nums = {} # {name: num}
        event_idx = 0
        
        # 记录当天的每个景点峰值
        daily_spot_peaks = {}
        
        for bucket_time_str in time_buckets:
            bucket_dt = datetime.strptime(f"{date.strftime('%Y-%m-%d')} {bucket_time_str}", "%Y-%m-%d %H:%M")
            
            # 处理所有早于等于当前 bucket 时间的事件
            while event_idx < len(events) and events[event_idx]['time'] <= bucket_dt:
                ev = events[event_idx]
                current_spot_nums[ev['name']] = ev['num']
                
                # 更新全局统计信息
                name = ev['name']
                if name not in spot_stats:
                    spot_stats[name] = {'max_num_5days': 0, 'district': ev['spot_data'].get('DNAME', '其他'), 'latest_info': ev['spot_data']}
                
                # 更新当天峰值
                daily_spot_peaks[name] = max(daily_spot_peaks.get(name, 0), ev['num'])
                
                # 更新最新信息（如果是最后一天）
                if i == 0:
                    spot_stats[name]['latest_info'] = ev['spot_data']
                
                event_idx += 1
            
            # 计算当前时刻总人数
            total_visitors = sum(current_spot_nums.values())
            daily_trend_data.append(total_visitors)
            
        trend_series.append({
            "name": short_date,
            "type": "line",
            "smooth": True,
            "data": daily_trend_data
        })
        
        # 更新全局峰值 (取5天中最大的那一天峰值? 还是累加? 用户说"客流峰值"，通常指最大承载压力，取Max)
        # 用户之前说"统计过去5天的客流峰值总和" (Top 10)
        # 用户后来又说"矩形树图...使用客流峰值替代"
        # 我们统一逻辑：
        # Top 10: 使用 5天峰值之和 (反映持续热度)
        # Treemap: 使用 5天内的最大峰值 (反映最大规模)
        
        for name, peak in daily_spot_peaks.items():
            if name in spot_stats:
                # 累加峰值用于 Top 10
                spot_stats[name]['sum_peak_5days'] = spot_stats[name].get('sum_peak_5days', 0) + peak
                # 最大峰值用于 Treemap
                spot_stats[name]['max_num_5days'] = max(spot_stats[name]['max_num_5days'], peak)

    # --- 生成 Top 10 数据 (按5天峰值总和) ---
    all_spots_list = []
    for name, stats in spot_stats.items():
        all_spots_list.append({
            "NAME": name,
            "SUM_PEAK": stats.get('sum_peak_5days', 0),
            "MAX_PEAK": stats['max_num_5days'],
            "DISTRICT": stats['district'],
            "LATEST": stats['latest_info']
        })
    
    top_10 = sorted(all_spots_list, key=lambda x: x['SUM_PEAK'], reverse=True)[:10]
    
    # --- 生成 Treemap 数据 ---
    # 结构: 直接展示所有景点 (Size = MAX_PEAK)
    treemap_data = []
    for spot in all_spots_list:
        treemap_data.append({
            "name": spot['NAME'],
            "value": spot['MAX_PEAK']
        })

    # 准备最终输出
    # 为了兼容之前的表格，all_spots 需要包含 LATEST 的信息，并补充统计数据
    final_all_spots = []
    for s in all_spots_list:
        info = s['LATEST'].copy()
        info['SUM_PEAK'] = s['SUM_PEAK']
        info['MAX_PEAK'] = s['MAX_PEAK']
        final_all_spots.append(info)

    final_overview = {
        "generated_at": today.isoformat(),
        "time_buckets": time_buckets,
        "trend_series": trend_series,
        "top_10": top_10,
        "treemap_data": treemap_data,
        "all_spots": sorted(final_all_spots, key=lambda x: int(x.get('NUM', 0)), reverse=True)
    }
    
    output_path = os.path.join(DATA_DIR, 'overview.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_overview, f, ensure_ascii=False, indent=2)
    
    logging.info(f"概览数据已保存至: {output_path}")
    return final_all_spots

def process_spot_details(bucket, all_spots):
    """处理每个景点的详细数据（最近1个月）"""
    logging.info("开始处理景点详情数据...")
    
    today = datetime.now()
    # 假设数据按月存储在 tourist_data/YYYY/MM/景点名.jsonl
    # 我们需要获取当前月的数据
    current_month_prefix = f"tourist_data/{today.strftime('%Y/%m')}/"
    
    # 注意：如果跨月，可能需要读取上个月的数据。
    # 为了简化，这里先只读取当前月份的文件夹。
    # 用户示例路径: /tourist_data/2025/11/上海M50创意园.jsonl
    
    for spot_info in all_spots:
        name = spot_info.get('NAME')
        if not name:
            continue
            
        # 处理文件名中的特殊字符 (参考 crawler 中的逻辑)
        safe_name = name.replace('/', '_').replace('\\', '_')
        object_key = f"{current_month_prefix}{safe_name}.jsonl"
        
        logging.info(f"处理景点: {name}")
        records = fetch_spot_detail_jsonl_from_oss(bucket, object_key)
        
        if not records:
            logging.info(f"  无数据: {object_key}")
            continue
            
        # 去重逻辑：按 TIME 字段去重
        unique_data = {}
        for spot_data in records:
            time_key = spot_data.get('TIME')
            if time_key:
                unique_data[time_key] = spot_data
        
        # 转换为列表并按时间排序
        sorted_data = sorted(unique_data.values(), key=lambda x: x.get('TIME', ''))
        
        # 保存
        output_path = os.path.join(SPOTS_DIR, f"{safe_name}.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                "name": name,
                "data": sorted_data
            }, f, ensure_ascii=False, indent=2)
            
    logging.info("所有景点详情处理完毕")

def main():
    bucket = get_bucket()
    if not bucket:
        return
    
    # 1. 生成概览数据
    all_spots = process_overview_data(bucket)
    
    # 2. 生成详情数据
    if all_spots:
        process_spot_details(bucket, all_spots)

if __name__ == '__main__':
    main()
