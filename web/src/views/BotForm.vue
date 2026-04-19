<template>
  <div>
    <h2>{{ isEdit ? '编辑机器人' : '创建机器人' }}</h2>
    
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="150px"
      style="max-width: 800px; margin-top: 20px;"
    >
      <el-divider>基本信息</el-divider>
      
      <el-form-item label="机器人ID" prop="bot_id">
        <el-input v-model="form.bot_id" :disabled="isEdit" placeholder="唯一标识，如: bot-meeting" />
      </el-form-item>
      
      <el-form-item label="名称" prop="name">
        <el-input v-model="form.name" placeholder="显示名称" />
      </el-form-item>
      
      <el-form-item label="描述" prop="description">
        <el-input v-model="form.description" type="textarea" rows="2" placeholder="机器人功能描述" />
      </el-form-item>
      
      <el-divider>企业微信配置</el-divider>
      
      <el-form-item label="Bot ID" prop="wecom_bot_id">
        <el-input v-model="form.wecom_bot_id" placeholder="企业微信机器人 ID" />
      </el-form-item>
      
      <el-form-item label="Secret" prop="wecom_secret">
        <el-input v-model="form.wecom_secret" type="password" show-password placeholder="企业微信机器人 Secret" />
      </el-form-item>
      
      <el-form-item label="默认 Chat ID" prop="default_chatid">
        <el-input v-model="form.default_chatid" placeholder="可选，用于测试" />
      </el-form-item>
      
      <el-divider>Dify 配置</el-divider>
      
      <el-form-item label="API Base URL" prop="dify_api_base">
        <el-input v-model="form.dify_api_base" placeholder="http://127.0.0.1/v1" />
      </el-form-item>
      
      <el-form-item label="API Key" prop="dify_api_key">
        <el-input v-model="form.dify_api_key" type="password" show-password placeholder="Dify API Key (app-xxx)" />
      </el-form-item>
      
      <el-form-item label="Workflow ID" prop="dify_workflow_id">
        <el-input v-model="form.dify_workflow_id" placeholder="可选" />
      </el-form-item>
      
      <el-form-item label="输入变量名" prop="input_variable">
        <el-input v-model="form.input_variable" placeholder="input" />
      </el-form-item>
      
      <el-form-item label="输出变量名" prop="output_variable">
        <el-input v-model="form.output_variable" placeholder="text" />
      </el-form-item>
      
      <el-form-item label="超时时间(秒)" prop="timeout">
        <el-input-number v-model="form.timeout" :min="10" :max="300" />
      </el-form-item>
      
      <el-divider>消息配置</el-divider>
      
      <el-form-item label="欢迎消息" prop="welcome_message">
        <el-input v-model="form.welcome_message" type="textarea" rows="2" />
      </el-form-item>
      
      <el-form-item label="思考中消息" prop="thinking_message">
        <el-input v-model="form.thinking_message" />
      </el-form-item>
      
      <el-form-item>
        <el-button type="primary" @click="submitForm" :loading="loading">
          {{ isEdit ? '保存' : '创建' }}
        </el-button>
        <el-button @click="$router.push('/bots')">取消</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const formRef = ref()
const loading = ref(false)

const isEdit = ref(false)
const botId = ref('')

const form = reactive({
  bot_id: '',
  name: '',
  description: '',
  wecom_bot_id: '',
  wecom_secret: '',
  default_chatid: '',
  dify_api_base: 'http://127.0.0.1/v1',
  dify_api_key: '',
  dify_workflow_id: '',
  input_variable: 'input',
  output_variable: 'text',
  timeout: 60,
  welcome_message: '你好！有什么可以帮你的吗？',
  thinking_message: '⏳ 思考中...'
})

const rules = {
  bot_id: [{ required: true, message: '请输入机器人ID', trigger: 'blur' }],
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  wecom_bot_id: [{ required: true, message: '请输入企业微信 Bot ID', trigger: 'blur' }],
  wecom_secret: [{ required: true, message: '请输入 Secret', trigger: 'blur' }],
  dify_api_key: [{ required: true, message: '请输入 API Key', trigger: 'blur' }]
}

async function loadBot() {
  if (!isEdit.value) return
  
  try {
    const response = await axios.get(`/api/bots/${botId.value}`)
    Object.assign(form, response.data)
  } catch (error) {
    ElMessage.error('加载机器人信息失败')
    router.push('/bots')
  }
}

async function submitForm() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  
  loading.value = true
  try {
    if (isEdit.value) {
      await axios.put(`/api/bots/${botId.value}`, form)
      ElMessage.success('保存成功')
    } else {
      await axios.post('/api/bots', form)
      ElMessage.success('创建成功')
    }
    router.push('/bots')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (route.params.id) {
    isEdit.value = true
    botId.value = route.params.id
    loadBot()
  }
})
</script>
