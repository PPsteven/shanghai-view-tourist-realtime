# 上海旅游景区实时人流数据爬虫

[![GitHub](https://img.shields.io/github/license/PPsteven/shanghai-view-tourist-realtime)](https://github.com/PPsteven/shanghai-view-tourist-realtime)
[![Python](https://img.shields.io/badge/python-3.9-blue.svg)](https://www.python.org/downloads/)
[![GitHub Actions](https://github.com/PPsteven/shanghai-view-tourist-realtime/actions/workflows/tourist-crawler.yml/badge.svg)](https://github.com/PPsteven/shanghai-view-tourist-realtime/actions/workflows/tourist-crawler.yml)

这是一个用于定时抓取上海市主要旅游景区实时人流数据的 Python 脚本，并将数据存储到阿里云 OSS 对象存储中。

## 前言
多年前实现的脚本，用于定时爬取上海景区数据，用来做人流量展示的，适合用于课堂教学使用。
由于服务器和数据库到期后就没有继续爬了，感觉比较可惜，数据连续性断了。
昨天突发奇想，用阿里云OSS(存储) + Github Actions(定时) 可以几乎很低成本的实现这个项目，快速实现了一版，后续用这种方式，持续把好用的玩具开源出来。

后续TODO:

- [ ] 前端 Github Pages 实现可视化 + Github Actions(定时脚本推送)

## 功能特性

- 🕒 **定时采集**: 每10分钟自动抓取一次数据
- 📊 **双重存储**: 支持按日期和按景点名称两种数据组织方式
- ☁️ **云端存储**: 数据直接上传至阿里云 OSS，便于后续分析使用
- 🛡️ **高可靠性**: 包含错误处理和重试机制
- ⚙️ **自动化部署**: 基于 GitHub Actions 实现全自动运行

## 技术架构

- **语言**: Python 3.9
- **核心依赖**:
  - `requests`: HTTP 请求库
  - `oss2`: 阿里云 OSS SDK
- **部署平台**: GitHub Actions
- **存储服务**: 阿里云对象存储 OSS

## 数据来源

本项目数据来源于上海市文旅局官方接口：
```
https://tourist.whlyj.sh.gov.cn/api/statistics/getViewTourist
```

## 数据结构

数据按照两种方式进行组织并存储在 OSS 中：

### 按日期存储
路径：`tourist_data/by_date/YYYY/MM/DD/data.json`

```json
{
  "date": "2025/11/07",
  "last_updated": "2025-11-07T11:00:00.000000",
  "total_records": 5,
  "data": [
    {
      // 多次采集的数据记录
    }
  ]
}
```

### 按景点名称存储
路径：`tourist_data/by_name/{景点名称}/data.json`

```json
{
  "spot_name": "外滩",
  "spot_code": "WH001",
  "district": "黄浦区",
  "last_updated": "2025-11-07T11:00:00.000000",
  "total_records": 10,
  "data": [
    {
      // 该景点多次采集的数据记录
    }
  ]
}
```

## 快速开始

### 环境准备

1. **安装 Python 3.9+**
2. **安装依赖包**:
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境变量**:
   复制 `.env.example` 为 `.env` 并填写以下配置项：
   ```bash
   # 阿里云 OSS 配置
   OSS_ACCESS_KEY_ID=your_access_key_id
   OSS_ACCESS_KEY_SECRET=your_access_key_secret
   OSS_ENDPOINT=oss-cn-shanghai.aliyuncs.com
   OSS_BUCKET_NAME=your_bucket_name
   ```

### 手动运行

```bash
python tourist_crawler.py
```

### 自动化运行

项目通过 GitHub Actions 实现每10分钟自动运行一次数据采集任务。

## 部署配置

### GitHub Secrets 配置

在仓库设置中添加以下 Secrets：
- `OSS_ACCESS_KEY_ID`: 阿里云访问密钥 ID
- `OSS_ACCESS_KEY_SECRET`: 阿里云访问密钥 Secret
- `OSS_ENDPOINT`: OSS 服务节点地址

### 环境变量说明

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `OSS_ACCESS_KEY_ID` | - | 阿里云访问密钥 ID |
| `OSS_ACCESS_KEY_SECRET` | - | 阿里云访问密钥 Secret |
| `OSS_ENDPOINT` | oss-cn-shanghai.aliyuncs.com | OSS 服务节点地址 |
| `OSS_BUCKET_NAME` | shanghai-tourist-traffic | OSS 存储桶名称 |

## 本地开发

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行测试
```bash
python tourist_crawler.py
```

## 注意事项

1. 请确保阿里云 OSS 相关权限配置正确
2. 不要将敏感信息提交到代码仓库中
3. 建议定期检查 OSS 存储空间使用情况

## License

本项目采用 MIT 许可证，详情请见 [LICENSE](LICENSE) 文件。
