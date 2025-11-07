import React from 'react'
import { Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import SpotDetailPage from './pages/SpotDetailPage'
import './App.css'

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>上海旅游景点实时数据</h1>
      </header>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/spot/:spotCode" element={<SpotDetailPage />} />
      </Routes>
    </div>
  )
}

export default App
