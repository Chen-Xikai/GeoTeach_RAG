<template>
  <div class="library-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>📚 资料库管理</h1>
      <p>上传和管理教学资料</p>
    </div>

    <!-- 统计信息 -->
    <el-row :gutter="16" style="margin-bottom: 24px;">
      <el-col :span="8">
        <div class="stat-card">
          <div class="stat-icon" style="background: #ede9fe;">
            <el-icon :size="24" color="#7c3aed"><Document /></el-icon>
          </div>
          <div class="stat-info">
            <h3>{{ stats.count || 0 }}</h3>
            <p>文档总数</p>
          </div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card">
          <div class="stat-icon" style="background: #dbeafe;">
            <el-icon :size="24" color="#2563eb"><FolderOpened /></el-icon>
          </div>
          <div class="stat-info">
            <h3>{{ selectedCategory || '全部' }}</h3>
            <p>当前分类</p>
          </div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card">
          <div class="stat-icon" style="background: #d1fae5;">
            <el-icon :size="24" color="#059669"><CircleCheck /></el-icon>
          </div>
          <div class="stat-info">
            <h3>{{ stats.status || '未初始化' }}</h3>
            <p>知识库状态</p>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <!-- 侧边栏：分类和上传 -->
      <el-col :span="6">
        <div class="content-card">
          <h3 style="margin-bottom: 16px;">📤 上传资料</h3>
          
          <!-- 分类选择 -->
          <el-form label-position="top">
            <el-form-item label="资料分类">
              <el-select v-model="selectedCategory" placeholder="选择分类" style="width: 100%;">
                <el-option label="课本资料" value="textbook" />
                <el-option label="课程标准" value="curriculum" />
                <el-option label="教案库" value="lesson_plan" />
                <el-option label="学案库" value="study_plan" />
                <el-option label="优秀教案" value="excellent_lesson" />
                <el-option label="优秀学案" value="excellent_study" />
                <el-option label="说课稿" value="speech_draft" />
                <el-option label="讲课稿" value="lecture_draft" />
              </el-select>
            </el-form-item>
          </el-form>
          
          <!-- 文件上传 -->
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :on-change="handleFileChange"
            :file-list="fileList"
            multiple
            drag
            style="margin-top: 16px;"
          >
            <el-icon :size="48"><Upload /></el-icon>
            <div style="margin-top: 8px;">拖拽文件到此处</div>
            <div style="font-size: 12px; color: #6b7280;">支持 PDF, DOCX, TXT, MD</div>
          </el-upload>
          
          <el-button 
            type="primary" 
            style="width: 100%; margin-top: 16px;"
            :loading="uploading"
            @click="uploadFiles"
          >
            上传并处理
          </el-button>
        </div>
      </el-col>

      <!-- 主内容：文档列表 -->
      <el-col :span="18">
        <div class="content-card">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <h3>📋 文档列表</h3>
            <el-button @click="refreshDocuments">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
          
          <el-table :data="documents" style="width: 100%;" v-loading="loading">
            <el-table-column prop="title" label="标题" min-width="200">
              <template #default="{ row }">
                <div style="display: flex; align-items: center; gap: 8px;">
                  <el-icon><Document /></el-icon>
                  <span>{{ row.metadata?.title || row.metadata?.source?.split('/').pop() || '未知' }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="category" label="分类" width="120">
              <template #default="{ row }">
                <el-tag size="small">{{ row.metadata?.category || '未分类' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="source" label="来源" width="150">
              <template #default="{ row }">
                <span style="font-size: 12px; color: #6b7280;">
                  {{ row.metadata?.学段 || '' }} {{ row.metadata?.年级 || '' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button size="small" type="danger" @click="deleteDocument(row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <div v-if="documents.length === 0 && !loading" style="text-align: center; padding: 40px; color: #6b7280;">
            <el-icon :size="48"><FolderOpened /></el-icon>
            <p style="margin-top: 8px;">暂无文档，请先上传资料</p>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { documentsApi } from '@/api'

const documents = ref([])
const stats = ref({ count: 0, status: '未初始化' })
const selectedCategory = ref('textbook')
const fileList = ref([])
const uploading = ref(false)
const loading = ref(false)

const refreshDocuments = async () => {
  loading.value = true
  try {
    const res = await documentsApi.list()
    documents.value = res.data.documents || []
    
    const statsRes = await documentsApi.stats()
    stats.value = statsRes.data || { count: 0, status: '未初始化' }
  } catch (error) {
    console.error('获取文档失败:', error)
  } finally {
    loading.value = false
  }
}

const handleFileChange = (file) => {
  fileList.value.push(file)
}

const uploadFiles = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请先选择文件')
    return
  }
  
  uploading.value = true
  try {
    for (const file of fileList.value) {
      await documentsApi.importFile(file.raw, selectedCategory.value)
    }
    ElMessage.success('上传成功')
    fileList.value = []
    await refreshDocuments()
  } catch (error) {
    ElMessage.error('上传失败: ' + error.message)
  } finally {
    uploading.value = false
  }
}

const deleteDocument = async (doc) => {
  try {
    await ElMessageBox.confirm('确定要删除这个文档吗？', '确认')
    const source = doc.metadata?.source || doc.id
    await documentsApi.delete(source)
    ElMessage.success('删除成功')
    await refreshDocuments()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + error.message)
    }
  }
}

onMounted(refreshDocuments)
</script>

<style scoped>
.library-page {
  max-width: 1200px;
  margin: 0 auto;
}
</style>
