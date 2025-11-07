import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import ReactECharts from 'echarts-for-react'
import './HomePage.css'

function HomePage() {
  const [dailyData, setDailyData] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedDate, setSelectedDate] = useState(0)
  const navigate = useNavigate()

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      // Load the last 5 days of data
      // Data files are stored in public/data/ directory
      const data = []
      const dates = []
      const today = new Date()

      for (let i = 4; i >= 0; i--) {
        const date = new Date(today)
        date.setDate(date.getDate() - i)
        const dateStr = date.toISOString().split('T')[0]
        dates.push(dateStr)

        try {
          const response = await fetch(`/data/${dateStr}.json`)
          if (response.ok) {
            const jsonData = await response.json()
            data.push({
              date: dateStr,
              data: jsonData
            })
          }
        } catch (err) {
          console.warn(`Failed to load data for ${dateStr}`)
        }
      }

      setDailyData(data)
      setLoading(false)
    } catch (error) {
      console.error('Error loading data:', error)
      setLoading(false)
    }
  }

  const handleSpotClick = (spotCode) => {
    navigate(`/spot/${spotCode}`)
  }

  // Get current spots with deduplication
  const currentSpots = useMemo(() => {
    if (!dailyData[selectedDate]) return []

    const dataRecords = dailyData[selectedDate].data.data || []
    const allSpots = dataRecords.flatMap(record => record.rows || [])

    // Remove duplicates by CODE, keep the latest data
    const spotMap = new Map()
    allSpots.forEach(spot => {
      spotMap.set(spot.CODE, spot)
    })

    return Array.from(spotMap.values())
  }, [dailyData, selectedDate])

  const getDistrictStatistics = useMemo(() => {
    if (currentSpots.length === 0) return null

    const districtMap = new Map()

    currentSpots.forEach(spot => {
      const district = spot.DNAME || '未知'
      if (!districtMap.has(district)) {
        districtMap.set(district, {
          totalSpots: 0,
          totalVisitors: 0,
          openSpots: 0
        })
      }
      const stat = districtMap.get(district)
      stat.totalSpots++
      stat.totalVisitors += spot.NUM || 0
      if (spot.TYPE === '正常') {
        stat.openSpots++
      }
    })

    return Array.from(districtMap.entries()).map(([name, stat]) => ({
      name,
      ...stat
    }))
  }, [currentSpots])

  const districtChartOption = useMemo(() => {
    const stats = getDistrictStatistics
    if (!stats) return {}

    return {
      title: {
        text: '各区景点游客分布',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      legend: {
        data: ['游客数量', '开放景点数'],
        top: 30
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: stats.map(s => s.name),
        axisLabel: {
          rotate: 45
        }
      },
      yAxis: [
        {
          type: 'value',
          name: '游客数量',
          position: 'left'
        },
        {
          type: 'value',
          name: '景点数量',
          position: 'right'
        }
      ],
      series: [
        {
          name: '游客数量',
          type: 'bar',
          data: stats.map(s => s.totalVisitors),
          itemStyle: {
            color: '#5470c6'
          }
        },
        {
          name: '开放景点数',
          type: 'line',
          yAxisIndex: 1,
          data: stats.map(s => s.openSpots),
          itemStyle: {
            color: '#91cc75'
          }
        }
      ]
    }
  }, [getDistrictStatistics])

  const topSpotsChartOption = useMemo(() => {
    if (currentSpots.length === 0) return {}

    const openSpots = currentSpots.filter(s => s.TYPE === '正常')
    const topSpots = openSpots
      .sort((a, b) => (b.NUM || 0) - (a.NUM || 0))
      .slice(0, 10)

    return {
      title: {
        text: '热门景点TOP10',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        },
        formatter: (params) => {
          const param = params[0]
          const spot = topSpots[param.dataIndex]
          return `${spot.NAME}<br/>游客数: ${spot.NUM}<br/>舒适度: ${spot.SSD}<br/>最大容量: ${spot.MAX_NUM}`
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'value'
      },
      yAxis: {
        type: 'category',
        data: topSpots.map(s => s.NAME),
        axisLabel: {
          width: 150,
          overflow: 'truncate'
        }
      },
      series: [
        {
          name: '游客数量',
          type: 'bar',
          data: topSpots.map(s => ({
            value: s.NUM,
            itemStyle: {
              color: s.SSD === '舒适' ? '#91cc75' :
                     s.SSD === '较舒适' ? '#fac858' : '#ee6666'
            }
          })),
          label: {
            show: true,
            position: 'right'
          }
        }
      ]
    }
  }, [currentSpots])

  if (loading) {
    return <div className="loading">加载中...</div>
  }

  if (dailyData.length === 0) {
    return <div className="no-data">暂无数据</div>
  }

  const currentData = dailyData[selectedDate]

  return (
    <div className="home-page">
      <div className="date-selector">
        {dailyData.map((item, index) => (
          <button
            key={item.date}
            className={`date-button ${selectedDate === index ? 'active' : ''}`}
            onClick={() => setSelectedDate(index)}
          >
            {item.date}
          </button>
        ))}
      </div>

      <div className="summary-cards">
        <div className="card">
          <div className="card-title">总景点数</div>
          <div className="card-value">{currentSpots.length}</div>
        </div>
        <div className="card">
          <div className="card-title">开放景点</div>
          <div className="card-value">
            {currentSpots.filter(s => s.TYPE === '正常').length}
          </div>
        </div>
        <div className="card">
          <div className="card-title">总游客数</div>
          <div className="card-value">
            {currentSpots.reduce((sum, s) => sum + (s.NUM || 0), 0).toLocaleString()}
          </div>
        </div>
        <div className="card">
          <div className="card-title">更新时间</div>
          <div className="card-value small">
            {currentData?.data?.last_updated ?
              new Date(currentData.data.last_updated).toLocaleString('zh-CN') :
              '未知'}
          </div>
        </div>
      </div>

      <div className="charts-section">
        <div className="chart-container">
          <ReactECharts
            option={districtChartOption}
            style={{ height: '400px' }}
            notMerge={true}
            lazyUpdate={true}
          />
        </div>
        <div className="chart-container">
          <ReactECharts
            option={topSpotsChartOption}
            style={{ height: '400px' }}
            notMerge={true}
            lazyUpdate={true}
          />
        </div>
      </div>

      <div className="spots-list">
        <h2>景点列表</h2>
        <div className="spots-grid">
          {currentSpots.map((spot) => (
            <div
              key={spot.CODE}
              className={`spot-card ${spot.TYPE === '正常' ? 'open' : 'closed'}`}
              onClick={() => handleSpotClick(spot.CODE)}
            >
              <div className="spot-name">{spot.NAME}</div>
              <div className="spot-info">
                <span className="spot-district">{spot.DNAME}</span>
                <span className={`spot-status ${spot.TYPE === '正常' ? 'open' : 'closed'}`}>
                  {spot.TYPE}
                </span>
              </div>
              {spot.TYPE === '正常' && (
                <>
                  <div className="spot-visitors">
                    游客数: <strong>{spot.NUM?.toLocaleString() || 0}</strong>
                  </div>
                  <div className="spot-comfort">
                    舒适度: <span className={`comfort-${spot.SSD}`}>{spot.SSD}</span>
                  </div>
                  <div className="spot-capacity">
                    容量: {spot.NUM || 0} / {spot.MAX_NUM?.toLocaleString() || 0}
                  </div>
                </>
              )}
              <div className="spot-grade">
                {spot.GRADE && <span className="grade-badge">{spot.GRADE}</span>}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default HomePage
