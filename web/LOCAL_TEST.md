# 本地测试指南

## 问题修复

已修复数据结构访问问题。数据格式是：
```json
{
  "data": {
    "data": [
      {
        "rows": [
          { "CODE": "xxx", "NAME": "景点名" }
        ]
      }
    ]
  }
}
```

代码现在正确使用 `flatMap` 提取所有景点数据。

## 快速开始

### 1. 确保已有数据文件

检查数据是否存在：
```bash
ls -lh web/public/data/
ls web/public/data/spots/ | head -10
```

如果没有数据，运行获取脚本：
```bash
cd web
python fetch_data.py
```

### 2. 安装依赖

```bash
cd web
npm install
```

### 3. 启动开发服务器

```bash
npm run dev
```

### 4. 访问网站

打开浏览器访问：http://localhost:5173

你应该能看到：
- ✅ 日期选择器（显示最近的日期）
- ✅ 统计卡片（总景点数、开放景点、总游客数等）
- ✅ 图表（各区游客分布、热门景点TOP10）
- ✅ 景点列表卡片

## 浏览器调试

如果还是没有数据，打开浏览器开发者工具（F12）：

### 检查网络请求
1. 打开 Network 标签
2. 刷新页面
3. 查看是否成功加载了 JSON 文件
4. 检查响应内容

### 检查控制台
1. 打开 Console 标签
2. 查看是否有错误信息
3. 如果看到 "Failed to load data for YYYY-MM-DD"，说明对应日期的文件不存在

## 常见问题

### Q1: 显示"暂无数据"
**原因**：`public/data/` 目录中没有最近5天的数据文件

**解决**：
```bash
cd web
python fetch_data.py
```

### Q2: 图表不显示
**原因**：数据结构解析错误或没有开放的景点

**解决**：
- 检查浏览器控制台是否有错误
- 确认至少有一个日期的数据文件存在

### Q3: 点击景点后详情页显示"未找到该景点数据"
**原因**：`public/data/spots/` 目录中缺少对应景点的JSON文件

**解决**：
```bash
cd web
python fetch_data.py  # 这会下载所有景点数据
```

### Q4: Python脚本报错 "缺少必要的OSS配置项"
**原因**：未设置环境变量

**解决**：
```bash
export OSS_ACCESS_KEY_ID=your_key_id
export OSS_ACCESS_KEY_SECRET=your_key_secret
export OSS_ENDPOINT=oss-cn-beijing.aliyuncs.com
export OSS_BUCKET_NAME=your_bucket_name
```

或者在项目根目录创建 `.env` 文件（注意不是 web/.env）：
```bash
OSS_ACCESS_KEY_ID=your_key_id
OSS_ACCESS_KEY_SECRET=your_key_secret
OSS_ENDPOINT=oss-cn-beijing.aliyuncs.com
OSS_BUCKET_NAME=your_bucket_name
```

## 数据检查命令

```bash
# 检查有哪些日期的数据
ls web/public/data/*.json

# 检查数据文件大小
du -h web/public/data/*.json

# 查看数据文件的前几行
head -30 web/public/data/2025-11-07.json

# 统计景点数据文件数量
ls web/public/data/spots/ | wc -l

# 测试JSON格式是否正确
python -m json.tool web/public/data/2025-11-07.json > /dev/null && echo "✓ JSON格式正确"
```

## 验证步骤

1. ✅ 数据文件存在：`ls web/public/data/`
2. ✅ npm 依赖已安装：`ls web/node_modules/`
3. ✅ 开发服务器运行：`npm run dev`
4. ✅ 浏览器能访问：http://localhost:5173
5. ✅ 页面显示数据：检查统计卡片有数字
6. ✅ 图表显示：两个图表都有内容
7. ✅ 景点列表：下方有景点卡片
8. ✅ 详情页：点击任意景点能进入详情页

## 重新开始（清理环境）

如果问题无法解决，可以完全重新开始：

```bash
# 1. 清理数据
rm -rf web/public/data/*.json
rm -rf web/public/data/spots/*

# 2. 清理node_modules
rm -rf web/node_modules

# 3. 重新安装
cd web
npm install

# 4. 重新获取数据
python fetch_data.py

# 5. 启动服务
npm run dev
```

## 成功标志

页面加载后应该看到类似：
- 总景点数：100+
- 开放景点：XX
- 总游客数：XXXXX
- 两个图表显示数据
- 滚动下方看到景点卡片网格

如果看到以上内容，说明本地测试成功！🎉
