import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { public: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { public: true }
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('../views/Layout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '控制台' }
      },
      {
        path: 'bots',
        name: 'Bots',
        component: () => import('../views/BotManager.vue'),
        meta: { title: '机器人管理' }
      },
      {
        path: 'bots/create',
        name: 'CreateBot',
        component: () => import('../views/BotForm.vue'),
        meta: { title: '创建机器人' }
      },
      {
        path: 'bots/edit/:id',
        name: 'EditBot',
        component: () => import('../views/BotForm.vue'),
        meta: { title: '编辑机器人' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (!to.meta.public && !authStore.token) {
    next('/login')
  } else if ((to.path === '/login' || to.path === '/register') && authStore.token) {
    next('/')
  } else {
    next()
  }
})

export default router
