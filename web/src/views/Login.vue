<template>
  <div class="login-container">
    <!-- 左侧品牌展示 -->
    <div class="brand-section">
      <div class="brand-content">
        <!-- 欢迎问候 -->
        <div class="welcome-greeting">
          <h2 class="greeting-title">👋 欢迎使用</h2>
          <p class="greeting-subtitle">开启您的智能桥接之旅</p>
        </div>
        
        <!-- Logo 图标 -->
        <div class="logo-container">
          <div class="logo-icon">
            <svg viewBox="0 0 200 200" class="bridge-logo">
              <defs>
                <linearGradient id="bridgeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style="stop-color:#ffffff;stop-opacity:1" />
                  <stop offset="100%" style="stop-color:#e0e7ff;stop-opacity:1" />
                </linearGradient>
                <linearGradient id="flowGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" style="stop-color:#67c23a" />
                  <stop offset="50%" style="stop-color:#409eff" />
                  <stop offset="100%" style="stop-color:#e6a23c" />
                </linearGradient>
              </defs>
              
              <!-- 外圈光环 -->
              <circle cx="100" cy="100" r="95" fill="none" stroke="url(#bridgeGrad)" stroke-width="2" opacity="0.3"/>
              <circle cx="100" cy="100" r="85" fill="none" stroke="url(#bridgeGrad)" stroke-width="1" opacity="0.5"/>
              
              <!-- 主桥拱 - 优雅的弧线 -->
              <path d="M 25 140 Q 100 60 175 140" fill="none" stroke="url(#bridgeGrad)" stroke-width="8" stroke-linecap="round"/>
              
              <!-- 桥身横条 -->
              <rect x="20" y="135" width="160" height="10" rx="5" fill="url(#bridgeGrad)"/>
              
              <!-- 垂直支撑柱 -->
              <rect x="55" y="105" width="6" height="35" rx="3" fill="white" opacity="0.9"/>
              <rect x="97" y="85" width="6" height="55" rx="3" fill="white" opacity="0.9"/>
              <rect x="139" y="105" width="6" height="35" rx="3" fill="white" opacity="0.9"/>
              
              <!-- 数据流动线条 - 左到右 -->
              <path d="M 35 125 Q 65 115 95 120" fill="none" stroke="#67c23a" stroke-width="3" stroke-linecap="round" opacity="0.9">
                <animate attributeName="stroke-dasharray" values="0,20;20,0" dur="1.5s" repeatCount="indefinite"/>
              </path>
              <path d="M 95 120 Q 125 125 155 118" fill="none" stroke="#409eff" stroke-width="3" stroke-linecap="round" opacity="0.9">
                <animate attributeName="stroke-dasharray" values="0,20;20,0" dur="1.5s" begin="0.5s" repeatCount="indefinite"/>
              </path>
              
              <!-- 节点圆点 -->
              <circle cx="35" cy="125" r="6" fill="#67c23a"/>
              <circle cx="97" cy="100" r="8" fill="#409eff"/>
              <circle cx="160" cy="122" r="6" fill="#e6a23c"/>
              
              <!-- 连接点光晕 -->
              <circle cx="97" cy="100" r="12" fill="none" stroke="#409eff" stroke-width="2" opacity="0.5">
                <animate attributeName="r" values="12;16;12" dur="2s" repeatCount="indefinite"/>
                <animate attributeName="opacity" values="0.5;0.2;0.5" dur="2s" repeatCount="indefinite"/>
              </circle>
              
              <!-- 底部装饰线 -->
              <line x1="40" y1="155" x2="160" y2="155" stroke="white" stroke-width="2" opacity="0.4" stroke-linecap="round"/>
            </svg>
          </div>
          <h1 class="brand-name">WEDBRIDGE</h1>
          <p class="brand-slogan">连接企业微信与 Dify AI 的智能桥梁</p>
        </div>
        
        <!-- 特性展示 -->
        <div class="features">
          <div class="feature-item">
            <el-icon class="feature-icon"><Connection /></el-icon>
            <span>无缝连接 WeCom 与 Dify</span>
          </div>
          <div class="feature-item">
            <el-icon class="feature-icon"><Cpu /></el-icon>
            <span>支持数百个机器人同时运行</span>
          </div>
          <div class="feature-item">
            <el-icon class="feature-icon"><Lightning /></el-icon>
            <span>实时消息转发，秒级响应</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 右侧登录表单 -->
    <div class="form-section">
      <el-card class="login-card">
        <template #header>
          <div class="login-header">
            <h2 class="login-title">欢迎回来</h2>
            <p class="login-subtitle">请登录您的账户</p>
          </div>
        </template>
        
        <el-form :model="form" :rules="rules" ref="formRef" class="login-form">
          <el-form-item prop="email">
            <el-input
              v-model="form.email"
              placeholder="邮箱"
              :prefix-icon="Message"
              size="large"
              class="login-input"
            />
          </el-form-item>
          
          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="密码"
              :prefix-icon="Lock"
              size="large"
              class="login-input"
              @keyup.enter="handleLogin"
            />
          </el-form-item>
          
          <el-form-item>
            <el-button
              type="primary"
              size="large"
              :loading="loading"
              @click="handleLogin"
              class="login-button"
            >
              <el-icon class="button-icon"><ArrowRight /></el-icon>
              登录
            </el-button>
          </el-form-item>
          
          <div class="login-links">
            <span class="no-account">还没有账户？</span>
            <router-link to="/register" class="register-link">立即注册</router-link>
          </div>
        </el-form>
      </el-card>
      
      <!-- 底部版权 -->
      <div class="footer">
        <p>© 2024 WEDBRIDGE. All rights reserved.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Message, Lock, Connection, Cpu, Lightning, ArrowRight } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const formRef = ref()
