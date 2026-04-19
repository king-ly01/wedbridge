<template>
  <div class="dashboard-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-icon">
        <el-icon><HomeFilled /></el-icon>
      </div>
      <div class="header-content">
        <h1 class="page-title">控制台</h1>
        <p class="page-subtitle">实时监控您的机器人运行状态</p>
      </div>
    </div>
    
    <!-- 品牌标题 -->
    <div class="brand-header">
      <div class="brand-logo">
        <svg viewBox="0 0 200 200" class="bridge-icon-small">
          <defs>
            <linearGradient id="dashBridgeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style="stop-color:#ffffff;stop-opacity:1" />
              <stop offset="100%" style="stop-color:#e0e7ff;stop-opacity:1" />
            </linearGradient>
          </defs>
          
          <!-- 外圈 -->
          <circle cx="100" cy="100" r="95" fill="none" stroke="url(#dashBridgeGrad)" stroke-width="2" opacity="0.3"/>
          <circle cx="100" cy="100" r="85" fill="none" stroke="url(#dashBridgeGrad)" stroke-width="1" opacity="0.5"/>
          
          <!-- 主桥拱 -->
          <path d="M 25 140 Q 100 60 175 140" fill="none" stroke="url(#dashBridgeGrad)" stroke-width="8" stroke-linecap="round"/>
          
          <!-- 桥身 -->
          <rect x="20" y="135" width="160" height="10" rx="5" fill="url(#dashBridgeGrad)"/>
          
          <!-- 支撑柱 -->
          <rect x="55" y="105" width="6" height="35" rx="3" fill="white" opacity="0.9"/>
          <rect x="97" y="85" width="6" height="55" rx="3" fill="white" opacity="0.9"/>
          <rect x="139" y="105" width="6" height="35" rx="3" fill="white" opacity="0.9"/>
          
          <!-- 数据流 -->
          <path d="M 35 125 Q 65 115 95 120" fill="none" stroke="#67c23a" stroke-width="3" stroke-linecap="round" opacity="0.9"/>
          <path d="M 95 120 Q 125 125 155 118" fill="none" stroke="#409eff" stroke-width="3" stroke-linecap="round" opacity="0.9"/>
          
          <!-- 节点 -->
          <circle cx="35" cy="125" r="5" fill="#67c23a"/>
          <circle cx="97" cy="100" r="7" fill="#409eff"/>
          <circle cx="160" cy="122" r="5" fill="#e6a23c"/>
          
          <!-- 中心光晕 -->
          <circle cx="97" cy="100" r="10" fill="none" stroke="#409eff" stroke-width="2" opacity="0.5"/>
        </svg>
      </div>
      <h1 class="brand-title">WEDBRIDGE</h1>
      <p class="brand-desc">智能消息桥接平台</p>
    </div>
    
    <!-- 石拱桥图表 -->
    <div class="bridge-chart-container">
      <div class="bridge-title">
        <el-icon><DataLine /></el-icon>
        <span>消息流通桥</span>
      </div>
      <div class="bridge-wrapper">
        <!-- 桥身 -->
        <svg class="bridge-svg" viewBox="0 0 800 300" preserveAspectRatio="xMidYMid meet">
          <!-- 定义渐变 -->
          <defs>
            <linearGradient id="stoneGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" style="stop-color:#e8e8e8;stop-opacity:1" />
              <stop offset="50%" style="stop-color:#d0d0d0;stop-opacity:1" />
              <stop offset="100%" style="stop-color:#b8b8b8;stop-opacity:1" />
            </linearGradient>
            <linearGradient id="archGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" style="stop-color:#f5f5f5;stop-opacity:1" />
              <stop offset="100%" style="stop-color:#e0e0e0;stop-opacity:1" />
            </linearGradient>
            <linearGradient id="flowGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" style="stop-color:#409eff;stop-opacity:0.8" />
              <stop offset="50%" style="stop-color:#67c23a;stop-opacity:0.9" />
              <stop offset="100%" style="stop-color:#409eff;stop-opacity:0.8" />
            </linearGradient>
          </defs>
          
          <!-- 桥墩 -->
          <rect x="50" y="200" width="60" height="100" fill="url(#stoneGradient)" rx="5" />
          <rect x="250" y="200" width="60" height="100" fill="url(#stoneGradient)" rx="5" />
          <rect x="450" y="200" width="60" height="100" fill="url(#stoneGradient)" rx="5" />
          <rect x="650" y="200" width="60" height="100" fill="url(#stoneGradient)" rx="5" />
          
          <!-- 桥拱 - 三个拱形 -->
          <path d="M 80 200 Q 180 80 280 200" fill="none" stroke="url(#stoneGradient)" stroke-width="20" stroke-linecap="round" />
          <path d="M 280 200 Q 380 80 480 200" fill="none" stroke="url(#stoneGradient)" stroke-width="20" stroke-linecap="round" />
          <path d="M 480 200 Q 580 80 680 200" fill="none" stroke="url(#stoneGradient)" stroke-width="20" stroke-linecap="round" />
          
          <!-- 桥面 -->
          <rect x="30" y="190" width="740" height="25" fill="url(#stoneGradient)" rx="3" />
          
          <!-- 栏杆柱子 -->
          <rect x="40" y="165" width="8" height="25" fill="#c0c0c0" rx="2" />
          <rect x="120" y="165" width="8" height="25" fill="#c0c0c0" rx="2" />
          <rect x="200" y="165" width="8" height="25" fill="#c0c0c0" rx="2" />
          <rect x="280" y="165" width="8" height="25" fill="#c0c0c0" rx="2" />
          <rect x="360" y="165" width="8" height="25" fill="#c0c0c0" rx="2" />
          <rect x="440" y="165" width="8" height="25" fill="#c0c0c0" rx="2" />
          <rect x="520" y="165" width="8" height="25" fill="#c0c0c0" rx="2" />
          <rect x="600" y="165" width="8" height="25" fill="#c0c0c0" rx="2" />
          <rect x="680" y="165" width="8" height="25" fill="#c0c0c0" rx="2" />
          <rect x="752" y="165" width="8" height="25" fill="#c0c0c0" rx="2" />
          
          <!-- 栏杆横梁 -->
          <rect x="30" y="160" width="740" height="8" fill="#d0d0d0" rx="2" />
          
          <!-- 流动效果 - 消息流 -->
          <circle class="flow-particle" cx="80" cy="180" r="6" fill="#409eff">
            <animate attributeName="cx" values="80;280;480;680;750" dur="3s" repeatCount="indefinite" />
            <animate attributeName="cy" values="180;170;180;170;180" dur="3s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="1;1;1;1;0" dur="3s" repeatCount="indefinite" />
          </circle>
          <circle class="flow-particle" cx="80" cy="180" r="5" fill="#67c23a">
            <animate attributeName="cx" values="80;280;480;680;750" dur="3s" begin="1s" repeatCount="indefinite" />
            <animate attributeName="cy" values="180;170;180;170;180" dur="3s" begin="1s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="1;1;1;1;0" dur="3s" begin="1s" repeatCount="indefinite" />
          </circle>
          <circle class="flow-particle" cx="80" cy="180" r="5" fill="#e6a23c">
            <animate attributeName="cx" values="80;280;480;680;750" dur="3s" begin="2s" repeatCount="indefinite" />
            <animate attributeName="cy" values="180;170;180;170;180" dur="3s" begin="2s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="1;1;1;1;0" dur="3s" begin="2s" repeatCount="indefinite" />
          </circle>
          
          <!-- 数据标签 -->
          <text x="180" y="250" text-anchor="middle" class="bridge-label">WeCom</text>
          <text x="380" y="250" text-anchor="middle" class="bridge-label">Bridge</text>
          <text x="580" y="250" text-anchor="middle" class="bridge-label">Dify</text>
          
          <!-- 消息数量 -->
          <text x="180" y="275" text-anchor="middle" class="bridge-stat">{{ bridgeStats.wecom }}</text>
          <text x="380" y="275" text-anchor="middle" class="bridge-stat">{{ bridgeStats.bridge }}</text>
          <text x="580" y="275" text-anchor="middle" class="bridge-stat">{{ bridgeStats.dify }}</text>
        </svg>
        
        <!-- 水波纹效果 -->
        <div class="water-effect">
          <div class="wave wave-1"></div>
          <div class="wave wave-2"></div>
          <div class="wave wave-3"></div>
        </div>
      </div>
      
      <!-- 统计信息 -->
      <div class="bridge-stats">
        <div class="stat-item">
          <div class="stat-value">{{ bridgeStats.totalMessages }}</div>
          <div class="stat-label">总消息数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value" style="color: #67c23a;">{{ bridgeStats.successRate }}%</div>
          <div class="stat-label">成功率</div>
        </div>
        <div class="stat-item">
          <div class="stat-value" style="color: #409eff;">{{ bridgeStats.activeBots }}</div>
          <div class="stat-label">活跃机器人</div>
        </div>
      </div>
    </div>
    
    <!-- 统计卡片 -->
    <h2 class="section-title">
      <el-icon><TrendCharts /></el-icon>
      <span>机器人统计</span>
    </h2>
    <el-row :gutter="24" class="stats-row">
      <el-col :xs="24" :sm="8">
        <el-card class="stat-card" :body-style="{ padding: '30px' }">
          <template #header>
            <div class="stat-card-header">
              <el-icon><Monitor /></el-icon>
              <span>机器人总数</span>
            </div>
          </template>
          <div class="stat-number-large">{{ stats.total }}</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card class="stat-card" :body-style="{ padding: '30px' }">
          <template #header>
            <div class="stat-card-header">
              <el-icon><CircleCheck /></el-icon>
              <span>已启用</span>
            </div>
          </template>
          <div class="stat-number-large" style="color: #67C23A;">{{ stats.enabled }}</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card class="stat-card" :body-style="{ padding: '30px' }">
          <template #header>
            <div class="stat-card-header">
              <el-icon><CircleClose /></el-icon>
              <span>已禁用</span>
            </div>
          </template>
          <div class="stat-number-large" style="color: #909399;">{{ stats.disabled }}</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { HomeFilled, DataLine, TrendCharts, Monitor, CircleCheck, CircleClose } from '@element-plus/icons-vue'

