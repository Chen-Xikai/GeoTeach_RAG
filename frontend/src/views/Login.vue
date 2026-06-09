<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <el-icon :size="48" color="#7c3aed"><Location /></el-icon>
        <h1>GeoTeach AI</h1>
        <p>地理教学智能助手</p>
      </div>
      
      <el-form @submit.prevent="handleLogin">
        <el-form-item>
          <el-input
            v-model="password"
            type="password"
            placeholder="请输入访问密码"
            size="large"
            show-password
            @keyup.enter="handleLogin"
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-button 
          type="primary" 
          size="large" 
          style="width: 100%;"
          :loading="loading"
          @click="handleLogin"
        >
          进入系统
        </el-button>
      </el-form>
      
      <div v-if="errorMsg" class="error-msg">
        <el-alert :title="errorMsg" type="error" show-icon :closable="false" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { authApi } from '@/api'
import { ElMessage } from 'element-plus'

const password = ref('')
const loading = ref(false)
const errorMsg = ref('')

const handleLogin = async () => {
  if (!password.value) {
    errorMsg.value = '请输入密码'
    return
  }
  
  loading.value = true
  errorMsg.value = ''
  
  try {
    const res = await authApi.login(password.value)
    if (res.status === 'success') {
      const role = res.data.role
      localStorage.setItem('geoteach_role', role)
      localStorage.setItem('geoteach_auth', 'true')
      ElMessage.success(res.data.message || '登录成功')
      // 登录成功后跳转到首页
      window.location.href = '/'
    } else {
      errorMsg.value = res.message || '密码错误'
    }
  } catch (e) {
    errorMsg.value = e.message || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 400px;
  padding: 40px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h1 {
  margin: 16px 0 8px;
  font-size: 28px;
  color: #1f2937;
}

.login-header p {
  color: #6b7280;
  font-size: 14px;
}

.error-msg {
  margin-top: 16px;
}
</style>
