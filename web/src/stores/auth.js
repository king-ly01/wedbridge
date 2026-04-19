import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || '/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  
  const isLoggedIn = computed(() => !!token.value)
  
  // 设置 axios 默认 header
  if (token.value) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
  }
  
  async function login(email, password) {
    const response = await axios.post(`${API_URL}/auth/login`, {
      email,
      password
    })
    
    token.value = response.data.access_token
    user.value = response.data.user
    
    localStorage.setItem('token', token.value)
    localStorage.setItem('user', JSON.stringify(user.value))
    
    axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
    
    return response.data
  }
  
  async function register(username, email, password) {
    const response = await axios.post(`${API_URL}/auth/register`, {
      username,
      email,
      password
    })
    return response.data
  }
  
  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    delete axios.defaults.headers.common['Authorization']
  }
  
  // 从服务器刷新用户信息（获取最新头像等）
  async function refreshUser() {
    if (!token.value) return
    try {
      const response = await axios.get(`${API_URL}/auth/me`)
      user.value = response.data
      localStorage.setItem('user', JSON.stringify(user.value))
      return user.value
    } catch (error) {
      console.error('刷新用户信息失败:', error)
      return null
    }
  }
  
  // 更新本地用户信息
  function updateUser(userData) {
    user.value = { ...user.value, ...userData }
    localStorage.setItem('user', JSON.stringify(user.value))
  }
  
  return {
    token,
    user,
    isLoggedIn,
    login,
    register,
    logout,
    refreshUser,
    updateUser
  }
})
