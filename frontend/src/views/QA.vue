<template>
  <div class="qa-page">
    <div class="page-header">
      <h1>❓ 智能问答</h1>
      <p>基于知识库解答地理教学问题</p>
    </div>

    <el-row :gutter="16">
      <!-- 左侧：模式 + 会话列表 -->
      <el-col :span="6">
        <div class="content-card">
          <h3 style="margin-bottom: 12px;">👤 角色模式</h3>
          <el-segmented v-model="mode" :options="modeOptions" @change="handleModeChange" size="small" />
          
          <div class="mode-desc">
            <template v-if="mode === 'teacher'">
              <p><strong>教师端</strong>：教学策略、课标解读、课堂设计</p>
            </template>
            <template v-else>
              <p><strong>学生端</strong>：概念解释、学习方法、答题技巧</p>
            </template>
          </div>
          
          <el-divider />
          
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <h3>💬 对话历史</h3>
            <el-button size="small" type="primary" @click="createSession">
              <el-icon><Plus /></el-icon> 新建
            </el-button>
          </div>
          
          <div class="session-list">
            <div 
              v-for="session in sessions" 
              :key="session.id"
              class="session-item"
              :class="{ active: currentSessionId === session.id }"
              @click="switchSession(session.id)"
            >
              <div class="session-info">
                <div class="session-title">{{ session.title }}</div>
                <div class="session-meta">{{ session.messageCount }}条消息 · {{ formatTime(session.updatedAt) }}</div>
              </div>
              <el-button 
                size="small" 
                text 
                @click.stop="deleteSession(session.id)"
                class="session-delete"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
            
            <div v-if="sessions.length === 0" class="empty-sessions">
              <p>暂无对话记录</p>
              <p style="font-size: 12px;">点击"新建"开始对话</p>
            </div>
          </div>
          
          <el-divider />
          
          <el-button 
            style="width: 100%;"
            @click="clearAllSessions"
            :disabled="sessions.length === 0"
          >
            清空所有对话
          </el-button>
        </div>
      </el-col>

      <!-- 右侧：对话区域 -->
      <el-col :span="18">
        <div class="content-card chat-card">
          <!-- 对话标题栏 -->
          <div class="chat-header" v-if="currentSession">
            <span class="chat-title">{{ currentSession.title }}</span>
            <div class="chat-actions">
              <el-button size="small" @click="exportSession" :disabled="currentMessages.length === 0">
                <el-icon><Download /></el-icon> 导出
              </el-button>
              <el-button size="small" type="danger" @click="clearCurrentSession" :disabled="currentMessages.length === 0">
                <el-icon><Delete /></el-icon> 清空
              </el-button>
            </div>
          </div>
          
          <!-- 消息列表 -->
          <div class="messages-container" ref="messagesContainer">
            <div v-if="!currentSession" class="welcome-message">
              <el-icon :size="64" color="#7c3aed"><ChatDotRound /></el-icon>
              <h2>GeoTeach AI 助手</h2>
              <p>点击左侧"新建"开始对话，或选择已有对话继续</p>
            </div>
            
            <div v-else-if="currentMessages.length === 0" class="welcome-message">
              <el-icon :size="64" color="#7c3aed"><ChatDotRound /></el-icon>
              <h2>{{ mode === 'teacher' ? 'GeoTeach 教师助手' : 'GeoTeach 学习助手' }}</h2>
              <p>{{ mode === 'teacher' ? '我是您的地理教学专家，可以帮您解答教学问题、提供教学建议。' : '我是您的地理学习助手，可以帮您理解概念、提供学习方法。' }}</p>
              <p>请在下方输入您的问题开始对话。</p>
            </div>
            
            <div v-for="(msg, index) in currentMessages" :key="index" class="message" :class="msg.role">
              <div class="message-avatar">
                <el-icon v-if="msg.role === 'user'" :size="24"><User /></el-icon>
                <el-icon v-else :size="24"><ChatDotRound /></el-icon>
              </div>
              <div class="message-content">
                <div class="message-text" :class="{ 'markdown-content': msg.role === 'assistant' }">
                  <template v-if="msg.role === 'assistant'">
                    <MarkdownRenderer :content="msg.content" />
                  </template>
                  <template v-else>
                    {{ msg.content }}
                  </template>
                </div>
                <div class="message-time">{{ msg.time }}</div>
              </div>
            </div>
            
            <div v-if="loading" class="message assistant">
              <div class="message-avatar">
                <el-icon :size="24"><ChatDotRound /></el-icon>
              </div>
              <div class="message-content">
                <div class="typing-indicator">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 输入区域 -->
          <div class="input-area">
            <el-input
              v-model="inputMessage"
              placeholder="输入您的问题... (Ctrl+Enter 发送)"
              :rows="2"
              type="textarea"
              @keydown.enter.ctrl="sendMessage"
              :disabled="loading || !currentSession"
            />
            <el-button 
              type="primary" 
              @click="sendMessage"
              :loading="loading"
              :disabled="!inputMessage.trim() || !currentSession"
            >
              <el-icon><Promotion /></el-icon>
              发送
            </el-button>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { qaApi, documentsApi } from '@/api'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'

