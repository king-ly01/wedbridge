<template>
  <div class="bot-manager">
    <!-- 页面标题 -->
    <div class="page-header">
      <div>
        <h2>机器人管理</h2>
        <p class="subtitle">管理您的企业微信智能机器人</p>
      </div>
      <el-button type="primary" size="large" @click="startCreate">
        <el-icon><Plus /></el-icon>
        创建机器人
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">机器人总数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card success">
          <div class="stat-value">{{ stats.connected }}</div>
          <div class="stat-label">已连接</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card warning">
          <div class="stat-value">{{ stats.disconnected }}</div>
          <div class="stat-label">未连接</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card info">
          <div class="stat-value">{{ stats.messages }}</div>
          <div class="stat-label">今日消息</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 机器人列表 -->
    <el-card class="bot-list-card">
      <template #header>
        <div class="card-header">
          <span>机器人列表</span>
          <div class="header-actions">
            <el-input
              v-model="searchQuery"
              placeholder="搜索机器人ID或描述"
              clearable
              :prefix-icon="Search"
              style="width: 250px; margin-right: 12px;"
            />
            <el-button :icon="Refresh" circle @click="refreshData" :loading="loading" />
          </div>
        </div>
      </template>

      <el-table :data="paginatedBots" v-loading="loading" stripe class="bot-table" row-key="bot_id">
        <el-table-column type="index" width="50" align="center" />
        
        <el-table-column label="状态" min-width="120" align="center">
          <template #default="{ row }">
            <div class="status-indicator">
              <span 
                class="status-dot" 
                :class="[getConnectionStatus(row).class, { 'pulse': getConnectionStatus(row).pulse }]"
                :style="{ 
                  backgroundColor: getConnectionStatus(row).color, 
                  boxShadow: '0 0 0 3px ' + getConnectionStatus(row).color + '33' 
                }"
              ></span>
              <span class="status-text" :style="{ color: getConnectionStatus(row).color }">
                {{ getConnectionStatus(row).text }}
              </span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="bot_id" label="机器人ID" min-width="150" show-overflow-tooltip />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />

        <el-table-column label="上次启动时间" min-width="160" align="center">
          <template #default="{ row }">
            <span v-if="getLastStartedAt(row)" class="last-started-time">
              {{ getLastStartedAt(row) }}
            </span>
            <span v-else class="no-data">--</span>
          </template>
        </el-table-column>
        
        <el-table-column label="连接信息" min-width="120" align="center">
          <template #default="{ row }">
            <div v-if="connectionInfo[row.bot_id]" class="connection-info">
              <div>消息: {{ connectionInfo[row.bot_id].message_count || 0 }}</div>
              <div>错误: {{ connectionInfo[row.bot_id].error_count || 0 }}</div>
            </div>
            <span v-else class="no-data">--</span>
          </template>
        </el-table-column>

        <el-table-column label="状态控制" min-width="100" align="center">
          <template #default="{ row }">
            <el-switch
              :model-value="row.enabled"
              :active-icon="Check"
              :inactive-icon="Close"
              inline-prompt
              @change="(val) => handleBotToggle(row, val)"
            />
          </template>
        </el-table-column>

        <el-table-column label="操作" min-width="160" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button 
                size="small" 
                type="primary" 
                plain
                @click="startEdit(row)"
                class="action-btn"
              >
                <el-icon><Edit /></el-icon>修改
              </el-button>
              <el-button 
                size="small" 
                type="danger" 
                plain
                @click="confirmDelete(row)"
                class="action-btn"
              >
                <el-icon><Delete /></el-icon>删除
              </el-button>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="详情" min-width="80" align="center">
          <template #default="{ row }">
            <el-button 
              size="small" 
              @click="viewDetails(row)"
              class="detail-btn"
            >
              <el-icon><View /></el-icon>详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="filteredBots.length"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>

      <el-empty v-if="!loading && filteredBots.length === 0" description="暂无机器人" />
    </el-card>

    <!-- 创建/修改机器人对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '修改机器人' : '创建机器人'"
      width="700px"
      :close-on-click-modal="false"
      @close="resetForm"
    >
      <el-steps :active="currentStep" finish-status="success" simple>
        <el-step title="基本信息" />
        <el-step title="企微配置" />
        <el-step title="Dify配置" />
        <el-step title="完成" />
      </el-steps>

      <div class="step-content">
        <!-- 步骤 1: 基本信息 -->
        <div v-if="currentStep === 0">
          <el-form :model="form" label-width="120px">
            <el-form-item label="机器人ID" required>
              <el-input v-model="form.bot_id" placeholder="唯一标识，如: meeting-bot-01" />
            </el-form-item>
            <el-form-item label="描述">
              <el-input v-model="form.description" type="textarea" rows="3" />
            </el-form-item>
          </el-form>
        </div>

        <!-- 步骤 2: 企微配置 -->
        <div v-if="currentStep === 1">
          <el-form :model="form" label-width="120px">
            <el-form-item label="Bot ID" required>
              <el-input v-model="form.wecom_bot_id" placeholder="企业微信机器人ID" />
            </el-form-item>
            <el-form-item label="Secret" required>
              <el-input v-model="form.wecom_secret" type="password" show-password />
            </el-form-item>
          </el-form>
          
          <!-- 测试连接区域 -->
          <div class="test-connection-area">
            <el-divider />
            
            <!-- 未测试状态 -->
            <div v-if="!wecomTestPassed" class="test-waiting">
              <el-button type="primary" @click="startWecomTest" :loading="testingWecom" size="large">
                测试连接
              </el-button>
              <p class="test-hint">点击测试连接后，请在企业微信给机器人发消息</p>
            </div>
            
            <!-- 测试中状态 -->
            <div v-if="testingWecom && !wecomTestPassed" class="test-running">
              <el-alert
                title="请在企业微信中发送消息"
                type="warning"
                :closable="false"
                show-icon
              />
              <div class="test-instruction-box">
                <p><strong>请按以下步骤操作：</strong></p>
                <ol>
                  <li>打开企业微信，找到机器人 <strong>{{ form.wecom_bot_id }}</strong></li>
                  <li>给机器人发送任意消息（如"你好"或"测试"）</li>
                  <li>等待 Bridge 接收消息并回复连接成功</li>
                </ol>
                <div class="waiting-box">
                  <el-icon class="is-loading" :size="30"><Loading /></el-icon>
                  <span>等待接收消息...（{{ wecomTestCountdown }}秒）</span>
                </div>
              </div>
            </div>
            
            <!-- 测试成功状态 -->
            <div v-if="wecomTestPassed" class="test-success">
              <el-result
                icon="success"
                title="连接成功！"
                sub-title="企业微信机器人已正确配置"
              >
                <template #extra>
                  <p class="success-text">✓ 已收到您的消息</p>
                  <p class="success-text">✓ 机器人可以正常接收和发送消息</p>
                  <p class="success-text">✓ 请检查企业微信是否收到连接成功消息</p>
                </template>
              </el-result>
            </div>
            
            <!-- 测试失败状态 -->
            <div v-if="wecomTestFailed" class="test-failed">
              <el-result
                icon="error"
                title="连接失败"
                :sub-title="wecomTestError"
              >
                <template #extra>
                  <el-button type="primary" @click="restartWecomTest">重新测试</el-button>
                </template>
              </el-result>
            </div>
          </div>
        </div>

        <!-- 步骤 3: Dify配置 -->
        <div v-if="currentStep === 2">
          <el-form :model="form" label-width="120px">
            <el-form-item label="API地址">
              <el-input v-model="form.dify_api_base" placeholder="http://your-dify/v1" />
            </el-form-item>
            <el-form-item label="API Key" required>
              <el-input v-model="form.dify_api_key" type="password" show-password />
            </el-form-item>
          </el-form>
        </div>

        <!-- 步骤 4: 完成 -->
        <div v-if="currentStep === 3" class="finish-step">
          <el-result
            icon="success"
            title="配置完成"
            :sub-title="`机器人「${form.bot_id}」已${isEdit ? '更新' : '创建'}`"
          >
            <template #extra>
              <div class="notify-url-section" v-if="createdNotifyUrl">
                <el-alert
                  title="Dify HTTP 节点配置信息"
                  type="info"
                  :closable="false"
                  show-icon
                  style="margin-bottom: 15px; text-align: left;"
                >
                  <div style="margin-top: 10px;">
                    <p><strong>请在 Dify 工作流的 HTTP 节点中配置以下信息：</strong></p>
                    <div class="url-box">
                      <div class="url-label">请求地址：</div>
                      <el-input
                        v-model="createdNotifyUrl"
                        readonly
                        class="url-input"
                      >
                        <template #append>
                          <el-button @click="copyCreatedNotifyUrl">
                            <el-icon><DocumentCopy /></el-icon>
                          </el-button>
                        </template>
                      </el-input>
                    </div>
                    <div class="url-box">
                      <div class="url-label">请求方法：</div>
                      <el-tag>POST</el-tag>
                    </div>
                    <div class="url-box">
                      <div class="url-label">Content-Type：</div>
                      <el-tag>application/json</el-tag>
                    </div>
                  </div>
                </el-alert>
              </div>
              <el-button type="primary" @click="dialogVisible = false">完成</el-button>
            </template>
          </el-result>
        </div>
      </div>

      <template #footer v-if="currentStep < 3">
        <el-button v-if="currentStep > 0" @click="currentStep--">上一步</el-button>
        <el-button type="primary" @click="nextStep">
          {{ currentStep === 2 ? (isEdit ? '保存修改' : '创建') : '下一步' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 详情抽屉 -->
    <el-drawer
      v-model="detailsVisible"
      title="机器人详情"
      size="500px"
    >
      <div v-if="selectedBot" class="bot-details">
        <h3>{{ selectedBot.bot_id }}</h3>
        <p class="bot-id">ID: {{ selectedBot.bot_id }}</p>
        
        <el-divider />
        
        <!-- Notify URL 区域 -->
        <h4>回调地址 (Dify HTTP 节点配置)</h4>
        <div class="notify-url-section">
          <div class="url-display-box">
            <div class="url-text" :class="{ 'masked': !showToken }">
              {{ displayNotifyUrl }}
            </div>
            <div class="url-actions">
              <el-button 
                :icon="showToken ? Hide : View" 
                circle 
                size="small"
                @click="showToken = !showToken"
                :title="showToken ? '隐藏 Token' : '显示 Token'"
              />
              <el-button 
                icon="DocumentCopy" 
                circle 
                size="small"
                @click="copyNotifyUrl"
                title="复制完整地址"
              />
            </div>
          </div>
          <p class="url-hint">
            <el-icon><InfoFilled /></el-icon>
            在 Dify 工作流的 HTTP 节点中配置此地址，用于接收机器人消息
          </p>
        </div>
        
        <el-divider />
        
        <h4>连接状态</h4>
        <div v-if="connectionInfo[selectedBot.bot_id]" class="status-detail">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="连接状态">
              <el-tag :type="connectionInfo[selectedBot.bot_id].connected ? 'success' : 'danger'">
                {{ connectionInfo[selectedBot.bot_id].connected ? '已连接' : '未连接' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="认证状态">
              {{ connectionInfo[selectedBot.bot_id].authenticated ? '已认证' : '未认证' }}
            </el-descriptions-item>
            <el-descriptions-item label="今日消息">
              {{ connectionInfo[selectedBot.bot_id].today_messages || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="累计消息">
              {{ connectionInfo[selectedBot.bot_id].message_count || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="错误数量">
              {{ connectionInfo[selectedBot.bot_id].error_count || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="运行时间">
              {{ formatUptime(connectionInfo[selectedBot.bot_id].uptime_seconds) }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
        <div v-else class="no-connection-info">
          <el-empty description="暂无连接信息">
            <template #description>
              <p>暂无连接信息</p>
              <p class="sub-text">机器人可能未启动或 Worker 服务未连接</p>
            </template>
            <el-button type="primary" size="small" @click="fetchConnectionStatus">
              <el-icon><Refresh /></el-icon> 刷新状态
            </el-button>
          </el-empty>
        </div>
      </div>
    </el-drawer>

    <!-- 测试连接对话框 -->
    <el-dialog
      v-model="testDialogVisible"
      title="测试机器人连接"
      width="550px"
      :close-on-click-modal="false"
      @close="closeTestDialog"
    >
      <div v-if="testBot" class="test-dialog-content">
        <!-- 步骤 1: 等待用户发送消息 -->
        <div v-if="testStatus === 'waiting'">
          <el-alert
            title="请在企业微信中发送消息"
            type="warning"
            :closable="false"
            show-icon
          />
          <div class="test-instruction-box">
            <p><strong>请按以下步骤操作：</strong></p>
            <ol>
              <li>打开企业微信，找到机器人 <strong>{{ testBot.bot_id }}</strong></li>
              <li>给机器人发送任意消息（如"你好"或"测试"）</li>
              <li>等待 Bridge 接收消息并回复连接成功</li>
            </ol>
            <div class="waiting-box">
              <el-icon class="is-loading" :size="30"><Loading /></el-icon>
              <span>等待接收消息...（{{ testCountdown }}秒）</span>
            </div>
          </div>
        </div>

        <!-- 步骤 2: 连接成功 -->
        <div v-if="testStatus === 'success'">
          <el-result
            icon="success"
            title="连接成功！"
            sub-title="企业微信机器人已正确配置"
          >
            <template #extra>
              <div class="success-info">
                <p class="success-text">✓ 已收到您的消息</p>
                <p class="success-text">✓ 机器人可以正常接收和发送消息</p>
              </div>
              
              <el-divider />
              
              <div class="notify-url-box" v-if="testBot.token">
                <p><strong>Dify HTTP 节点配置 URL：</strong></p>
                <el-input
                  :value="getNotifyUrl(testBot)"
                  readonly
                  class="url-input"
                >
                  <template #append>
                    <el-button @click="copyTestNotifyUrl">
                      <el-icon><DocumentCopy /></el-icon> 复制
                    </el-button>
                  </template>
                </el-input>
              </div>
            </template>
          </el-result>
        </div>

        <!-- 连接失败/超时 -->
        <div v-if="testStatus === 'timeout'">
          <el-result
            icon="error"
            title="连接超时"
            sub-title="未在60秒内收到消息"
          >
            <template #extra>
              <p>请检查：</p>
              <ul style="text-align: left; margin: 10px 0;">
                <li>机器人是否已启动</li>
                <li>企业微信机器人配置是否正确</li>
                <li>是否给企业微信机器人发送了消息</li>
              </ul>
              <el-button type="primary" @click="restartTest">重新测试</el-button>
            </template>
          </el-result>
        </div>
      </div>

      <template #footer>
        <el-button v-if="testStatus !== 'success'" @click="closeTestDialog">取消</el-button>
        <el-button v-if="testStatus === 'success'" type="primary" @click="closeTestDialog">完成</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, View, Edit, Delete, CircleClose, CircleCheck, Warning, ChatDotRound, InfoFilled, Loading, DocumentCopy, Search, Check, Close, Hide } from '@element-plus/icons-vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

// 状态
const loading = ref(false)
const bots = ref([])
const connectionInfo = ref({})
const refreshTimer = ref(null)

// 对话框状态
const dialogVisible = ref(false)
const currentStep = ref(0)
const isEdit = ref(false)
const originalBotId = ref(null)
const testingWecom = ref(false)

// 详情抽屉
const detailsVisible = ref(false)
const selectedBot = ref(null)
const showToken = ref(false)

// 测试对话框
const testDialogVisible = ref(false)
const testBot = ref(null)
const testStatus = ref('waiting') // waiting, success, timeout
const testCountdown = ref(60)
const testCountdownTimer = ref(null)

// 创建完成后显示的 notify URL
const createdNotifyUrl = ref('')

// 企微测试状态（创建流程中使用）
const wecomTestPassed = ref(false)
const wecomTestFailed = ref(false)
const wecomTestCountdown = ref(60)
const wecomTestError = ref('')
const wecomTestTimer = ref(null)

// 搜索和分页
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(10)

// 过滤并排序后的机器人列表
// 排序规则：开启的在上面，关闭的在下面；同组内按上次启动时间倒序
const filteredBots = computed(() => {
  let list = bots.value
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    list = list.filter(bot => 
      bot.bot_id.toLowerCase().includes(query) || 
      (bot.description && bot.description.toLowerCase().includes(query))
    )
  }
  // 排序：enabled 在上，disabled 在下；同组按 last_started_at 倒序
  return [...list].sort((a, b) => {
    // 1. enabled 优先
    if (a.enabled !== b.enabled) return a.enabled ? -1 : 1
    // 2. 同组内按上次启动时间倒序（最近启动的排最前）
    const aTime = getLastStartedAtRaw(a)
    const bTime = getLastStartedAtRaw(b)
    if (aTime && bTime) return new Date(bTime) - new Date(aTime)
    if (aTime) return -1
    if (bTime) return 1
    return 0
  })
})

// 分页后的机器人列表
const paginatedBots = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredBots.value.slice(start, end)
})

// 分页事件处理
function handleSizeChange(val) {
  pageSize.value = val
  currentPage.value = 1
}

function handleCurrentChange(val) {
  currentPage.value = val
}

// Notify URL 显示（带遮罩）
const displayNotifyUrl = computed(() => {
  if (!selectedBot.value) return ''
  const baseUrl = window.location.origin
  const url = `${baseUrl}/notify?token=${selectedBot.value.token}`
  if (showToken.value) {
    return url
  }
  // 遮罩 token
  return `${baseUrl}/notify?token=********************`
})

// 复制 Notify URL
function copyNotifyUrl() {
  if (!selectedBot.value) return
  const baseUrl = window.location.origin
  const fullUrl = `${baseUrl}/notify?token=${selectedBot.value.token}`
  
  // 尝试使用现代 Clipboard API
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(fullUrl).then(() => {
      ElMessage.success('回调地址已复制到剪贴板')
    }).catch(() => {
      // 降级使用传统方法
      fallbackCopyTextToClipboard(fullUrl)
    })
  } else {
    // 使用传统方法
    fallbackCopyTextToClipboard(fullUrl)
  }
}

// 复制创建完成页面的 Notify URL
function copyCreatedNotifyUrl() {
  if (!createdNotifyUrl.value) return
  
  // 尝试使用现代 Clipboard API
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(createdNotifyUrl.value).then(() => {
      ElMessage.success('请求地址已复制到剪贴板')
    }).catch(() => {
      // 降级使用传统方法
      fallbackCopyTextToClipboard(createdNotifyUrl.value)
    })
  } else {
    // 使用传统方法
    fallbackCopyTextToClipboard(createdNotifyUrl.value)
  }
}

// 传统复制方法（兼容 HTTP 环境）
function fallbackCopyTextToClipboard(text) {
  const textArea = document.createElement('textarea')
  textArea.value = text
  textArea.style.position = 'fixed'
  textArea.style.left = '-9999px'
  textArea.style.top = '0'
  document.body.appendChild(textArea)
  textArea.focus()
  textArea.select()
  
  try {
    const successful = document.execCommand('copy')
    if (successful) {
      ElMessage.success('回调地址已复制到剪贴板')
    } else {
      ElMessage.error('复制失败，请手动复制')
    }
  } catch (err) {
    ElMessage.error('复制失败，请手动复制')
  }
  
  document.body.removeChild(textArea)
}

// 表单
const form = ref({
  bot_id: '',
  name: '',
  description: '',
  wecom_bot_id: '',
  wecom_secret: '',
  default_chatid: '',  // 测试连接时获取的 chatid
  dify_api_base: '',
  dify_api_key: '',
  enabled: true
})

// 统计
const stats = computed(() => {
  const total = bots.value.length
  const connected = bots.value.filter(b => 
    connectionInfo.value[b.bot_id]?.connected
  ).length
  return {
    total,
    connected,
    disconnected: total - connected,
    messages: Object.values(connectionInfo.value).reduce(
      (sum, info) => sum + (info.today_messages || 0), 0  // 使用今日消息数
    )
  }
})

// 获取连接状态 - 完整状态反馈系统
// 状态规则：
// - 未启动（灰色）：机器人 disabled
// - 正在连接（蓝色）：enabled 但还未 connected/authenticated
// - 连接成功（绿色）：enabled + connected + authenticated
// - 连接失败（红色）：enabled 但连接异常或认证失败
function getConnectionStatus(bot) {
  const info = connectionInfo.value[bot.bot_id]
  
  // 机器人未启用 - 灰色
  if (!bot.enabled) {
    return { class: 'disabled', text: '未启动', color: '#909399', pulse: false }
  }
  
  // 已启用但没有连接信息 - 正在连接中（蓝色闪烁）
  if (!info) {
    return { class: 'connecting', text: '正在连接', color: '#409eff', pulse: true }
  }
  
  // 已启用，连接上了但认证失败 - 红色（连接失败）
  if (info.connected && !info.authenticated) {
    return { class: 'error', text: '连接失败', color: '#f56c6c', pulse: false }
  }
  
  // 已启用但未连接 - 正在连接中（蓝色闪烁）
  if (!info.connected) {
    return { class: 'connecting', text: '正在连接', color: '#409eff', pulse: true }
  }
  
  // 已启用、已连接、已认证 - 绿色（连接成功）
  if (info.connected && info.authenticated) {
    return { class: 'connected', text: '连接成功', color: '#67c23a', pulse: false }
  }
  
  return { class: 'unknown', text: '未知', color: '#909399', pulse: false }
}

// 获取上次启动时间原始值（用于排序）
function getLastStartedAtRaw(bot) {
  // 优先从连接信息中获取（实时），其次从数据库记录获取
  const info = connectionInfo.value[bot.bot_id]
  if (info && info.last_started_at) return info.last_started_at
  if (bot.last_started_at) return bot.last_started_at
  return null
}

// 格式化上次启动时间（用于显示）
function getLastStartedAt(bot) {
  const raw = getLastStartedAtRaw(bot)
  if (!raw) return null
  const d = new Date(raw)
  if (isNaN(d.getTime())) return null
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

// 格式化运行时间
function formatUptime(seconds) {
  if (!seconds) return '--'
  const hours = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  if (hours > 0) return `${hours}小时${mins}分钟`
  return `${mins}分钟`
}

// 获取机器人列表
async function fetchBots() {
  loading.value = true
  try {
    const response = await axios.get('/api/bots')
    bots.value = response.data
    await fetchConnectionStatus()
  } catch (error) {
    ElMessage.error('获取机器人列表失败')
  } finally {
    loading.value = false
  }
}

// 获取连接状态
async function fetchConnectionStatus() {
  try {
    // 从 Worker 服务获取连接状态（通过代理）
    const response = await axios.get('/worker/stats', { timeout: 5000 })
    const workerStats = response.data
    
    console.log('Worker stats:', workerStats) // 调试日志
    
    // 转换为 connectionInfo 格式
    const info = {}
    for (const [botId, conn] of Object.entries(workerStats.bots || {})) {
      info[botId] = {
        connected: conn.connected,
        authenticated: conn.authenticated,
        message_count: conn.message_count || 0,
        today_messages: conn.today_messages || 0,
        error_count: conn.error_count || 0,
        uptime_seconds: conn.uptime_seconds || 0,
        last_interaction_success: conn.last_interaction_success,
        last_started_at: conn.last_started_at || null
      }
    }
    connectionInfo.value = info
    console.log('Connection info updated:', info) // 调试日志
  } catch (error) {
    // Worker 服务可能不可用，清空连接信息
    console.log('Worker 服务不可用，清空连接状态', error)
    connectionInfo.value = {}
  }
}

// 刷新数据
function refreshData() {
  fetchBots()
  ElMessage.success('已刷新')
}

// 开始创建
function startCreate() {
  isEdit.value = false
  originalBotId.value = null
  resetForm()
  dialogVisible.value = true
}

// 开始修改
function startEdit(bot) {
  isEdit.value = true
  originalBotId.value = bot.bot_id
  form.value = { ...bot }
  currentStep.value = 0
  dialogVisible.value = true
}

// 查看详情
async function viewDetails(bot) {
  selectedBot.value = bot
  detailsVisible.value = true
  // 打开详情时刷新连接状态，确保显示最新数据
  await fetchConnectionStatus()
}

// 下一步
async function nextStep() {
  // 步骤 0: 验证基本信息
  if (currentStep.value === 0) {
    if (!form.value.bot_id || !form.value.bot_id.trim()) {
      ElMessage.warning('请输入机器人ID')
      return
    }
    currentStep.value++
    return
  }
  
  // 步骤 1: 验证企微配置
  if (currentStep.value === 1) {
    if (!form.value.wecom_bot_id || !form.value.wecom_bot_id.trim()) {
      ElMessage.warning('请输入企业微信 Bot ID')
      return
    }
    if (!form.value.wecom_secret || !form.value.wecom_secret.trim()) {
      ElMessage.warning('请输入企业微信 Secret')
      return
    }
    // 检查是否已通过测试连接
    if (!wecomTestPassed.value) {
      ElMessage.warning('请先点击"测试连接"完成连接验证')
      return
    }
    currentStep.value++
    return
  }
  
  // 步骤 2: 保存
  if (currentStep.value === 2) {
    await saveBot()
  }
}

// 保存机器人
async function saveBot() {
  try {
    const submitData = { ...form.value }
    
    if (isEdit.value) {
      // 修改 = 删除旧 + 创建新（原子操作）
      await axios.delete(`/api/bots/${originalBotId.value}`)
    }
    const response = await axios.post('/api/bots', submitData)
    
    // 保存创建返回的 notify_url
    if (response.data.notify_url) {
      createdNotifyUrl.value = response.data.notify_url
    }
    
    ElMessage.success(isEdit.value ? '修改成功' : '创建成功')
    currentStep.value = 3
    fetchBots()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  }
}

// 确认删除
async function confirmDelete(bot) {
  try {
    const statusInfo = connectionInfo.value[bot.bot_id]
    const isConnected = statusInfo?.connected
    
    let message = `
      <div style="text-align: left;">
        <p>确定要删除机器人 <strong>"${bot.bot_id}"</strong> 吗？</p>
        <p style="color: #f56c6c; margin-top: 10px;">
          <el-icon><Warning /></el-icon> 
          此操作不可恢复，机器人配置将永久丢失！
        </p>
        ${isConnected ? '<p style="color: #e6a23c; margin-top: 5px;">⚠️ 该机器人当前处于连接状态，删除后将断开连接。</p>' : ''}
      </div>
    `
    
    await ElMessageBox.confirm(
      message,
      '⚠️ 确认删除机器人',
      {
        type: 'error',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        dangerouslyUseHTMLString: true,
        confirmButtonClass: 'el-button--danger'
      }
    )
    
    await axios.delete(`/api/bots/${bot.bot_id}`)
    ElMessage.success(`机器人 "${bot.bot_id}" 已删除`)
    fetchBots()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + (error.response?.data?.detail || '未知错误'))
    }
  }
}

// 处理机器人开关切换
async function handleBotToggle(bot, newValue) {
  // 先根据新值调用对应函数
  if (newValue) {
    await confirmStart(bot)
  } else {
    await confirmStop(bot)
  }
}

// 确认启动机器人
async function confirmStart(bot) {
  try {
    await ElMessageBox.confirm(
      `
        <div style="text-align: left;">
          <p>确定要启动机器人 <strong>"${bot.bot_id}"</strong> 吗？</p>
          <p style="color: #67c23a; margin-top: 10px;">
            ✓ 启动后，机器人将开始接收消息并转发到 Dify
          </p>
        </div>
      `,
      '确认启动机器人',
      {
        type: 'success',
        confirmButtonText: '确认启动',
        cancelButtonText: '取消',
        dangerouslyUseHTMLString: true
      }
    )
    
    await axios.post(`/api/bots/${bot.bot_id}/start`)
    ElMessage.success(`机器人 "${bot.bot_id}" 已启动`)
    fetchBots()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('启动失败: ' + (error.response?.data?.detail || '未知错误'))
    }
    // 无论成功或取消，都刷新列表以确保状态一致
    fetchBots()
  }
}

// 确认停止机器人
async function confirmStop(bot) {
  try {
    const statusInfo = connectionInfo.value[bot.bot_id]
    const isConnected = statusInfo?.connected
    
    await ElMessageBox.confirm(
      `
        <div style="text-align: left;">
          <p>确定要停止机器人 <strong>"${bot.bot_id}"</strong> 吗？</p>
          <p style="color: #f56c6c; margin-top: 10px;">
            ⚠️ 停止后，机器人将断开连接，不再接收和转发消息
          </p>
          ${isConnected ? '<p style="color: #e6a23c; margin-top: 5px;">该机器人当前处于连接状态。</p>' : ''}
        </div>
      `,
      '⚠️ 确认停止机器人',
      {
        type: 'error',
        confirmButtonText: '确认停止',
        cancelButtonText: '取消',
        dangerouslyUseHTMLString: true,
        confirmButtonClass: 'el-button--danger'
      }
    )
    
    await axios.post(`/api/bots/${bot.bot_id}/stop`)
    ElMessage.success(`机器人 "${bot.bot_id}" 已停止`)
    fetchBots()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('停止失败: ' + (error.response?.data?.detail || '未知错误'))
    }
    // 无论成功或取消，都刷新列表以确保状态一致
    fetchBots()
  }
}

// 打开测试对话框
function openTestDialog(bot) {
  if (!bot.enabled) {
    ElMessage.warning('请先启动机器人后再进行测试')
    return
  }
  testBot.value = bot
  testStatus.value = 'waiting'
  testCountdown.value = 60
  testDialogVisible.value = true
  
  // 开始倒计时并等待消息
  startTestCountdown()
  waitForTestMessage()
}

// 测试倒计时
function startTestCountdown() {
  clearInterval(testCountdownTimer.value)
  testCountdownTimer.value = setInterval(() => {
    testCountdown.value--
    if (testCountdown.value <= 0) {
      clearInterval(testCountdownTimer.value)
      if (testStatus.value === 'waiting') {
        testStatus.value = 'timeout'
      }
    }
  }, 1000)
}

// 等待测试消息 - 优化版：快速检测 + 短超时
async function waitForTestMessage() {
  const startTime = Date.now()
  const maxWaitTime = 15000 // 15秒总超时（足够用户发送消息）
  const checkInterval = 1000 // 每秒检查一次
  
  // 先快速尝试一次（可能消息已经到达）
  try {
    const response = await axios.post(`/api/bots/${testBot.value.bot_id}/wait-message`, {}, {
      timeout: 3000 // 首次快速检测 3 秒
    })
    
    if (response.data.success) {
      testStatus.value = 'success'
      clearInterval(testCountdownTimer.value)
      ElMessage.success('连接测试成功！')
      return
    }
  } catch (error) {
    // 首次快速检测失败，继续轮询
  }
  
  // 轮询检测：每隔 1 秒检查一次，总共 15 秒
  while (Date.now() - startTime < maxWaitTime) {
    await new Promise(resolve => setTimeout(resolve, checkInterval))
    
    // 如果已经收到消息（通过其他方式检测到）
    if (testStatus.value === 'success') {
      return
    }
    
    // 尝试短连接检测
    try {
      const response = await axios.post(`/api/bots/${testBot.value.bot_id}/wait-message`, {}, {
        timeout: 2000 // 每次检测 2 秒
      })
      
      if (response.data.success) {
        testStatus.value = 'success'
        clearInterval(testCountdownTimer.value)
        ElMessage.success('连接测试成功！')
        return
      }
    } catch (error) {
      // 继续轮询
    }
  }
  
  // 超时
  if (testStatus.value !== 'success') {
    testStatus.value = 'timeout'
  }
}

// 重新测试
function restartTest() {
  testStatus.value = 'waiting'
  testCountdown.value = 60
  startTestCountdown()
  waitForTestMessage()
}

// 获取 notify URL
function getNotifyUrl(bot) {
  const host = window.location.hostname
  const port = window.location.port || '8899'
  return `http://${host}:${port}/notify?token=${bot.token}`
}

// 复制测试的 notify URL
function copyTestNotifyUrl() {
  const url = getNotifyUrl(testBot.value)
  navigator.clipboard.writeText(url).then(() => {
    ElMessage.success('URL 已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败，请手动复制')
  })
}

// 关闭测试对话框
function closeTestDialog() {
  testDialogVisible.value = false
  testBot.value = null
  clearInterval(testCountdownTimer.value)
}

// 开始企微测试（创建流程中）
async function startWecomTest() {
  if (!form.value.wecom_bot_id || !form.value.wecom_secret) {
    ElMessage.warning('请先填写 Bot ID 和 Secret')
    return
  }
  
  wecomTestPassed.value = false
  wecomTestFailed.value = false
  wecomTestCountdown.value = 60
  testingWecom.value = true
  
  // 开始倒计时
  clearInterval(wecomTestTimer.value)
  wecomTestTimer.value = setInterval(() => {
    wecomTestCountdown.value--
    if (wecomTestCountdown.value <= 0) {
      clearInterval(wecomTestTimer.value)
      if (!wecomTestPassed.value) {
        testingWecom.value = false
        wecomTestFailed.value = true
        wecomTestError.value = '等待超时，未在60秒内收到消息'
      }
    }
  }, 1000)
  
  try {
    // 调用 API 等待用户发送消息
    const response = await axios.post('/api/bots/test-wecom-wait', {
      bot_id: form.value.wecom_bot_id,
      secret: form.value.wecom_secret,
      timeout: 60
    }, {
      timeout: 70000
    })
    
    clearInterval(wecomTestTimer.value)
    
    if (response.data.success) {
      wecomTestPassed.value = true
      testingWecom.value = false
      // 保存 chatid 到表单，创建机器人时使用
      form.value.default_chatid = response.data.chatid
      ElMessage.success('连接测试成功！请检查企业微信消息')
    } else {
      testingWecom.value = false
      wecomTestFailed.value = true
      // 根据错误信息给出更友好的提示
      const msg = response.data.message || '测试失败'
      if (msg.startsWith('AUTH_FAILED:')) {
        // 认证失败 - Bot ID 或 Secret 错误
        wecomTestError.value = '企业微信认证失败，请检查：\n1. Bot ID 是否正确\n2. Secret 是否正确\n3. 机器人是否已在企业微信后台启用'
      } else if (msg.includes('超时')) {
        wecomTestError.value = '等待超时，未在60秒内收到消息，请重新测试并发送消息'
      } else if (msg.includes('网络') || msg.includes('连接')) {
        wecomTestError.value = '网络连接问题，请检查网络或稍后重试'
      } else {
        wecomTestError.value = msg
      }
    }
  } catch (error) {
    clearInterval(wecomTestTimer.value)
    if (!wecomTestPassed.value) {
      testingWecom.value = false
      wecomTestFailed.value = true
      wecomTestError.value = error.response?.data?.detail || error.response?.data?.message || '测试失败'
    }
  }
}

// 重新测试
function restartWecomTest() {
  wecomTestPassed.value = false
  wecomTestFailed.value = false
  startWecomTest()
}

// 重置表单
function resetForm() {
  form.value = {
    bot_id: '',
    description: '',
    wecom_bot_id: '',
    wecom_secret: '',
    default_chatid: '',  // 测试连接时获取的 chatid
    dify_api_base: '',
    dify_api_key: '',
    enabled: true
  }
  currentStep.value = 0
  createdNotifyUrl.value = ''
  wecomTestPassed.value = false
  wecomTestFailed.value = false
  clearInterval(wecomTestTimer.value)
}

// 自动刷新 - 2秒间隔，更快响应状态变化
onMounted(async () => {
  await fetchBots()
  // 立即获取一次连接状态
  await fetchConnectionStatus()
  // 每2秒刷新一次，平衡实时性和性能
  refreshTimer.value = setInterval(fetchConnectionStatus, 2000)
})

onUnmounted(() => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
  }
})
</script>

