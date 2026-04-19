<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
      <h2>机器人管理</h2>
      <el-button type="primary" @click="$router.push('/bots/create')">
        <el-icon><Plus /></el-icon> 创建机器人
      </el-button>
    </div>
    
    <el-table :data="bots" v-loading="loading" border>
      <el-table-column prop="bot_id" label="机器人ID" width="120" />
      <el-table-column prop="name" label="名称" width="150" />
      <el-table-column prop="description" label="描述" />
      <el-table-column prop="enabled" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.enabled ? 'success' : 'info'">
            {{ row.enabled ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="250">
        <template #default="{ row }">
          <el-button size="small" @click="toggleBot(row)">
            {{ row.enabled ? '禁用' : '启用' }}
          </el-button>
          <el-button size="small" type="primary" @click="$router.push(`/bots/edit/${row.bot_id}`)">
            编辑
          </el-button>
          <el-button size="small" type="danger" @click="deleteBot(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

const bots = ref([])
const loading = ref(false)

async function fetchBots() {
  loading.value = true
  try {
    const response = await axios.get('/api/bots')
    bots.value = response.data
  } catch (error) {
    ElMessage.error('获取机器人列表失败')
  } finally {
    loading.value = false
  }
}

async function toggleBot(bot) {
  try {
    await axios.post(`/api/bots/${bot.bot_id}/toggle`)
    ElMessage.success(`${bot.name} 已${bot.enabled ? '禁用' : '启用'}`)
    
    // 触发 Worker 强制同步，使状态变更立即生效
    try {
      await axios.post('/worker/sync')
    } catch (syncError) {
      // 同步接口失败不影响主流程，Worker 会在 5 秒内自动同步
      console.log('Worker sync triggered in background')
    }
    
    fetchBots()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

async function deleteBot(bot) {
  try {
    await ElMessageBox.confirm(
      `确定要删除机器人 "${bot.name}" 吗？`,
      '确认删除',
      { type: 'warning' }
    )
    await axios.delete(`/api/bots/${bot.bot_id}`)
    ElMessage.success('删除成功')
    fetchBots()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(fetchBots)
</script>
