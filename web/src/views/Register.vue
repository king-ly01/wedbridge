<template>
  <div class="register-page">
    <!-- 左侧品牌展示 -->
    <div class="brand-section">
      <div class="brand-content">
        <!-- 欢迎问候 -->
        <div class="welcome-greeting">
          <h2 class="greeting-title">🎉 欢迎加入</h2>
          <p class="greeting-subtitle">开启您的智能桥接之旅</p>
        </div>
        
        <!-- Logo 图标 -->
        <div class="logo-container">
          <div class="logo-icon">
            <svg viewBox="0 0 200 200" class="bridge-logo">
              <defs>
                <linearGradient id="bridgeGradReg" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style="stop-color:#ffffff;stop-opacity:1" />
                  <stop offset="100%" style="stop-color:#e0e7ff;stop-opacity:1" />
                </linearGradient>
              </defs>
              
              <!-- 外圈光环 -->
              <circle cx="100" cy="100" r="95" fill="none" stroke="url(#bridgeGradReg)" stroke-width="2" opacity="0.3"/>
              <circle cx="100" cy="100" r="85" fill="none" stroke="url(#bridgeGradReg)" stroke-width="1" opacity="0.5"/>
              
              <!-- 主桥拱 - 优雅的弧线 -->
              <path d="M 25 140 Q 100 60 175 140" fill="none" stroke="url(#bridgeGradReg)" stroke-width="8" stroke-linecap="round"/>
              
              <!-- 桥身横条 -->
              <rect x="20" y="135" width="160" height="10" rx="5" fill="url(#bridgeGradReg)"/>
              
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
    
    <!-- 右侧注册表单 -->
    <div class="form-section">
      <el-card class="register-card">
        <template #header>
          <div class="register-header">
            <h2 class="register-title">创建账号</h2>
            <p class="register-subtitle">填写以下信息完成注册</p>
          </div>
        </template>
        
        <el-form :model="form" :rules="rules" ref="formRef" class="register-form">
          <el-form-item prop="username">
            <el-input
              v-model="form.username"
              placeholder="用户名"
              :prefix-icon="User"
              size="large"
              class="register-input"
            />
          </el-form-item>
          
          <el-form-item prop="email">
            <el-input
              v-model="form.email"
              placeholder="邮箱"
              :prefix-icon="Message"
              size="large"
              class="register-input"
            />
          </el-form-item>
          
          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="密码"
              :prefix-icon="Lock"
              size="large"
              class="register-input"
              show-password
            />
          </el-form-item>
          
          <el-form-item prop="confirmPassword">
            <el-input
              v-model="form.confirmPassword"
              type="password"
              placeholder="确认密码"
              :prefix-icon="Lock"
              size="large"
              class="register-input"
              show-password
              @keyup.enter="handleRegister"
            />
          </el-form-item>
          
          <el-form-item>
            <el-button
              type="primary"
              size="large"
              :loading="loading"
              @click="handleRegister"
              class="register-button"
            >
              创建账号
            </el-button>
          </el-form-item>
          
          <div class="register-links">
            <span class="text-gray">已有账号？</span>
            <router-link to="/login" class="login-link">立即登录</router-link>
          </div>
        </el-form>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, Lock, Message, Connection, Cpu, Lightning } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref()
const loading = ref(false)

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const validatePass2 = (rule, value, callback) => {
  if (value !== form.password) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validatePass2, trigger: 'blur' }
  ]
}

async function handleRegister() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  
  loading.value = true
  try {
    await authStore.register(form.username, form.email, form.password)
    
    // 显示注册成功提示，然后跳转到登录页
    ElMessageBox.alert(
      `用户 "${form.username}" 注册成功！\n\n请使用您的邮箱和密码登录。`,
      '注册成功',
      {
        confirmButtonText: '去登录',
        type: 'success',
        callback: () => {
          router.push({
            path: '/login',
            query: { email: form.email }
          })
        }
      }
    )
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  background: #f5f7fa;
}

/* 左侧品牌区域 */
.brand-section {
  flex: 1;
  background: linear-gradient(135deg, #1a5fb4 0%, #0d3a7a 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  position: relative;
  overflow: hidden;
}

.brand-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.03'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
  opacity: 0.5;
}

.brand-content {
  position: relative;
  z-index: 1;
  max-width: 500px;
  color: white;
  text-align: center;
}

.welcome-greeting {
  margin-bottom: 40px;
}

.greeting-title {
  font-size: 32px;
  font-weight: 600;
  margin: 0 0 10px 0;
}

.greeting-subtitle {
  font-size: 18px;
  opacity: 0.9;
  margin: 0;
}

.logo-container {
  margin-bottom: 50px;
}

.logo-icon {
  width: 120px;
  height: 120px;
  margin: 0 auto 20px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.bridge-logo {
  width: 80px;
  height: 80px;
}

.brand-name {
  font-size: 42px;
  font-weight: 700;
  margin: 0 0 10px 0;
  letter-spacing: 2px;
  font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
}

.brand-slogan {
  font-size: 16px;
  opacity: 0.8;
  margin: 0;
}

.features {
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: center;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 15px;
  opacity: 0.9;
}

.feature-icon {
  font-size: 20px;
  color: #67c23a;
}

/* 右侧表单区域 */
.form-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: #ffffff;
}

.register-card {
  width: 100%;
  max-width: 420px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: none;
}

.register-card :deep(.el-card__header) {
  background: transparent;
  border-bottom: 1px solid #ebeef5;
  padding: 30px 30px 20px;
}

.register-header {
  text-align: center;
}

.register-title {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.register-subtitle {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.register-form {
  padding: 20px 10px;
}

.register-input :deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px #dcdfe6 inset;
}

.register-input :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #1a5fb4 inset;
}

.register-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #1a5fb4 inset;
}

.register-button {
  width: 100%;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  height: 44px;
  background: linear-gradient(135deg, #1a5fb4 0%, #0d3a7a 100%);
  border: none;
  transition: all 0.3s;
}

.register-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(26, 95, 180, 0.4);
}

.register-links {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
}

.text-gray {
  color: #909399;
}

.login-link {
  color: #1a5fb4;
  text-decoration: none;
  font-weight: 500;
  margin-left: 4px;
}

.login-link:hover {
  text-decoration: underline;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .register-page {
    flex-direction: column;
  }
  
  .brand-section {
    padding: 30px 20px;
    min-height: 300px;
  }
  
  .brand-name {
    font-size: 32px;
  }
  
  .form-section {
    padding: 30px 20px;
  }
  
  .register-card {
    max-width: 100%;
  }
}
</style>