// ============ 模式配置 ============
const modeOptions = [
  { label: '👨‍🏫 教师端', value: 'teacher' },
  { label: '👨‍🎓 学生端', value: 'student' }
]

// ============ 状态 ============
const mode = ref('teacher')
const sessions = ref([])
const currentSessionId = ref(null)
const inputMessage = ref('')
const loading = ref(false)
const stats = ref({ count: 0, status: '未初始化' })
const messagesContainer = ref(null)

// ============ 计算属性 ============
const currentSession = computed(() => {
  return sessions.value.find(s => s.id === currentSessionId.value) || null
})

const currentMessages = computed(() => {
  if (!currentSession.value) return []
  return currentSession.value.messages || []
})

// ============ localStorage 操作 ============
const SESSIONS_KEY = 'geoteach_qa_sessions'

const getSessionKey = (id) => `geoteach_qa_session_${id}`

const loadSessions = () => {
  try {
    const stored = localStorage.getItem(SESSIONS_KEY)
    sessions.value = stored ? JSON.parse(stored) : []
  } catch (e) {
    sessions.value = []
  }
}

const saveSessions = () => {
  try {
    const index = sessions.value.map(s => ({
      id: s.id,
      title: s.title,
      mode: s.mode,
      messageCount: s.messages.length,
      createdAt: s.createdAt,
      updatedAt: s.updatedAt
    }))
    localStorage.setItem(SESSIONS_KEY, JSON.stringify(index))
  } catch (e) {
    console.error('保存会话索引失败:', e)
  }
}

const loadSessionDetail = (id) => {
  try {
    const stored = localStorage.getItem(getSessionKey(id))
    return stored ? JSON.parse(stored) : null
  } catch (e) {
    return null
  }
}

const saveSessionDetail = (session) => {
  try {
    localStorage.setItem(getSessionKey(session.id), JSON.stringify(session))
  } catch (e) {
    console.error('保存会话详情失败:', e)
  }
}

const removeSessionDetail = (id) => {
  try {
    localStorage.removeItem(getSessionKey(id))
  } catch (e) {
    console.error('删除会话详情失败:', e)
  }
}

// ============ 会话操作 ============
const createSession = () => {
  const id = 'session_' + Date.now()
  const session = {
    id,
    title: '新对话',
    mode: mode.value,
    messages: [],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  }
  
  sessions.value.unshift(session)
  currentSessionId.value = id
  saveSessions()
  saveSessionDetail(session)
}

