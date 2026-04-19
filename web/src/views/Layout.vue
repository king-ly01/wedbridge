<template>
  <el-container class="layout-container">
    <el-aside width="200px" class="sidebar">
          <div class="logo">
            <h3>WEDBRIDGE</h3>
          </div>
          <el-menu
            :default-active="$route.path"
            router
            class="sidebar-menu"
            background-color="#304156"
            text-color="#bfcbd9"
            active-text-color="#409EFF"
          >
            <el-menu-item index="/dashboard">
              <el-icon><HomeFilled /></el-icon>
              <span>控制台</span>
            </el-menu-item>
            <el-menu-item index="/bots">
              <el-icon><ChatDotRound /></el-icon>
              <span>机器人管理</span>
            </el-menu-item>
          </el-menu>
        </el-aside>
        
        <el-container>
          <el-header class="header">
            <div class="header-right">
              <!-- 问候语 -->
              <div class="greeting">
                <span class="greeting-text">{{ greeting }}</span>
              </div>
              <el-dropdown @command="handleCommand" trigger="click">
                <div class="user-info">
                  <el-avatar 
                    :size="32" 
                    :src="userAvatar" 
                    class="user-avatar"
                  >
                    {{ userInitials }}
                  </el-avatar>
                  <span class="username">{{ authStore.user?.username }}</span>
                  <el-icon class="el-icon--right"><arrow-down /></el-icon>
                </div>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="profile">
                      <el-icon><User /></el-icon>个人信息
                    </el-dropdown-item>
                    <el-dropdown-item command="switch">
                      <el-icon><Switch /></el-icon>切换用户
                    </el-dropdown-item>
                    <el-dropdown-item divided command="logout">
                      <el-icon><SwitchButton /></el-icon>退出登录
                    </el-dropdown-item>
                    <el-dropdown-item command="delete-account" class="delete-account-item">
                      <el-icon><Delete /></el-icon>注销账户
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </el-header>
          
          <el-main class="main-content">
            <router-view />
          </el-main>
        </el-container>
      </el-container>
  
  <!-- 用户信息对话框 -->
  <el-dialog
    v-model="profileVisible"
    title="个人信息"
    width="450px"
  >
    <div class="profile-content">
      <!-- 头像选择和上传区域 -->
      <div class="avatar-section">
        <div class="current-avatar">
          <el-avatar :size="80" :src="previewAvatar || userAvatar">{{ userInitials }}</el-avatar>
          <div class="avatar-actions">
            <el-button type="primary" size="small" @click="showAvatarSelector = true">
              <el-icon><Picture /></el-icon> 选择头像
            </el-button>
            <el-upload
              class="avatar-upload"
              action="#"
              :auto-upload="false"
              :show-file-list="false"
              :on-change="handleAvatarChange"
              accept="image/*"
            >
              <el-button type="success" size="small">
                <el-icon><Upload /></el-icon> 上传图片
              </el-button>
            </el-upload>
          </div>
        </div>
        
        <!-- 预设头像选择器 -->
        <div v-if="showAvatarSelector" class="avatar-selector">
          <div class="preset-avatars">
            <div
              v-for="(avatar, index) in presetAvatars"
              :key="index"
              class="preset-avatar-item"
              :class="{ selected: selectedPresetAvatar === avatar }"
              @click="selectPresetAvatar(avatar)"
            >
              <el-avatar :size="50" :src="avatar" />
            </div>
          </div>
          <div class="avatar-selector-actions">
            <el-button size="small" @click="showAvatarSelector = false">取消</el-button>
            <el-button type="primary" size="small" @click="confirmAvatarChange">确认</el-button>
          </div>
        </div>
        
        <!-- 上传预览 -->
        <div v-if="uploadedAvatar" class="upload-preview">
          <p>图片预览：</p>
          <el-avatar :size="60" :src="uploadedAvatar" />
          <div class="upload-actions">
            <el-button size="small" @click="uploadedAvatar = null">取消</el-button>
            <el-button type="primary" size="small" @click="confirmUploadAvatar">确认使用</el-button>
          </div>
        </div>
      </div>
      
      <el-descriptions :column="1" border>
        <el-descriptions-item label="用户名">{{ authStore.user?.username }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ authStore.user?.email || '未设置' }}</el-descriptions-item>
        <el-descriptions-item label="用户ID">{{ authStore.user?.id }}</el-descriptions-item>
        <el-descriptions-item label="注册时间">{{ formatDate(authStore.user?.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag v-if="authStore.user?.is_active" type="success">正常</el-tag>
          <el-tag v-else type="danger">禁用</el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </div>
  </el-dialog>
  
  <!-- 退出登录确认对话框 -->
  <el-dialog
    v-model="logoutVisible"
    title="确认退出登录"
    width="400px"
  >
    <p>确定要退出当前账号吗？</p>
    <template #footer>
      <el-button @click="logoutVisible = false">取消</el-button>
      <el-button type="danger" @click="confirmLogout">确认退出</el-button>
    </template>
  </el-dialog>

  <!-- 注销账户确认对话框 -->
  <el-dialog
    v-model="deleteAccountVisible"
    title="⚠️ 危险操作：注销账户"
    width="500px"
    :close-on-click-modal="false"
    :show-close="false"
    class="delete-account-dialog"
  >
    <div class="delete-account-warning">
      <el-alert
        title="此操作不可恢复！"
        type="error"
        :closable="false"
        show-icon
      >
        <template #default>
          <div style="margin-top: 10px;">
            <p><strong>注销账户将导致以下后果：</strong></p>
            <ul style="margin: 10px 0; padding-left: 20px; line-height: 2;">
              <li>您的账户信息将被永久删除</li>
              <li>所有关联的机器人将被删除</li>
              <li>所有配置和数据将无法恢复</li>
              <li>此操作立即生效，无法撤销</li>
            </ul>
          </div>
        </template>
      </el-alert>

      <div class="confirm-input-section">
        <p style="margin-bottom: 15px;">
          请输入 <strong style="color: #f56c6c;">DELETE</strong> 以确认注销账户：
        </p>
        <el-input
          v-model="deleteAccountConfirm"
          placeholder="请输入 DELETE"
          size="large"
          :input-style="{ textTransform: 'uppercase' }"
        />
      </div>
    </div>

    <template #footer>
      <el-button @click="closeDeleteAccountDialog" :disabled="deletingAccount">取消</el-button>
      <el-button 
        type="danger" 
        @click="confirmDeleteAccount" 
        :disabled="deleteAccountConfirm !== 'DELETE' || deletingAccount"
        :loading="deletingAccount"
      >
        我了解风险，确认注销
      </el-button>
    </template>
  </el-dialog>

  <!-- 切换用户对话框 -->
  <el-dialog
    v-model="switchVisible"
    title="切换用户"
    width="420px"
  >
    <div v-if="savedUsers.length > 0">
      <p style="margin-bottom: 15px;">选择之前登录过的用户：</p>
      <div class="saved-users-list">
        <div 
          v-for="user in savedUsers" 
          :key="user.email"
          class="user-item"
          :class="{ 'selected': selectedUser === user.email }"
          @click="selectedUser = user.email"
        >
          <div class="user-info">
            <el-avatar :size="36" :src="`https://api.dicebear.com/7.x/avataaars/svg?seed=${user.username}&backgroundColor=b6e3f4`">
              {{ user.username.charAt(0).toUpperCase() }}
            </el-avatar>
            <div class="user-details">
              <div class="username">{{ user.username }}</div>
              <div class="email">{{ user.email || '无邮箱' }}</div>
            </div>
          </div>
          <div class="user-actions">
            <el-radio :label="user.email" v-model="selectedUser">
              <span></span>
            </el-radio>
            <el-button 
              type="danger" 
              link 
              size="small"
              @click.stop="removeSavedUser(user.email)"
              title="删除此用户记录"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </div>
    <el-empty v-else description="没有保存的登录用户" />
    
    <el-divider />
    
    <el-button type="primary" @click="loginAsNewUser" style="width: 100%;">
      <el-icon><Plus /></el-icon> 登录新用户
    </el-button>
    
    <template #footer v-if="savedUsers.length > 0">
      <el-button @click="switchVisible = false">取消</el-button>
      <el-button type="primary" @click="confirmSwitch" :disabled="!selectedUser">切换</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import { HomeFilled, ChatDotRound, User, Switch, SwitchButton, ArrowDown, Plus, Delete, Picture, Upload } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const profileVisible = ref(false)
const switchVisible = ref(false)
const logoutVisible = ref(false)
const deleteAccountVisible = ref(false)
const deleteAccountConfirm = ref('')
const deletingAccount = ref(false)
const selectedUser = ref('')

// 头像相关
const showAvatarSelector = ref(false)
const selectedPresetAvatar = ref('')
const uploadedAvatar = ref('')
const previewAvatar = ref('')

// 预设头像列表（使用 DiceBear 生成多种风格）
const presetAvatars = [
  'https://api.dicebear.com/7.x/avataaars/svg?seed=Felix&backgroundColor=b6e3f4',
  'https://api.dicebear.com/7.x/avataaars/svg?seed=Aneka&backgroundColor=c0aede',
  'https://api.dicebear.com/7.x/avataaars/svg?seed=Zack&backgroundColor=ffdfbf',
  'https://api.dicebear.com/7.x/avataaars/svg?seed=Bella&backgroundColor=ffdfbf',
  'https://api.dicebear.com/7.x/avataaars/svg?seed=Leo&backgroundColor=b6e3f4',
  'https://api.dicebear.com/7.x/avataaars/svg?seed=Molly&backgroundColor=c0aede',
  'https://api.dicebear.com/7.x/avataaars/svg?seed=Max&backgroundColor=ffdfbf',
  'https://api.dicebear.com/7.x/avataaars/svg?seed=Luna&backgroundColor=b6e3f4',
  'https://api.dicebear.com/7.x/bottts/svg?seed=Robot1&backgroundColor=b6e3f4',
  'https://api.dicebear.com/7.x/bottts/svg?seed=Robot2&backgroundColor=c0aede',
  'https://api.dicebear.com/7.x/identicon/svg?seed=User1&backgroundColor=b6e3f4',
  'https://api.dicebear.com/7.x/identicon/svg?seed=User2&backgroundColor=c0aede'
]

// 从 localStorage 获取保存的用户列表
const savedUsers = ref([])
function loadSavedUsers() {
  const users = localStorage.getItem('saved_users')
  if (users) {
    savedUsers.value = JSON.parse(users)
  }
}

// 保存当前用户到列表
function saveCurrentUser() {
  if (!authStore.user) return
  
  const existingIndex = savedUsers.value.findIndex(u => u.username === authStore.user.username)
  const userInfo = {
    username: authStore.user.username,
    email: authStore.user.email,
    savedAt: new Date().toISOString()
  }
  
  if (existingIndex >= 0) {
    savedUsers.value[existingIndex] = userInfo
  } else {
    savedUsers.value.push(userInfo)
  }
  
  // 最多保存 5 个用户
  if (savedUsers.value.length > 5) {
    savedUsers.value.shift()
  }
  
  localStorage.setItem('saved_users', JSON.stringify(savedUsers.value))
}

// 用户头像（优先使用用户设置的，否则使用 DiceBear 生成）
const userAvatar = computed(() => {
  // 如果用户设置了头像，使用用户头像
  if (authStore.user?.avatar) {
    return authStore.user.avatar
  }
  // 否则使用默认的 DiceBear 头像
  const username = authStore.user?.username || 'user'
  return `https://api.dicebear.com/7.x/avataaars/svg?seed=${username}&backgroundColor=b6e3f4`
})

// 用户名字首字母
const userInitials = computed(() => {
  const username = authStore.user?.username || 'U'
  return username.charAt(0).toUpperCase()
})

// 问候语列表
const greetings = [
  '今天也要开心呀~',
  '愿你有个美好的一天！',
  '加油，你是最棒的！',
  '记得按时吃饭哦~',
  '今天也要元气满满！',
  '愿你工作顺利！',
  '保持好心情，万事皆顺意~',
  '又是充满希望的一天！',
  '相信自己，你可以的！',
  '愿你被世界温柔以待~'
]

// 根据用户名和时间生成固定的问候语（保证同一会话中不变）
const greeting = computed(() => {
  const username = authStore.user?.username || '朋友'
  const hour = new Date().getHours()
  let timeGreeting = ''
  
  if (hour < 6) {
    timeGreeting = '夜深了，注意休息~'
  } else if (hour < 9) {
    timeGreeting = '早上好，开启美好一天！'
  } else if (hour < 12) {
    timeGreeting = '上午好，工作顺利！'
  } else if (hour < 14) {
    timeGreeting = '中午好，记得吃饭~'
  } else if (hour < 18) {
    timeGreeting = '下午好，继续加油！'
  } else {
    timeGreeting = '晚上好，辛苦了！'
  }
  
  // 根据用户名选择一条固定的随机问候
  const randomIndex = username.split('').reduce((sum, char) => sum + char.charCodeAt(0), 0) % greetings.length
  const randomGreeting = greetings[randomIndex]
  
  return `${username}，${timeGreeting} ${randomGreeting}`
})

function handleCommand(command) {
  switch (command) {
    case 'logout':
      logoutVisible.value = true
      break
    case 'profile':
      profileVisible.value = true
      break
    case 'switch':
      loadSavedUsers()
      selectedUser.value = ''
      switchVisible.value = true
      break
    case 'delete-account':
      deleteAccountVisible.value = true
      break
  }
}

function confirmLogout() {
  saveCurrentUser()
  authStore.logout()
  logoutVisible.value = false
  ElMessage.success('已退出登录')
  router.push('/login')
}

function loginAsNewUser() {
  saveCurrentUser()
  authStore.logout()
  switchVisible.value = false
  router.push('/login')
}

async function confirmSwitch() {
  if (!selectedUser.value) {
    ElMessage.warning('请选择要切换的用户')
    return
  }
  
  const user = savedUsers.value.find(u => u.email === selectedUser.value)
  if (!user) {
    ElMessage.error('用户不存在')
    return
  }
  
  // 保存当前用户
  saveCurrentUser()
  
  // 退出当前用户
  authStore.logout()
  switchVisible.value = false
  
  // 跳转到登录页并带上邮箱
  router.push({
    path: '/login',
    query: { email: user.email }
  })
  
  ElMessage.success(`请为 ${user.email} 输入密码登录`)
}

// 删除保存的用户记录
function removeSavedUser(email) {
  const index = savedUsers.value.findIndex(u => u.email === email)
  if (index > -1) {
    savedUsers.value.splice(index, 1)
    localStorage.setItem('saved_users', JSON.stringify(savedUsers.value))
    
    // 如果删除的是当前选中的，清空选择
    if (selectedUser.value === email) {
      selectedUser.value = ''
    }
    
    ElMessage.success('用户记录已删除')
  }
}

// 关闭注销账户对话框
function closeDeleteAccountDialog() {
  deleteAccountVisible.value = false
  deleteAccountConfirm.value = ''
}

// 确认注销账户
async function confirmDeleteAccount() {
  if (deleteAccountConfirm.value !== 'DELETE') {
    ElMessage.warning('请输入 DELETE 以确认注销')
    return
  }
  
  deletingAccount.value = true
  try {
    await axios.delete('/api/auth/me')
    ElMessage.success('账户已注销')
    
    // 清除登录状态
    authStore.logout()
    
    // 从保存的用户列表中移除
    const users = JSON.parse(localStorage.getItem('saved_users') || '[]')
    const filtered = users.filter(u => u.username !== authStore.user?.username)
    localStorage.setItem('saved_users', JSON.stringify(filtered))
    
    // 跳转到登录页
    router.push('/login')
  } catch (error) {
    ElMessage.error('注销失败: ' + (error.response?.data?.detail || '未知错误'))
  } finally {
    deletingAccount.value = false
    closeDeleteAccountDialog()
  }
}

function formatDate(dateStr) {
  if (!dateStr) return '未知'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// ============ 头像相关函数 ============

// 选择预设头像
function selectPresetAvatar(avatar) {
  selectedPresetAvatar.value = avatar
  previewAvatar.value = avatar
}

// 确认使用预设头像
async function confirmAvatarChange() {
  if (!selectedPresetAvatar.value) {
    ElMessage.warning('请先选择一个头像')
    return
  }
  
  await updateAvatar(selectedPresetAvatar.value)
  showAvatarSelector.value = false
  selectedPresetAvatar.value = ''
  previewAvatar.value = ''
}

// 处理文件上传
function handleAvatarChange(file) {
  const isImage = file.raw.type.startsWith('image/')
  if (!isImage) {
    ElMessage.error('请上传图片文件')
    return
  }
  
  const isLt2M = file.raw.size / 1024 / 1024 < 2
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB')
    return
  }
  
  // 读取文件为 base64
  const reader = new FileReader()
  reader.readAsDataURL(file.raw)
  reader.onload = () => {
    uploadedAvatar.value = reader.result
    previewAvatar.value = reader.result
    showAvatarSelector.value = false
  }
}

// 确认使用上传的头像
async function confirmUploadAvatar() {
  if (!uploadedAvatar.value) {
    ElMessage.warning('请先上传图片')
    return
  }
  
  await updateAvatar(uploadedAvatar.value)
  uploadedAvatar.value = ''
  previewAvatar.value = ''
}

// 更新头像到服务器
async function updateAvatar(avatarUrl) {
  try {
    await axios.put('/api/user/avatar', { avatar: avatarUrl })
    // 使用 store 方法更新本地用户（会同步到 localStorage）
    authStore.updateUser({ avatar: avatarUrl })
    ElMessage.success('头像更新成功')
  } catch (error) {
    ElMessage.error('头像更新失败: ' + (error.response?.data?.detail || '未知错误'))
  }
}

// 页面加载时刷新用户信息（获取最新头像）
onMounted(() => {
  // 延迟一点执行，避免页面加载时的闪烁
  setTimeout(() => {
    authStore.refreshUser()
  }, 500)
})
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.sidebar {
  background-color: #304156;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  border-bottom: 1px solid #1f2d3d;
}

.logo h3 {
  margin: 0;
}

.sidebar-menu {
  border-right: none;
}

.header {
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0,21,41,.08);
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.greeting {
  font-size: 14px;
  color: #606266;
}

.greeting-text {
  font-weight: 500;
}

.user-info {
  cursor: pointer;
  color: #606266;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 10px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-info:hover {
  background-color: #f5f7fa;
}

.user-avatar {
  border: 2px solid #e4e7ed;
}

.username {
  font-size: 14px;
  font-weight: 500;
}

.profile-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.profile-avatar {
  margin-bottom: 10px;
}

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
}

.delete-account-item {
  color: #f56c6c !important;
}

.delete-account-item:hover {
  background-color: #fef0f0 !important;
  color: #f56c6c !important;
}

.delete-account-warning {
  padding: 10px 0;
}

.confirm-input-section {
  margin-top: 25px;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

/* 切换用户对话框样式 */
.saved-users-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.user-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.user-item:hover {
  border-color: #409eff;
  background-color: #f5f7fa;
}

.user-item.selected {
  border-color: #409eff;
  background-color: #ecf5ff;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.user-details .username {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}

.user-details .email {
  font-size: 12px;
  color: #909399;
}

.user-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 头像选择和上传样式 */
.avatar-section {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  padding: 20px 0;
  border-bottom: 1px solid #e4e7ed;
  margin-bottom: 20px;
}

.current-avatar {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.avatar-actions {
  display: flex;
  gap: 10px;
}

.avatar-upload {
  display: inline-block;
}

.avatar-selector {
  width: 100%;
  background-color: #f5f7fa;
  border-radius: 8px;
  padding: 15px;
  margin-top: 10px;
}

.preset-avatars {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 10px;
  margin-bottom: 15px;
}

.preset-avatar-item {
  cursor: pointer;
  padding: 5px;
  border-radius: 8px;
  transition: all 0.3s;
  display: flex;
  justify-content: center;
}

.preset-avatar-item:hover {
  background-color: #e4e7ed;
}

.preset-avatar-item.selected {
  background-color: #409eff;
}

.avatar-selector-actions {
  display: flex;
  justify-content: center;
  gap: 10px;
}

.upload-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 15px;
  background-color: #f0f9ff;
  border-radius: 8px;
  border: 1px dashed #409eff;
}

.upload-preview p {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.upload-actions {
  display: flex;
  gap: 10px;
  margin-top: 5px;
}
</style>
