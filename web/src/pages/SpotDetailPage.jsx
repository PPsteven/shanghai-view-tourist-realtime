import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import ReactECharts from 'echarts-for-react'
import './SpotDetailPage.css'

function SpotDetailPage() {
  const { spotCode } = useParams()
  const navigate = useNavigate()
  const [spotData, setSpotData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadSpotData()
  }, [spotCode])

  const loadSpotData = async () => {
    try {
      const response = await fetch(`./data/spots/${spotCode}.json`)
      
      if (response.ok) {
        const rawData = await response.json()
        
        // 处理新的按月存储的数据结构
        if (rawData.months_data && rawData.months_data.length > 0) {
          // 合并所有月份的数据
          const allData = []
          let totalRecords = 0
          let lastUpdated = rawData.last_updated
          let spotName = rawData.spot_name
          let district = ''
          
          rawData.months_data.forEach(monthData => {
            if (monthData.data && monthData.data.length > 0) {
              allData.push(...monthData.data)
              totalRecords += monthData.total_records || monthData.data.length
              if (!district && monthData.district) {
                district = monthData.district
              }
              // 使用最新的更新时间
              if (monthData.last_updated && new Date(monthData.last_updated) > new Date(lastUpdated)) {
                lastUpdated = monthData.last_updated
              }
            }
          })
          
          // 构造兼容原有格式的数据结构
          const processedData = {
            spot_name: spotName,
            spot_code: rawData.spot_code,
            district: district,
            last_updated: lastUpdated,
            total_records: totalRecords,
            data: allData
          }
          
          setSpotData(processedData)
        } else if (rawData.data) {
          // 兼容旧的数据格式
          setSpotData(rawData)
        } else {
          console.error('No valid data structure found in response')
        }
      } else {
        console.error('Failed to load spot data, status:', response.status)
      }
    } catch (error) {
      console.error('Error loading spot data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getVisitorTrendOption = () => {
    if (!spotData || !spotData.data) return {}

    const sortedData = [...spotData.data].sort((a, b) =>
      new Date(a.TIME) - new Date(b.TIME)
    )

    const dates = sortedData.map(item => {
      const date = new Date(item.TIME)
      return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`
    })
    const visitors = sortedData.map(item => item.NUM || 0)

    return {
      title: {
        text: '游客数量变化趋势',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        formatter: (params) => {
          const param = params[0]
          const dataIndex = param.dataIndex
          const item = sortedData[dataIndex]
          return `${param.name}<br/>游客数: ${item.NUM || 0}<br/>舒适度: ${item.SSD}<br/>状态: ${item.TYPE}`
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: dates,
        axisLabel: {
          rotate: 45
        }
      },
      yAxis: {
        type: 'value',
        name: '游客数量'
      },
      series: [
        {
          name: '游客数量',
          type: 'line',
          data: visitors,
          smooth: true,
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(102, 126, 234, 0.5)' },
                { offset: 1, color: 'rgba(102, 126, 234, 0.1)' }
              ]
            }
          },
          itemStyle: {
            color: '#667eea'
          }
        }
      ]
    }
  }

  const getComfortDistributionOption = () => {
    if (!spotData || !spotData.data) return {}

    const comfortMap = new Map()
    spotData.data.forEach(item => {
      const comfort = item.SSD || '未知'
      comfortMap.set(comfort, (comfortMap.get(comfort) || 0) + 1)
    })

    const data = Array.from(comfortMap.entries()).map(([name, value]) => ({
      name,
      value
    }))

    return {
      title: {
        text: '舒适度分布',
        left: 'center'
      },
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        right: 10,
        top: 'center'
      },
      series: [
        {
          name: '舒适度',
          type: 'pie',
          radius: '50%',
          data: data,
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          },
          itemStyle: {
            color: (params) => {
              const colors = {
                '舒适': '#91cc75',
                '较舒适': '#fac858',
                '一般': '#ee6666',
                '暂无': '#999'
              }
              return colors[params.name] || '#5470c6'
            }
          }
        }
      ]
    }
  }

  const getCapacityUtilizationOption = () => {
    if (!spotData || !spotData.data) return {}

    const sortedData = [...spotData.data]
      .filter(item => item.MAX_NUM > 0)
      .sort((a, b) => new Date(a.TIME) - new Date(b.TIME))
      .slice(-20) // Last 20 records

    const dates = sortedData.map(item => {
      const date = new Date(item.TIME)
      return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`
    })
    const utilization = sortedData.map(item =>
      ((item.NUM || 0) / item.MAX_NUM * 100).toFixed(1)
    )

    return {
      title: {
        text: '容量利用率趋势',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        formatter: (params) => {
          const param = params[0]
          const dataIndex = param.dataIndex
          const item = sortedData[dataIndex]
          return `${param.name}<br/>利用率: ${param.value}%<br/>游客数: ${item.NUM}<br/>最大容量: ${item.MAX_NUM}`
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: dates,
        axisLabel: {
          rotate: 45
        }
      },
      yAxis: {
        type: 'value',
        name: '利用率(%)',
        max: 100
      },
      series: [
        {
          name: '容量利用率',
          type: 'bar',
          data: utilization.map(value => ({
            value,
            itemStyle: {
              color: value < 50 ? '#91cc75' : value < 80 ? '#fac858' : '#ee6666'
            }
          }))
        }
      ]
    }
  }

  if (loading) {
    return <div className="loading">加载中...</div>
  }

  if (!spotData) {
    return (
      <div className="spot-detail-page">
        <button className="back-button" onClick={() => navigate('/')}>
          ← 返回首页
        </button>
        <div className="no-data">未找到该景点数据</div>
      </div>
    )
  }

  const latestData = spotData.data && spotData.data.length > 0
    ? [...spotData.data].sort((a, b) => new Date(b.TIME) - new Date(a.TIME))[0]
    : null

  return (
    <div className="spot-detail-page">
      <button className="back-button" onClick={() => navigate('/')}>
        ← 返回首页
      </button>

      <div className="spot-header">
        <h1>{spotData.spot_name}</h1>
        <div className="spot-meta">
          <span className="meta-item">所属区域: {spotData.district}</span>
          <span className="meta-item">景点编号: {spotData.spot_code}</span>
          <span className="meta-item">数据记录: {spotData.total_records} 条</span>
          <span className="meta-item">
            最后更新: {new Date(spotData.last_updated).toLocaleString('zh-CN')}
          </span>
        </div>
      </div>

      {latestData && (
        <div className="current-status">
          <h2>当前状态</h2>
          <div className="status-cards">
            <div className="status-card">
              <div className="status-label">游客数量</div>
              <div className="status-value">{latestData.NUM?.toLocaleString() || 0}</div>
            </div>
            <div className="status-card">
              <div className="status-label">最大容量</div>
              <div className="status-value">{latestData.MAX_NUM?.toLocaleString() || 0}</div>
            </div>
            <div className="status-card">
              <div className="status-label">舒适度</div>
              <div className={`status-value comfort-${latestData.SSD}`}>
                {latestData.SSD || '未知'}
              </div>
            </div>
            <div className="status-card">
              <div className="status-label">开放状态</div>
              <div className={`status-value status-${latestData.TYPE === '正常' ? 'open' : 'closed'}`}>
                {latestData.TYPE || '未知'}
              </div>
            </div>
            <div className="status-card">
              <div className="status-label">景点等级</div>
              <div className="status-value">{latestData.GRADE || '未知'}</div>
            </div>
            <div className="status-card">
              <div className="status-label">开放时间</div>
              <div className="status-value small">{latestData.T_TIME || '未知'}</div>
            </div>
          </div>
          {latestData.WDES && (
            <div className="weather-info">
              <strong>天气情况:</strong> {latestData.WDES} |
              温度: {latestData.WLOW}°C - {latestData.WHIGH}°C |
              风向: {latestData.WDIRECTION} {latestData.WPOWER}
            </div>
          )}
        </div>
      )}

      <div className="charts-section">
        <div className="chart-container full-width">
          <ReactECharts option={getVisitorTrendOption()} style={{ height: '400px' }} />
        </div>
        <div className="chart-container">
          <ReactECharts option={getComfortDistributionOption()} style={{ height: '400px' }} />
        </div>
        <div className="chart-container">
          <ReactECharts option={getCapacityUtilizationOption()} style={{ height: '400px' }} />
        </div>
      </div>

      <div className="data-table">
        <h2>历史数据记录</h2>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>时间</th>
                <th>游客数</th>
                <th>舒适度</th>
                <th>状态</th>
                <th>容量利用率</th>
              </tr>
            </thead>
            <tbody>
              {spotData.data
                .sort((a, b) => new Date(b.TIME) - new Date(a.TIME))
                .slice(0, 50)
                .map((item, index) => (
                  <tr key={index}>
                    <td>{new Date(item.TIME).toLocaleString('zh-CN')}</td>
                    <td>{item.NUM?.toLocaleString() || 0}</td>
                    <td>
                      <span className={`comfort-badge comfort-${item.SSD}`}>
                        {item.SSD || '未知'}
                      </span>
                    </td>
                    <td>
                      <span className={`status-badge status-${item.TYPE === '正常' ? 'open' : 'closed'}`}>
                        {item.TYPE || '未知'}
                      </span>
                    </td>
                    <td>
                      {item.MAX_NUM > 0
                        ? `${((item.NUM || 0) / item.MAX_NUM * 100).toFixed(1)}%`
                        : '-'}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default SpotDetailPage