const stats = ref({ total: 0, enabled: 0, disabled: 0 })

// 桥图统计数据
const bridgeStats = ref({
  wecom: 0,
  bridge: 0,
  dify: 0,
  totalMessages: 0,
  successRate: 0,
  activeBots: 0
})

onMounted(async () => {
  try {
    const response = await axios.get('/api/bots')
    const bots = response.data
    stats.value = {
      total: bots.length,
      enabled: bots.filter(b => b.enabled).length,
      disabled: bots.filter(b => !b.enabled).length
    }
    
    // 获取桥图数据
    await fetchBridgeStats()
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
})

async function fetchBridgeStats() {
  try {
    // 获取当前用户的统计数据
    const response = await axios.get('/api/user/stats')
    bridgeStats.value = response.data
  } catch (error) {
    console.error('获取桥图数据失败:', error)
    // 使用默认数据
    bridgeStats.value = {
      wecom: 0,
      bridge: 0,
      dify: 0,
      totalMessages: 0,
      successRate: 0,
      activeBots: 0
    }
  }
}
</script>

<style scoped>
.dashboard-container {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

/* 页面标题 */
.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.header-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #1a5fb4 0%, #0d3a7a 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.page-subtitle {
  font-size: 14px;
  color: #909399;
  margin: 4px 0 0 0;
}

/* 品牌标题样式 */
.brand-header {
  text-align: center;
  margin-bottom: 24px;
  padding: 30px;
  background: linear-gradient(135deg, #1a5fb4 0%, #0d3a7a 100%);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;
}

.brand-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.03'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
  opacity: 0.5;
}

.brand-logo {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
  border: 2px solid rgba(255, 255, 255, 0.2);
  position: relative;
  z-index: 1;
}

.bridge-icon-small {
  width: 40px;
  height: 40px;
}

.brand-title {
  font-size: 42px;
  font-weight: 700;
  margin: 0 0 8px 0;
  color: white;
  letter-spacing: 4px;
  font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
  position: relative;
  z-index: 1;
}

.brand-desc {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
  font-weight: 300;
  letter-spacing: 2px;
  position: relative;
  z-index: 1;
}

/* 石拱桥图表容器 */
.bridge-chart-container {
  background: #ffffff;
  border-radius: 16px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid #e4e7ed;
  margin-bottom: 24px;
}

.bridge-title {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 25px;
}

.bridge-title .el-icon {
  font-size: 24px;
  color: #1a5fb4;
}

.bridge-wrapper {
  position: relative;
  background: linear-gradient(180deg, #e8f4f8 0%, #d0e8f0 50%, #b8dce8 100%);
  border-radius: 12px;
  padding: 20px;
  overflow: hidden;
}

.bridge-svg {
  width: 100%;
  height: auto;
  display: block;
}

.bridge-label {
  font-size: 14px;
  font-weight: 600;
  fill: #606266;
}

.bridge-stat {
  font-size: 18px;
  font-weight: bold;
  fill: #1a5fb4;
}

/* 水波纹效果 */
.water-effect {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 60px;
  overflow: hidden;
  opacity: 0.6;
}

.wave {
  position: absolute;
  bottom: 0;
  left: -100%;
  width: 300%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(26, 95, 180, 0.3), transparent);
  animation: wave-flow 4s linear infinite;
}

.wave-1 {
  animation-delay: 0s;
}

.wave-2 {
  animation-delay: 1.3s;
  opacity: 0.5;
}

.wave-3 {
  animation-delay: 2.6s;
  opacity: 0.3;
}

@keyframes wave-flow {
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(33.33%);
  }
}

/* 流动粒子动画 */
.flow-particle {
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

/* 桥图统计 */
.bridge-stats {
  display: flex;
  justify-content: center;
  gap: 60px;
  margin-top: 25px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 5px;
}

/* 章节标题 */
.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 30px 0 20px;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.section-title .el-icon {
  font-size: 22px;
  color: #1a5fb4;
}

/* 统计卡片 */
.stats-row {
  margin-top: 20px;
}

.stat-card {
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transition: transform 0.3s, box-shadow 0.3s;
  border: none;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.stat-card :deep(.el-card__header) {
  padding: 16px 20px;
  font-size: 16px;
  font-weight: 500;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
}

.stat-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
}

.stat-card-header .el-icon {
  font-size: 18px;
  color: #1a5fb4;
}

.stat-number-large {
  font-size: 48px;
  font-weight: bold;
  text-align: center;
  color: #1a5fb4;
  padding: 10px 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .dashboard-container {
    padding: 16px;
  }
  
  .page-title {
    font-size: 22px;
  }
  
  .brand-title {
    font-size: 32px;
  }
  
  .bridge-stats {
    gap: 30px;
  }
  
  .stat-number-large {
    font-size: 36px;
  }
}
</style>
