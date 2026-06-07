<template>
  <div class="qa-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>❓ 智能问答</h1>
      <p>基于知识库解答地理教学问题</p>
    </div>

    <el-row :gutter="16">
      <!-- 左侧：历史和示例 -->
      <el-col :span="6">
        <div class="content-card">
          <h3 style="margin-bottom: 16px;">💡 使用说明</h3>
          <el-collapse>
            <el-collapse-item title="功能特点" name="features">
              <ul class="feature-list">
                <li>专业解答地理教学问题</li>
                <li>引用课程标准要求</li>
                <li>提供可操作的教学建议</li>
              </ul>
            </el-collapse-item>
            <el-collapse-item title="示例问题" name="examples">
              <ul class="example-list">
                <li @click="askExample('如何讲解气压带和风带？')">如何讲解气压带和风带？</li>
                <li @click="askExample('地球运动的教学难点是什么？')">地球运动的教学难点是什么？</li>
                <li @click="askExample('如何设计地理实践活动？')">如何设计地理实践活动？</li>
                <li @click="askExample('什么是板块构造？')">什么是板块构造？</li>
              </ul>
            </el-collapse-item>
          </el-collapse>
          
          <el-divider />
          
          <h3 style="margin-bottom: 16px;">📊 知识库状态</h3>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="文档数量">{{ stats.count || 0 }}</el-descriptions-item>
            <el-descriptions-item label="状态">{{ stats.status || '未初始化' }}</el-descriptions-item>
          </el-descriptions>
          
          <el-button 
            style="width: 100%; margin-top: 16px;"
            @click="clearHistory"
          >
            清空对话历史
          </el-button>
        </div>
      </el-col>

      <!-- 右侧：对话区域 -->
      <el-col :span="18">
        <div class="content-card chat-card">
          <!-- 消息列表 -->
          <div class="messages-container" ref="messagesContainer">
            <div v-if="messages.length === 0" class="welcome-message">
              <el-icon :size="64" color="#7c3aed"><ChatDotRound /></el-icon>
              <h2>GeoTeach AI 助手</h2>
              <p>我是您的地理教学助手，可以帮您解答教学问题、提供教学建议。</p>
              <p>请在下方输入您的问题开始对话。</p>
            </div>
            
            <div v-for="(msg, index) in messages" :key="index" class="message" :class="msg.role">
              <div class="message-avatar">
                <el-icon v-if="msg.role === 'user'" :size="24"><User /></el-icon>
                <el-icon v-else :size="24"><ChatDotRound /></el-icon>
              </div>
              <div class="message-content">
                <div class="message-text">{{ msg.content }}</div>
                <div class="message-time">{{ msg.time }}</div>
              </div>
            </div>
            
            <div v-if="loading" class="message assistant">
              <div class="message-avatar">
                <el-icon :size="24"><ChatDotRound /></el-icon>
              </div>
              <div class="message-content">
                <div class="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 输入区域 -->
          <div class="input-area">
            <el-input
              v-model="inputMessage"
              placeholder="输入您的问题..."
              :rows="2"
              type="textarea"
              @keydown.enter.ctrl="sendMessage"
              :disabled="loading"
            />
            <el-button 
              type="primary" 
              @click="sendMessage"
              :loading="loading"
              :disabled="!inputMessage.trim()"
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
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { qaApi, documentsApi } from '@/api'

const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const stats = ref({ count: 0, status: '未初始化' })
const messagesContainer = ref(null)

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const sendMessage = async () => {
  const question = inputMessage.value.trim()
  if (!question || loading.value) return
  
  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: question,
    time: new Date().toLocaleTimeString()
  })
  
  inputMessage.value = ''
  loading.value = true
  scrollToBottom()
  
  try {
    const res = await qaApi.ask(question)
    
    // 添加AI回复
    messages.value.push({
      role: 'assistant',
      content: res.data.answer,
      time: new Date().toLocaleTimeString()
    })
  } catch (error) {
    messages.value.push({
      role: 'assistant',
      content: '抱歉，回答问题时出现错误：' + error.message,
      time: new Date().toLocaleTimeString()
    })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

const askExample = (question) => {
  inputMessage.value = question
  sendMessage()
}

const clearHistory = () => {
  messages.value = []
  ElMessage.success('对话历史已清空')
}

onMounted(async () => {
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

.chat-card {
  height: calc(100vh - 200px);
  display: flex;
  flex-direction: column;
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

.welcome-message h2 {
  margin-top: 16px;
  color: #1f2937;
}

.welcome-message p {
  margin-top: 8px;
  font-size: 14px;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message.user .message-avatar {
  background: #7c3aed;
  color: white;
}

.message.assistant .message-avatar {
  background: #f3f4f6;
  color: #4b5563;
}

.message-content {
  max-width: 70%;
}

.message-text {
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
}

.message.user .message-text {
  background: #7c3aed;
  color: white;
  border-bottom-right-radius: 4px;
}

.message.assistant .message-text {
  background: #f3f4f6;
  color: #1f2937;
  border-bottom-left-radius: 4px;
}

.message-time {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 4px;
}

.message.user .message-time {
  text-align: right;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: #f3f4f6;
  border-radius: 12px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #9ca3af;
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.6; }
  40% { transform: scale(1); opacity: 1; }
}

.input-area {
  padding: 16px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  gap: 12px;
}

.input-area .el-input {
  flex: 1;
}

.feature-list,
.example-list {
  padding-left: 20px;
  font-size: 14px;
}

.feature-list li,
.example-list li {
  margin-bottom: 8px;
}

.example-list li {
  cursor: pointer;
  color: #7c3aed;
}

.example-list li:hover {
  text-decoration: underline;
}
</style>
