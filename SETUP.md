# 部署指南

本文档详细说明如何部署上海旅游景点数据采集系统和可视化网站。

## 目录

- [前置要求](#前置要求)
- [阿里云OSS配置](#阿里云oss配置)
- [GitHub配置](#github配置)
- [本地测试](#本地测试)
- [故障排查](#故障排查)

## 前置要求

### 必需项
- GitHub账号
- 阿里云账号（需要开通OSS服务）
- Git
- Python 3.9+
- Node.js 18+

### 可选项
- 一个域名（如果想自定义网站域名）

## 阿里云OSS配置

### 1. 创建OSS Bucket

1. 登录[阿里云OSS控制台](https://oss.console.aliyun.com/)
2. 点击"创建Bucket"
3. 填写配置：
   - Bucket名称：如 `shanghai-tourist-traffic`
   - 区域：建议选择 `华北2（北京）` 或 `华东2（上海）`
   - 存储类型：标准存储
   - 读写权限：私有（重要！）
   - 其他选项保持默认
4. 点击确定创建

### 2. 获取访问密钥

1. 访问[RAM访问控制](https://ram.console.aliyun.com/)
2. 点击左侧"用户" > "创建用户"
3. 填写用户名，勾选"编程访问"
4. 保存AccessKey ID和AccessKey Secret（只会显示一次！）

### 3. 授权OSS权限

1. 在RAM控制台，找到刚创建的用户
2. 点击"添加权限"
3. 选择 `AliyunOSSFullAccess` 或创建自定义策略：

```json
{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "oss:PutObject",
        "oss:GetObject",
        "oss:ListObjects"
      ],
      "Resource": [
        "acs:oss:*:*:shanghai-tourist-traffic/*"
      ]
    }
  ]
}
```

## GitHub配置

### 1. Fork或Clone仓库

```bash
git clone https://github.com/PPsteven/shanghai-view-tourist-realtime.git
cd shanghai-view-tourist-realtime
```

### 2. 配置GitHub Secrets

进入仓库的 Settings > Secrets and variables > Actions，添加以下secrets：

| Secret名称 | 值 | 说明 |
|-----------|-----|------|
| `OSS_ACCESS_KEY_ID` | 你的AccessKey ID | 从阿里云RAM获取 |
| `OSS_ACCESS_KEY_SECRET` | 你的AccessKey Secret | 从阿里云RAM获取 |
| `OSS_ENDPOINT` | `oss-cn-beijing.aliyuncs.com` | 根据你的bucket区域调整 |
| `OSS_BUCKET_NAME` | `shanghai-tourist-traffic` | 你的bucket名称 |

### 3. 启用GitHub Pages

1. 进入仓库的 Settings > Pages
2. Source 选择 "GitHub Actions"
3. 保存

### 4. 启用GitHub Actions

1. 进入仓库的 Actions 标签页
2. 如果看到提示，点击 "I understand my workflows, go ahead and enable them"
3. 你应该能看到两个工作流：
   - `Data Collection` - 数据采集（每10分钟）
   - `Deploy Website to GitHub Pages` - 网站部署（每天8点）

### 5. 手动触发首次运行

1. 点击 "Data Collection" 工作流
2. 点击 "Run workflow" 按钮
3. 等待工作流完成（约1-2分钟）
4. 点击 "Deploy Website to GitHub Pages" 工作流
5. 同样点击 "Run workflow"
6. 等待完成后，访问 `https://your-username.github.io/shanghai-view-tourist-realtime/`

## 本地测试

### 测试数据采集

```bash
# 1. 创建.env文件
cp .env.example .env

# 2. 编辑.env，填入你的OSS配置
vim .env

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行采集脚本
python tourist_crawler.py
```

成功后，你应该能在OSS控制台看到上传的数据文件。

### 测试前端网站

```bash
# 1. 进入web目录
cd web

# 2. 安装依赖
npm install

# 3. 设置环境变量
export OSS_ACCESS_KEY_ID=your_key_id
export OSS_ACCESS_KEY_SECRET=your_key_secret
export OSS_ENDPOINT=oss-cn-beijing.aliyuncs.com
export OSS_BUCKET_NAME=your_bucket_name

# 4. 从OSS获取数据
python fetch_data.py

# 5. 启动开发服务器
npm run dev
```

访问 http://localhost:5173 查看网站。

## 故障排查

### 数据采集失败

**问题**: GitHub Actions中数据采集工作流失败

**解决方案**:
1. 检查Secrets是否配置正确
2. 检查OSS Bucket是否存在且有权限
3. 查看Actions日志中的具体错误信息
4. 确认API接口是否可访问：`curl https://tourist.whlyj.sh.gov.cn/api/statistics/getViewTourist`

### 网站部署失败

**问题**: GitHub Actions中网站部署工作流失败

**解决方案**:
1. 确保GitHub Pages已启用且设置为 "GitHub Actions"
2. 检查是否有数据文件（需要先运行数据采集）
3. 查看Actions日志
4. 确认Node.js版本（需要18+）

### 网站无数据显示

**问题**: 网站能访问但显示"暂无数据"

**解决方案**:
1. 检查是否运行过数据采集
2. 在浏览器开发者工具中检查网络请求
3. 确认数据文件路径是否正确
4. 手动运行数据获取脚本测试：`cd web && python fetch_data.py`

### OSS访问被拒绝

**问题**: 上传或下载数据时提示权限不足

**解决方案**:
1. 检查RAM用户是否有OSS权限
2. 确认AccessKey是否正确
3. 检查Bucket名称和Endpoint是否匹配
4. 确认Bucket存在且为私有权限

### 数据不更新

**问题**: 网站数据停留在某个时间点

**解决方案**:
1. 检查数据采集工作流是否正常运行
2. 检查OSS中是否有新数据
3. 手动触发网站部署工作流
4. 清除浏览器缓存

## 自定义域名（可选）

如果你想使用自定义域名：

1. 在DNS提供商添加CNAME记录，指向 `your-username.github.io`
2. 在仓库的 Settings > Pages > Custom domain 中添加你的域名
3. 启用 "Enforce HTTPS"

## 成本估算

### 阿里云OSS
- 存储费用：约 ¥0.12/GB/月
- 流量费用：约 ¥0.50/GB（外网下行）
- 请求费用：基本可忽略

**预估月成本**：
- 数据存储（1个月约1GB）：¥0.12
- GitHub Actions流量：免费（2000分钟/月）
- 总计：约 ¥1-2/月

### GitHub
- Actions：免费（公开仓库）
- Pages：免费
- 存储：免费

## 维护建议

1. **定期检查**：每周检查一次Actions运行状态
2. **数据备份**：定期导出OSS中的重要数据
3. **成本监控**：在阿里云控制台设置费用告警
4. **更新依赖**：每月检查并更新npm和pip依赖
5. **日志审查**：定期查看Actions运行日志，发现潜在问题

## 支持

如果遇到问题：
1. 查看[Issues](https://github.com/PPsteven/shanghai-view-tourist-realtime/issues)
2. 提交新的Issue描述你的问题
3. 附上相关的错误日志和配置信息（不要包含敏感信息！）