const loading = ref(false)

const form = reactive({
  email: '',
  password: ''
})

// 从 URL 参数获取邮箱（切换用户时传入）
onMounted(() => {
  if (route.query.email) {
    form.email = route.query.email
  }
})

const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function handleLogin() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  
  loading.value = true
  try {
    await authStore.login(form.email, form.password)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 左侧品牌区域 */
.brand-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  position: relative;
  overflow: hidden;
}

.brand-section::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 1px, transparent 1px);
  background-size: 30px 30px;
  opacity: 0.5;
}

.brand-content {
  position: relative;
  z-index: 1;
  text-align: center;
  color: white;
}

/* 欢迎问候 */
.welcome-greeting {
  margin-bottom: 30px;
}

.greeting-title {
  font-size: 36px;
  font-weight: 700;
  margin: 0 0 10px 0;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
  animation: fadeInDown 0.8s ease-out;
}

.greeting-subtitle {
  font-size: 18px;
  margin: 0;
  opacity: 0.9;
  font-weight: 300;
  animation: fadeInUp 0.8s ease-out 0.3s both;
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.logo-container {
  margin-bottom: 40px;
}

.logo-icon {
  width: 180px;
  height: 180px;
  margin: 0 auto 30px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.bridge-logo {
  width: 120px;
  height: 120px;
}

.brand-name {
  font-size: 48px;
  font-weight: 800;
  margin: 0 0 15px 0;
  letter-spacing: 4px;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
}

.brand-slogan {
  font-size: 18px;
  margin: 0;
  opacity: 0.9;
  font-weight: 300;
}

/* 特性列表 */
.features {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-top: 40px;
}

.feature-item {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-size: 16px;
  padding: 12px 24px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 30px;
  backdrop-filter: blur(5px);
  transition: transform 0.3s, background 0.3s;
}

.feature-item:hover {
  transform: translateX(5px);
  background: rgba(255, 255, 255, 0.2);
}

.feature-icon {
  font-size: 20px;
}

/* 右侧表单区域 */
.form-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
}

.login-card {
  width: 100%;
  max-width: 420px;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.login-card :deep(.el-card__header) {
  padding: 30px 30px 20px;
  border-bottom: none;
}

.login-header {
  text-align: center;
}

.login-title {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  margin: 0 0 8px 0;
}

.login-subtitle {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.login-form {
  padding: 20px 30px 30px;
}

.login-input :deep(.el-input__wrapper) {
  border-radius: 10px;
  padding: 8px 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.login-button {
  width: 100%;
  border-radius: 10px;
  padding: 15px;
  font-size: 16px;
  font-weight: 600;
  margin-top: 10px;
  background: linear-gradient(135deg, #409eff 0%, #1677ff 100%);
  border: none;
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.4);
  transition: transform 0.3s, box-shadow 0.3s;
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(64, 158, 255, 0.5);
}

.button-icon {
  margin-right: 8px;
}

.login-links {
  text-align: center;
  margin-top: 25px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.no-account {
  color: #909399;
  font-size: 14px;
}

.register-link {
  color: #409eff;
  font-weight: 600;
  margin-left: 5px;
  text-decoration: none;
  transition: color 0.3s;
}

.register-link:hover {
  color: #1677ff;
}

/* 底部版权 */
.footer {
  margin-top: 40px;
  text-align: center;
  color: #909399;
  font-size: 12px;
}

/* 响应式设计 */
@media (max-width: 900px) {
  .brand-section {
    display: none;
  }
  
  .form-section {
    flex: 1;
    padding: 40px 20px;
  }
}
</style>
