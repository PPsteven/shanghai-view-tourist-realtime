# 上海旅游景点实时数据可视化网站

这是一个静态网站项目，用于展示上海旅游景点的实时数据，包括游客数量、舒适度、开放状态等信息。

## 技术栈

- **React 18** - UI框架
- **Vite** - 构建工具
- **ECharts** - 数据可视化
- **React Router** - 路由管理
- **阿里云OSS** - 数据存储

## 功能特性

### 首页
- 展示最近5天的景点数据
- 按区域统计游客分布
- 热门景点TOP10排行
- 景点列表，支持按开放状态筛选
- 点击景点可查看详细信息

### 景点详情页
- 游客数量变化趋势图
- 舒适度分布饼图
- 容量利用率趋势
- 当前状态展示
- 天气信息
- 历史数据记录表格

## 项目结构

```
web/
├── public/              # 静态资源
│   └── data/           # 数据文件（由GitHub Actions生成）
│       ├── *.json      # 日期数据文件
│       └── spots/      # 景点数据目录
├── src/
│   ├── components/     # 组件
│   ├── pages/          # 页面
│   │   ├── HomePage.jsx        # 首页
│   │   └── SpotDetailPage.jsx  # 景点详情页
│   ├── utils/          # 工具函数
│   ├── App.jsx         # 主应用
│   ├── App.css
│   ├── main.jsx        # 入口文件
│   └── index.css
├── fetch_data.py       # OSS数据获取脚本
├── package.json
├── vite.config.js
└── index.html
```

## 本地开发

### 1. 安装依赖

```bash
cd web
npm install
```

### 2. 获取数据

确保环境变量已配置：

```bash
export OSS_ACCESS_KEY_ID=your_key_id
export OSS_ACCESS_KEY_SECRET=your_key_secret
export OSS_ENDPOINT=oss-cn-beijing.aliyuncs.com
export OSS_BUCKET_NAME=your_bucket_name
```

运行数据获取脚本：

```bash
python fetch_data.py
```

这将从OSS下载最近5天的数据和所有景点的历史数据到 `public/data/` 目录。

### 3. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:5173

### 4. 构建生产版本

```bash
npm run build
```

构建后的文件在 `dist/` 目录。

## GitHub Actions 自动部署

项目配置了GitHub Actions工作流，每天早上8点自动执行以下任务：

1. 从阿里云OSS获取最新数据
2. 构建React应用
3. 部署到GitHub Pages

### 配置步骤

1. **启用GitHub Pages**
   - 进入仓库 Settings > Pages
   - Source 选择 "GitHub Actions"

2. **配置Secrets**

   在仓库 Settings > Secrets and variables > Actions 中添加以下secrets：

   - `OSS_ACCESS_KEY_ID` - 阿里云OSS访问密钥ID
   - `OSS_ACCESS_KEY_SECRET` - 阿里云OSS访问密钥Secret
   - `OSS_ENDPOINT` - OSS端点（如：oss-cn-beijing.aliyuncs.com）
   - `OSS_BUCKET_NAME` - OSS存储桶名称

3. **手动触发（可选）**

   在 Actions 标签页中，可以手动触发 "Deploy Website to GitHub Pages" 工作流。

## 数据格式

### 日期数据格式 (YYYY-MM-DD.json)

```json
{
  "date": "2025/11/06",
  "last_updated": "2025-11-06T23:54:58.725525",
  "total_records": 22,
  "data": [
    {
      "total": "160",
      "rows": [
        {
          "CODE": "474",
          "NAME": "景点名称",
          "DISTRICT": "1",
          "DNAME": "黄浦区",
          "GRADE": "5A",
          "NUM": 0,
          "MAX_NUM": 2775,
          "TYPE": "闭园",
          "SSD": "舒适",
          "TIME": "2025-11-07 03:24",
          "T_TIME": "09:00~16:30",
          ...
        }
      ]
    }
  ]
}
```

### 景点数据格式 (spots/CODE.json)

```json
{
  "spot_name": "上海国际旅游度假区",
  "spot_code": "102",
  "district": "浦东新区",
  "last_updated": "2025-11-07T05:47:01.274970",
  "total_records": 32,
  "data": [
    {
      "CODE": "102",
      "NAME": "上海国际旅游度假区",
      "NUM": 765,
      "MAX_NUM": 140650,
      "SSD": "舒适",
      "TYPE": "正常",
      "TIME": "2025-11-07 03:25",
      ...
    }
  ]
}
```

## 数据来源

数据通过 `tourist_crawler.py` 爬虫脚本定期从上海文旅局官网获取，存储在阿里云OSS上。

- API源: https://tourist.whlyj.sh.gov.cn/api/statistics/getViewTourist
- 数据更新频率: 每15分钟
- OSS存储结构:
  - 按日期: `tourist_data/by_date/YYYY/MM/DD/data.json`
  - 按景点: `tourist_data/by_name/{景点名称}/data.json`

## 许可证

MIT