<style scoped>
.bot-manager {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.page-header h2 {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  color: #303133;
}

.subtitle {
  margin: 4px 0 0;
  color: #909399;
  font-size: 14px;
}

.stats-row {
  margin-bottom: 24px;
}

.stat-card {
  text-align: center;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transition: transform 0.3s, box-shadow 0.3s;
  border: none;
}

.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.stat-card.success {
  background: linear-gradient(135deg, #1a5fb4 0%, #0d3a7a 100%);
  color: white;
}

.stat-card.warning {
  background: linear-gradient(135deg, #e6a23c 0%, #c27a1a 100%);
  color: white;
}

.stat-card.info {
  background: linear-gradient(135deg, #67c23a 0%, #4a9c2d 100%);
  color: white;
}

.stat-value {
  font-size: 36px;
  font-weight: bold;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
}

.bot-list-card {
  margin-top: 24px;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  border: none;
}

.bot-list-card :deep(.el-card__header) {
  padding: 16px 20px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
}

.bot-table {
  width: 100%;
}

/* 行排序动画 */
.bot-table :deep(.el-table__body tr) {
  transition: all 0.4s ease;
}

.bot-table :deep(.el-table__header) {
  font-weight: 600;
}

.bot-table :deep(.el-table__cell) {
  vertical-align: middle;
  padding: 12px 8px;
}

.status-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.status-text {
  font-size: 13px;
  white-space: nowrap;
}

.connection-info {
  font-size: 13px;
  line-height: 1.6;
  color: #606266;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 500;
  color: #303133;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.action-buttons {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.action-btn {
  min-width: 70px;
}

.detail-btn {
  min-width: 60px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

/* Notify URL 样式 */
.notify-url-section {
  margin: 16px 0;
}

.url-display-box {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.url-text {
  flex: 1;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  word-break: break-all;
  color: #409eff;
}

.url-text.masked {
  color: #909399;
}

.url-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.url-hint {
  margin-top: 12px;
  font-size: 13px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
  transition: all 0.3s ease;
}

/* 连接成功 - 绿色 */
.status-dot.connected {
  background-color: #67c23a;
  box-shadow: 0 0 0 3px rgba(103, 194, 58, 0.2);
}

/* 连接失败 - 红色 */
.status-dot.error {
  background-color: #f56c6c;
  box-shadow: 0 0 0 3px rgba(245, 108, 108, 0.2);
}

/* 正在连接 - 蓝色闪烁 */
.status-dot.connecting {
  background-color: #409eff;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.2);
}

.status-dot.connecting.pulse {
  animation: pulse-blue 1.5s infinite;
}

/* 未启动/灰色 */
.status-dot.disconnected,
.status-dot.disabled,
.status-dot.unknown {
  background-color: #909399;
  box-shadow: none;
}

/* 蓝色脉冲动画 */
@keyframes pulse-blue {
  0%, 100% { 
    opacity: 1; 
    box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.2);
  }
  50% { 
    opacity: 0.6; 
    box-shadow: 0 0 0 6px rgba(64, 158, 255, 0.1);
  }
}

/* 通用脉冲动画 */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.connection-info {
  font-size: 12px;
  color: #666;
}

.no-data {
  color: #999;
}

.last-started-time {
  font-size: 13px;
  color: #606266;
  font-variant-numeric: tabular-nums;
}

.step-content {
  margin-top: 30px;
  min-height: 300px;
}

.finish-step {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.bot-details h3 {
  margin: 0 0 8px;
}

.bot-id {
  color: #666;
  font-size: 14px;
  margin: 0 0 16px;
}

.status-detail {
  margin-top: 16px;
}

.test-dialog-content {
  padding: 10px 0;
}

.test-instruction {
  font-size: 16px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.test-form {
  margin: 20px 0;
}

.notify-url-section {
  margin: 20px 0;
  max-width: 600px;
}

.test-connection-area {
  margin-top: 20px;
}

.test-waiting {
  text-align: center;
  padding: 20px 0;
}

.test-hint {
  margin-top: 15px;
  color: #909399;
  font-size: 14px;
}

.test-instruction-box {
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-top: 15px;
}

.test-instruction-box ol {
  margin: 15px 0;
  padding-left: 20px;
  line-height: 2;
}

.waiting-box {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-top: 20px;
  color: #e6a23c;
  font-weight: bold;
}

.success-text {
  color: #67c23a;
  margin: 5px 0;
}

.url-box {
  display: flex;
  align-items: center;
  margin: 10px 0;
  gap: 10px;
}

.url-label {
  min-width: 100px;
  text-align: right;
  color: #606266;
}

.url-input {
  flex: 1;
}
</style>