const switchSession = (id) => {
  currentSessionId.value = id
  // 加载完整会话数据
  const detail = loadSessionDetail(id)
  if (detail) {
    const idx = sessions.value.findIndex(s => s.id === id)
    if (idx !== -1) {
      sessions.value[idx] = detail
      // 同步mode
      mode.value = detail.mode || 'teacher'
    }
  }
  scrollToBottom()
}

const deleteSession = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这个对话吗？', '确认删除', { type: 'warning' })
    
    removeSessionDetail(id)
    sessions.value = sessions.value.filter(s => s.id !== id)
    
    if (currentSessionId.value === id) {
      currentSessionId.value = sessions.value.length > 0 ? sessions.value[0].id : null
    }
    
    saveSessions()
    ElMessage.success('对话已删除')
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

const clearCurrentSession = async () => {
  if (!currentSession.value) return
  try {
    await ElMessageBox.confirm('确定要清空当前对话吗？', '确认清空', { type: 'warning' })
    
    currentSession.value.messages = []
    currentSession.value.updatedAt = new Date().toISOString()
    saveSessionDetail(currentSession.value)
    saveSessions()
    ElMessage.success('对话已清空')
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

const clearAllSessions = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有对话吗？此操作不可恢复！', '确认清空', { type: 'warning' })
    
    // 删除所有会话详情
    sessions.value.forEach(s => removeSessionDetail(s.id))
    sessions.value = []
    currentSessionId.value = null
    
    localStorage.removeItem(SESSIONS_KEY)
    ElMessage.success('所有对话已清空')
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

const handleModeChange = () => {
  // 模式切换时，如果当前会话模式不匹配，更新会话模式
  if (currentSession.value) {
    currentSession.value.mode = mode.value
    saveSessionDetail(currentSession.value)
    saveSessions()
  }
}

// ============ 消息操作 ============
const generateTitle = (content) => {
  // 根据首条消息生成标题（取前15个字符）
  const title = content.length > 15 ? content.substring(0, 15) + '...' : content
  return title
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const sendMessage = async () => {
  const question = inputMessage.value.trim()
  if (!question || loading.value || !currentSession.value) return
  
  // 添加用户消息
  const userMsg = {
    role: 'user',
    content: question,
    time: new Date().toLocaleTimeString()
  }
  currentSession.value.messages.push(userMsg)
  
  // 如果是第一条消息，自动生成标题
  if (currentSession.value.messages.length === 1) {
    currentSession.value.title = generateTitle(question)
  }
  
  inputMessage.value = ''
  loading.value = true
  scrollToBottom()
  saveSessionDetail(currentSession.value)
  saveSessions()
  
  try {
    // 构建历史（排除当前消息，最近10轮）
    const historyForApi = currentSession.value.messages.slice(0, -1).slice(-20).map(m => ({
      role: m.role,
      content: m.content
    }))
    
    const res = await qaApi.ask(question, mode.value, historyForApi)
    
    // 添加AI回复
    currentSession.value.messages.push({
      role: 'assistant',
      content: res.data.answer,
      time: new Date().toLocaleTimeString()
    })
  } catch (error) {
    currentSession.value.messages.push({
      role: 'assistant',
      content: '抱歉，回答问题时出现错误：' + error.message,
      time: new Date().toLocaleTimeString()
    })
  } finally {
    loading.value = false
    currentSession.value.updatedAt = new Date().toISOString()
    scrollToBottom()
    saveSessionDetail(currentSession.value)
    saveSessions()
  }
}

const askExample = (question) => {
  if (!currentSession.value) {
    createSession()
  }
  inputMessage.value = question
  sendMessage()
}

// ============ 导出功能 ============
const exportSession = () => {
  if (!currentSession.value || currentSession.value.messages.length === 0) return
  
  let markdown = `# ${currentSession.value.title}\n\n`
  markdown += `> 模式：${currentSession.value.mode === 'teacher' ? '教师端' : '学生端'}\n`
  markdown += `> 创建时间：${currentSession.value.createdAt}\n\n---\n\n`
  
  currentSession.value.messages.forEach(msg => {
    const role = msg.role === 'user' ? '👤 用户' : '🤖 AI助手'
    markdown += `### ${role} (${msg.time})\n\n${msg.content}\n\n---\n\n`
  })
  
  // 创建下载
  const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${currentSession.value.title}.md`
  a.click()
  URL.revokeObjectURL(url)
  
  ElMessage.success('对话已导出')
}

// ============ 工具函数 ============
const formatTime = (isoString) => {
  if (!isoString) return ''
  const date = new Date(isoString)
  return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// ============ 生命周期 ============
onMounted(async () => {
  loadSessions()
  
  // 如果有会话，选中第一个
  if (sessions.value.length > 0) {
    switchSession(sessions.value[0].id)
  }
  
  try {
    const res = await documentsApi.stats()
    stats.value = res.data || { count: 0, status: '未初始化' }
  } catch (error) {
    console.error('获取状态失败:', error)
  }
})
</script>

<style scoped>
.qa-page {
  max-width: 1400px;
  margin: 0 auto;
}

.mode-desc {
  margin-top: 8px;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 6px;
  font-size: 12px;
  color: #6b7280;
}

.mode-desc p { margin: 2px 0; }
.mode-desc strong { color: #1f2937; }

.session-list {
  max-height: 300px;
  overflow-y: auto;
}

.session-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 4px;
}

.session-item:hover {
  background: #f3f4f6;
}

.session-item.active {
  background: #ede9fe;
  border: 1px solid #c4b5fd;
}

.session-info { flex: 1; min-width: 0; }

.session-title {
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-meta {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 2px;
}

.session-delete {
  opacity: 0;
  transition: opacity 0.2s;
}

.session-item:hover .session-delete {
  opacity: 1;
}

.empty-sessions {
  text-align: center;
  padding: 20px;
  color: #9ca3af;
  font-size: 13px;
}

.chat-card {
  height: calc(100vh - 200px);
  display: flex;
  flex-direction: column;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
}

.chat-title {
  font-weight: 600;
  color: #1f2937;
}

.chat-actions {
  display: flex;
  gap: 8px;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.welcome-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #6b7280;
  text-align: center;
}

.welcome-message h2 { margin-top: 16px; color: #1f2937; }
.welcome-message p { margin-top: 8px; font-size: 14px; }

.message { display: flex; gap: 12px; margin-bottom: 16px; }
.message.user { flex-direction: row-reverse; }

.message-avatar {
  width: 40px; height: 40px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}

.message.user .message-avatar { background: #7c3aed; color: white; }
.message.assistant .message-avatar { background: #f3f4f6; color: #4b5563; }

.message-content { max-width: 70%; }

.message-text {
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
}

.message.user .message-text { background: #7c3aed; color: white; border-bottom-right-radius: 4px; }
.message.assistant .message-text { background: #f3f4f6; color: #1f2937; border-bottom-left-radius: 4px; }

.message-time { font-size: 11px; color: #9ca3af; margin-top: 4px; }
.message.user .message-time { text-align: right; }

.typing-indicator { display: flex; gap: 4px; padding: 12px 16px; background: #f3f4f6; border-radius: 12px; }
.typing-indicator span { width: 8px; height: 8px; background: #9ca3af; border-radius: 50%; animation: typing 1.4s infinite ease-in-out; }
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing { 0%, 80%, 100% { transform: scale(0.6); opacity: 0.6; } 40% { transform: scale(1); opacity: 1; } }

.input-area { padding: 16px; border-top: 1px solid #e5e7eb; display: flex; gap: 12px; }
.input-area .el-input { flex: 1; }

.markdown-content { padding: 8px 12px; }
.markdown-content :deep(p) { margin: 0 0 8px 0; }
.markdown-content :deep(p:last-child) { margin-bottom: 0; }
</style>
