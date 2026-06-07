<template>
  <div class="generator-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>🛠️ 内容生成</h1>
      <p>生成说课稿、讲课稿、教案、学案</p>
    </div>

    <el-row :gutter="16">
      <!-- 左侧：配置 -->
      <el-col :span="8">
        <div class="content-card">
          <h3 style="margin-bottom: 16px;">📋 生成配置</h3>
          
          <!-- 教材目录选择 -->
          <el-form label-position="top">
            <el-form-item label="学段">
              <el-select v-model="form.level" @change="loadGrades">
                <el-option label="初中" value="初中" />
                <el-option label="高中" value="高中" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="年级">
              <el-select v-model="form.grade" @change="loadSemesters">
                <el-option v-for="g in grades" :key="g" :label="g" :value="g" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="学期">
              <el-select v-model="form.semester" @change="loadChapters">
                <el-option v-for="s in semesters" :key="s" :label="s" :value="s" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="章节">
              <el-select v-model="form.chapter" @change="loadSections">
                <el-option v-for="c in chapters" :key="c.id" :label="c.title" :value="c.title" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="小节" v-if="sections.length > 0">
              <el-select v-model="form.section">
                <el-option v-for="s in sections" :key="s.id" :label="s.title" :value="s.title" />
              </el-select>
            </el-form-item>
          </el-form>
          
          <el-divider />
          
          <!-- 基本信息 -->
          <el-form label-position="top">
            <el-form-item label="课题名称">
              <el-input v-model="form.topic" placeholder="输入课题名称" />
            </el-form-item>
            
            <el-form-item label="教材版本">
              <el-select v-model="form.textbookVersion">
                <el-option label="人教版" value="人教版" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="课时安排">
              <el-select v-model="form.classHours">
                <el-option label="1课时" value="1课时" />
                <el-option label="2课时" value="2课时" />
                <el-option label="3课时" value="3课时" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="授课对象" v-if="activeTab === 'lesson_plan'">
              <el-input v-model="form.students" placeholder="如：高二年级学生" />
            </el-form-item>
          </el-form>
        </div>
      </el-col>

      <!-- 右侧：生成结果 -->
      <el-col :span="16">
        <div class="content-card">
          <!-- 功能选择 -->
          <el-tabs v-model="activeTab" @tab-change="handleTabChange">
            <el-tab-pane label="🎤 说课稿" name="speech_draft">
              <template #label>
                <span><el-icon><Microphone /></el-icon> 说课稿</span>
              </template>
            </el-tab-pane>
            <el-tab-pane label="👨‍🏫 讲课稿" name="lecture_draft">
              <template #label>
                <span><el-icon><User /></el-icon> 讲课稿</span>
              </template>
            </el-tab-pane>
            <el-tab-pane label="📝 教案" name="lesson_plan">
              <template #label>
                <span><el-icon><Edit /></el-icon> 教案</span>
              </template>
            </el-tab-pane>
            <el-tab-pane label="📄 学案" name="study_plan">
              <template #label>
                <span><el-icon><Document /></el-icon> 学案</span>
              </template>
            </el-tab-pane>
          </el-tabs>

          <!-- 生成按钮 -->
          <div style="margin: 16px 0;">
            <el-button 
              type="primary" 
              size="large"
              :loading="generating"
              @click="generateContent"
              style="width: 100%;"
            >
              <el-icon><Magic /></el-icon>
              开始生成
            </el-button>
          </div>

          <!-- 生成结果 -->
          <div v-if="generatedContent" class="result-section">
            <div class="result-header">
              <h3>📄 生成结果</h3>
              <div class="result-actions">
                <el-button size="small" @click="copyContent">
                  <el-icon><CopyDocument /></el-icon>
                  复制
                </el-button>
                <el-button size="small" @click="downloadContent">
                  <el-icon><Download /></el-icon>
                  下载
                </el-button>
              </div>
            </div>
            
            <div class="result-content">
              <pre>{{ generatedContent }}</pre>
            </div>
          </div>
          
          <div v-else-if="!generating" class="empty-state">
            <el-icon :size="64" color="#d1d5db"><Edit /></el-icon>
            <p>配置参数后点击"开始生成"</p>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { catalogApi, generateApi } from '@/api'

