<template>
  <el-config-provider :locale="zhCn">
    <div class="app-container">
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
          <router-link to="/settings" class="nav-item" active-class="active">
            <el-icon><Setting /></el-icon>
            <span>设置</span>
          </router-link>
        </nav>
        
        <div class="sidebar-footer">
          <div class="system-status">
            <el-icon><CircleCheck /></el-icon>
            <span>系统正常</span>
          </div>
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
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
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
