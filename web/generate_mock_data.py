import os
import json
import random
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
SPOTS_DIR = os.path.join(DATA_DIR, 'spots')

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
if not os.path.exists(SPOTS_DIR):
    os.makedirs(SPOTS_DIR)

def generate_mock_data():
    print("Generating mock data (v2)...")
    
    spots = [
        "上海迪士尼乐园", "东方明珠广播电视塔", "上海野生动物园", "上海科技馆", 
        "豫园", "上海海昌海洋公园", "上海中心大厦", "金茂大厦88层观光厅",
        "上海欢乐谷", "朱家角古镇", "上海M50创意园", "田子坊",
        "上海博物馆", "上海自然博物馆", "上海天文馆", "共青森林公园"
    ]
    
    districts = ["浦东新区", "黄浦区", "松江区", "青浦区", "普陀区", "静安区", "杨浦区"]
    
    # 1. Generate Time Buckets
    time_buckets = []
    start_time = datetime.strptime("09:00", "%H:%M")
    end_time = datetime.strptime("21:00", "%H:%M")
    current = start_time
    while current <= end_time:
        time_buckets.append(current.strftime("%H:%M"))
        current += timedelta(minutes=30)
        
    # 2. Generate Trend Series (5 days)
    trend_series = []
    today = datetime.now()
    
    for i in range(4, -1, -1):
        date = today - timedelta(days=i)
        short_date = date.strftime('%m-%d')
        
        # Generate a curve: bell curve peaking around 14:00
        daily_data = []
        base_traffic = random.randint(50000, 80000) # Total city traffic base
        
        for t_str in time_buckets:
            t_obj = datetime.strptime(t_str, "%H:%M")
            hour = t_obj.hour + t_obj.minute / 60.0
            
            # Factor: 0 at 9:00, 1 at 14:00, 0.2 at 21:00
            if hour < 14:
                factor = (hour - 9) / 5
            else:
                factor = 1 - (hour - 14) / 8
            
            factor = max(0.1, factor)
            val = int(base_traffic * factor * (0.8 + random.random() * 0.4))
            daily_data.append(val)
            
        trend_series.append({
            "name": short_date,
            "type": "line",
            "smooth": True,
            "data": daily_data
        })

    # 3. Generate Spot Data & Stats
    all_spots_list = []
    spot_stats = {}
    
    for i, name in enumerate(spots):
        district = districts[i % len(districts)]
        max_capacity = random.randint(10000, 80000)
        
        # Simulate 5-day stats
        daily_peaks = []
        for _ in range(5):
            peak = random.randint(int(max_capacity * 0.2), int(max_capacity * 0.9))
            daily_peaks.append(peak)
            
        sum_peak = sum(daily_peaks)
        max_peak = max(daily_peaks)
        current_num = int(daily_peaks[-1] * (0.5 + random.random() * 0.5)) # Current is some fraction of peak
        
        spot_info = {
            "CODE": str(100 + i),
            "NAME": name,
            "DES": "",
            "TIME": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "GRADE": "5A" if i < 8 else "4A",
            "T_TIME": "09:00~21:00",
            "MAX_NUM": max_capacity,
            "SSD": "舒适" if current_num < max_capacity * 0.8 else "拥挤",
            "NUM": current_num,
            "TYPE": "开放",
            "DISTRICT": str(i),
            "DNAME": district,
            "SUM_PEAK": sum_peak,
            "MAX_PEAK": max_peak
        }
        all_spots_list.append(spot_info)
        
        # Generate detail file for each spot
        detail_data = []
        base_time = datetime.now() - timedelta(days=30)
        for day in range(30):
            for hour in range(9, 21):
                time_str = (base_time + timedelta(days=day, hours=hour)).strftime("%Y-%m-%d %H:%M")
                hour_factor = 1 - abs(hour - 14) / 7
                num = int(max_peak * hour_factor * (0.8 + random.random() * 0.4))
                if num < 0: num = 0
                
                detail_data.append({
                    "CODE": str(100 + i),
                    "NAME": name,
                    "TIME": time_str,
                    "GRADE": spot_info['GRADE'],
                    "MAX_NUM": max_capacity,
                    "SSD": "舒适",
                    "NUM": num,
                    "DNAME": district
                })
        
        safe_name = name.replace('/', '_').replace('\\', '_')
        with open(os.path.join(SPOTS_DIR, f"{safe_name}.json"), 'w', encoding='utf-8') as f:
            json.dump({
                "name": name,
                "data": detail_data
            }, f, ensure_ascii=False, indent=2)

    # 4. Generate Top 10
    top_10 = sorted(all_spots_list, key=lambda x: x['SUM_PEAK'], reverse=True)[:10]
    
    # 5. Generate Treemap Data
    treemap_data = []
    for spot in all_spots_list:
        treemap_data.append({
            "name": spot['NAME'],
            "value": spot['MAX_PEAK']
        })

    # Save overview.json
    final_overview = {
        "generated_at": datetime.now().isoformat(),
        "time_buckets": time_buckets,
        "trend_series": trend_series,
        "top_10": top_10,
        "treemap_data": treemap_data,
        "all_spots": sorted(all_spots_list, key=lambda x: x['NUM'], reverse=True)
    }
    
    with open(os.path.join(DATA_DIR, 'overview.json'), 'w', encoding='utf-8') as f:
        json.dump(final_overview, f, ensure_ascii=False, indent=2)
        
    print("Mock data (v2) generated successfully!")

if __name__ == "__main__":
    generate_mock_data()