const activeTab = ref('speech_draft')
const generating = ref(false)
const generatedContent = ref('')

// 表单数据
const form = ref({
  level: '高中',
  grade: '高二',
  semester: '选择性必修第一册',
  chapter: '',
  section: '',
  topic: '',
  textbookVersion: '人教版',
  classHours: '1课时',
  students: ''
})

// 目录数据
const grades = ref([])
const semesters = ref([])
const chapters = ref([])
const sections = ref([])

// 加载目录数据
const loadGrades = async () => {
  try {
    const res = await catalogApi.getGrades(form.value.level)
    grades.value = res.data.grades || []
    if (grades.value.length > 0) {
      form.value.grade = grades.value[0]
      await loadSemesters()
    }
  } catch (error) {
    console.error('获取年级失败:', error)
  }
}

const loadSemesters = async () => {
  // 根据年级加载学期
  if (form.value.level === '初中') {
    semesters.value = ['上册', '下册']
  } else {
    if (form.value.grade === '高一') {
      semesters.value = ['必修第一册', '必修第二册']
    } else if (form.value.grade === '高二') {
      semesters.value = ['选择性必修第一册', '选择性必修第二册', '选择性必修第三册']
    }
  }
  if (semesters.value.length > 0) {
    form.value.semester = semesters.value[0]
    await loadChapters()
  }
}

const loadChapters = async () => {
  try {
    const res = await catalogApi.getChapters(form.value.level, form.value.grade, form.value.semester)
    chapters.value = res.data.chapters || []
    sections.value = []
    form.value.chapter = ''
    form.value.section = ''
  } catch (error) {
    console.error('获取章节失败:', error)
  }
}

const loadSections = () => {
  const chapter = chapters.value.find(c => c.title === form.value.chapter)
  sections.value = chapter?.sections || []
  form.value.section = ''
}

const handleTabChange = () => {
  generatedContent.value = ''
}

// 生成内容
const generateContent = async () => {
  if (!form.value.topic) {
    ElMessage.warning('请输入课题名称')
    return
  }
  
  generating.value = true
  generatedContent.value = ''
  
  try {
    const data = {
      topic: form.value.topic,
      textbook_version: form.value.textbookVersion,
      grade_level: `${form.value.level}${form.value.grade}`,
      chapter: form.value.chapter,
      class_hours: form.value.classHours,
      students: form.value.students
    }
    
    let res
    switch (activeTab.value) {
      case 'speech_draft':
        res = await generateApi.speechDraft(data)
        break
      case 'lecture_draft':
        res = await generateApi.lectureDraft(data)
        break
      case 'lesson_plan':
        res = await generateApi.lessonPlan(data)
        break
      case 'study_plan':
        res = await generateApi.studyPlan(data)
        break
    }
    
    generatedContent.value = res.data.content
    ElMessage.success('生成完成')
  } catch (error) {
    ElMessage.error('生成失败: ' + error.message)
  } finally {
    generating.value = false
  }
}

// 复制内容
const copyContent = () => {
  navigator.clipboard.writeText(generatedContent.value)
  ElMessage.success('已复制到剪贴板')
}

// 下载内容
const downloadContent = () => {
  const blob = new Blob([generatedContent.value], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${activeTab.value}_${form.value.topic}.md`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(() => {
  loadGrades()
})
</script>

<style scoped>
.generator-page {
  max-width: 1400px;
  margin: 0 auto;
}

.result-section {
  margin-top: 16px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.result-header h3 {
  margin: 0;
}

.result-actions {
  display: flex;
  gap: 8px;
}

.result-content {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  max-height: 600px;
  overflow-y: auto;
}

.result-content pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: inherit;
  margin: 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px;
  color: #9ca3af;
}

.empty-state p {
  margin-top: 12px;
  font-size: 14px;
}
</style>
