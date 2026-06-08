<template>
  <div class="qa-page">
    <div class="page-header">
      <h1>❓ 智能问答</h1>
      <p>基于知识库解答地理教学问题</p>
    </div>

    <el-row :gutter="16">
      <!-- 左侧：模式和说明 -->
      <el-col :span="6">
        <div class="content-card">
          <h3 style="margin-bottom: 16px;">👤 角色模式</h3>
          <el-segmented v-model="mode" :options="modeOptions" @change="handleModeChange" />
          
          <div class="mode-desc" v-if="mode === 'teacher'">
            <p><strong>教师端模式</strong></p>
            <p>以地理教育专家身份回答，重点关注教学策略、课标解读、课堂设计。</p>
          </div>
          <div class="mode-desc" v-else>
            <p><strong>学生端模式</strong></p>
            <p>以学习助手身份回答，重点关注概念解释、学习方法、答题技巧。</p>
          </div>
          
          <el-divider />
          
          <h3 style="margin-bottom: 16px;">💡 使用说明</h3>
          <el-collapse>
            <el-collapse-item title="示例问题" name="examples">
              <ul class="example-list">
                <li v-for="(q, idx) in currentExamples" :key="idx" @click="askExample(q)">{{ q }}</li>
              </ul>
            </el-collapse-item>
          </el-collapse>
          
          <el-divider />
          
          <h3 style="margin-bottom: 16px;">📊 知识库状态</h3>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="文档数量">{{ stats.count || 0 }}</el-descriptions-item>
            <el-descriptions-item label="当前模式">{{ mode === 'teacher' ? '教师端' : '学生端' }}</el-descriptions-item>
            <el-descriptions-item label="对话条数">{{ messages.length }}</el-descriptions-item>
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
              <h2>{{ mode === 'teacher' ? 'GeoTeach 教师助手' : 'GeoTeach 学习助手' }}</h2>
              <p>{{ mode === 'teacher' ? '我是您的地理教学专家，可以帮您解答教学问题、提供教学建议。' : '我是您的地理学习助手，可以帮您理解概念、提供学习方法。' }}</p>
              <p>请在下方输入您的问题开始对话。</p>
            </div>
            
            <div v-for="(msg, index) in messages" :key="index" class="message" :class="msg.role">
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
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { qaApi, documentsApi } from '@/api'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'

// 模式配置
const modeOptions = [
  { label: '👨‍🏫 教师端', value: 'teacher' },
  { label: '👨‍🎓 学生端', value: 'student' }
]

const teacherExamples = [
  '如何讲解气压带和风带？',
  '地球运动的教学难点是什么？',
  '如何设计地理实践活动？',
  '课标中对区域认知的要求是什么？'
]

const studentExamples = [
  '什么是板块构造？',
  '如何理解季风的形成？',
  '怎样记忆世界气候类型？',
  '洋流对气候有什么影响？'
]

// 状态
const mode = ref('teacher')
const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const stats = ref({ count: 0, status: '未初始化' })
const messagesContainer = ref(null)

const currentExamples = computed(() => {
  return mode.value === 'teacher' ? teacherExamples : studentExamples
})

// localStorage 键名
const getStorageKey = (m) => `geoteach_qa_${m}`

// 保存聊天记录到 localStorage
const saveMessages = () => {
  try {
    localStorage.setItem(getStorageKey(mode.value), JSON.stringify(messages.value))
  } catch (e) {
    console.error('保存聊天记录失败:', e)
  }
}

// 从 localStorage 加载聊天记录
const loadMessages = () => {
  try {
    const stored = localStorage.getItem(getStorageKey(mode.value))
    messages.value = stored ? JSON.parse(stored) : []
  } catch (e) {
    console.error('加载聊天记录失败:', e)
    messages.value = []
  }
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// 发送消息
const sendMessage = async () => {
  const question = inputMessage.value.trim()
  if (!question || loading.value) return
  
  messages.value.push({
    role: 'user',
    content: question,
    time: new Date().toLocaleTimeString()
  })
  
  inputMessage.value = ''
  loading.value = true
  scrollToBottom()
  saveMessages()
  
  try {
    const res = await qaApi.ask(question, mode.value)
    
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
    saveMessages()
  }
}

// 示例问题
const askExample = (question) => {
  inputMessage.value = question
  sendMessage()
}

// 清空历史
const clearHistory = () => {
  messages.value = []
  saveMessages()
  ElMessage.success('对话历史已清空')
}

// 切换模式
const handleModeChange = () => {
  loadMessages()
  scrollToBottom()
}

// 监听消息变化自动保存
watch(messages, () => {
  saveMessages()
}, { deep: true })

onMounted(async () => {
  loadMessages()
  
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
  margin-top: 12px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  font-size: 13px;
  color: #6b7280;
}

.mode-desc p {
  margin: 4px 0;
}

.mode-desc strong {
  color: #1f2937;
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

.example-list {
  padding-left: 20px;
  font-size: 14px;
}

.example-list li {
  margin-bottom: 8px;
  cursor: pointer;
  color: #7c3aed;
}

.example-list li:hover {
  text-decoration: underline;
}

.markdown-content {
  padding: 8px 12px;
}

.markdown-content :deep(p) {
  margin: 0 0 8px 0;
}

.markdown-content :deep(p:last-child) {
  margin-bottom: 0;
}
</style>
