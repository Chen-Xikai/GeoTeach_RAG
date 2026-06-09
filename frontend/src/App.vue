<template>
  <el-config-provider :locale="zhCn">
    <!-- 未登录时显示登录页 -->
    <router-view v-if="!isLoggedIn" />
    
    <!-- 已登录时显示主界面 -->
    <div v-else class="app-container">
      <!-- 侧边栏 -->
      <aside class="sidebar">
        <div class="logo">
          <el-icon :size="32"><Location /></el-icon>
          <h1>GeoTeach AI</h1>
        </div>
        
        <nav class="nav-menu">
          <router-link to="/" class="nav-item" active-class="active">
            <el-icon><HomeFilled /></el-icon>
            <span>首页</span>
          </router-link>
          <router-link to="/library" class="nav-item" active-class="active">
            <el-icon><Collection /></el-icon>
            <span>资料库</span>
          </router-link>
          <router-link to="/generator" class="nav-item" active-class="active">
            <el-icon><Edit /></el-icon>
            <span>内容生成</span>
          </router-link>
          <router-link to="/qa" class="nav-item" active-class="active">
            <el-icon><ChatDotRound /></el-icon>
            <span>智能问答</span>
          </router-link>
          <router-link v-if="isAdmin" to="/settings" class="nav-item" active-class="active">
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </router-link>
        </nav>
        
        <div class="sidebar-footer">
          <div class="system-status">
            <el-icon><CircleCheck /></el-icon>
            <span>{{ isAdmin ? '管理员' : '已登录' }}</span>
          </div>
          <el-button text size="small" @click="handleLogout" style="color: rgba(255,255,255,0.6); margin-top: 8px;">
            <el-icon><SwitchButton /></el-icon>
            <span>退出</span>
          </el-button>
        </div>
      </aside>
      
      <!-- 主内容区 -->
      <main class="main-content">
        <router-view />
      </main>
    </div>
  </el-config-provider>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

const router = useRouter()
const route = useRoute()
const isLoggedIn = ref(localStorage.getItem('geoteach_auth') === 'true')
const role = ref(localStorage.getItem('geoteach_role') || '')
const isAdmin = computed(() => role.value === 'admin')

const handleLogout = () => {
  localStorage.removeItem('geoteach_auth')
  localStorage.removeItem('geoteach_role')
  isLoggedIn.value = false
  role.value = ''
  router.push('/login')
}

// 监听路由变化，同步登录状态
watch(() => route.path, () => {
  const auth = localStorage.getItem('geoteach_auth') === 'true'
  const r = localStorage.getItem('geoteach_role') || ''
  isLoggedIn.value = auth
  role.value = r
}, { immediate: true })

// 监听 localStorage 变化（登录/登出时触发）
onMounted(() => {
  // 检查当前登录状态
  isLoggedIn.value = localStorage.getItem('geoteach_auth') === 'true'
  role.value = localStorage.getItem('geoteach_role') || ''
})
</script>

<style scoped>
.app-container {
  display: flex;
  height: 100vh;
  background-color: #f5f7fa;
}

.sidebar {
  width: 240px;
  background: linear-gradient(180deg, #1e3a5f 0%, #2d5a87 100%);
  color: white;
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
}

.logo {
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo h1 {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.nav-menu {
  flex: 1;
  padding: 16px 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  transition: all 0.2s ease;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.nav-item.active {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  font-weight: 500;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.system-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}

.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}
</style>
