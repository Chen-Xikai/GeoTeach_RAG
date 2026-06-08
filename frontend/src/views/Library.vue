<template>
  <div class="library-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>📚 资料库管理</h1>
      <p>上传和管理教学资料（文件需审核后才能入库）</p>
    </div>

    <!-- 统计信息 -->
    <el-row :gutter="16" style="margin-bottom: 24px;">
      <el-col :span="6">
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
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: #fef3c7;">
            <el-icon :size="24" color="#d97706"><Clock /></el-icon>
          </div>
          <div class="stat-info">
            <h3>{{ pendingFiles.length }}</h3>
            <p>待审核</p>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
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
      <el-col :span="6">
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
            上传（待审核）
          </el-button>
          
          <el-alert 
            type="warning" 
            :closable="false"
            style="margin-top: 12px;"
            title="安全提示"
            description="上传的文件需要管理员审核后才能入库，防止恶意文件。"
            show-icon
          />
        </div>
      </el-col>

      <!-- 主内容：文档列表 -->
      <el-col :span="18">
        <el-tabs v-model="activeTab">
          <!-- 待审核文件 -->
          <el-tab-pane label="待审核" name="pending">
            <div class="content-card">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <h3>⏳ 待审核文件</h3>
                <el-button @click="refreshPending">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
              
              <el-table :data="pendingFiles" style="width: 100%;" v-loading="pendingLoading">
                <el-table-column prop="original_filename" label="文件名" min-width="200">
                  <template #default="{ row }">
                    <div style="display: flex; align-items: center; gap: 8px;">
                      <el-icon color="#d97706"><Document /></el-icon>
                      <span>{{ row.original_filename }}</span>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="category" label="分类" width="120">
                  <template #default="{ row }">
                    <el-tag size="small" type="warning">{{ row.category }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="file_size" label="大小" width="100">
                  <template #default="{ row }">
                    {{ formatSize(row.file_size) }}
                  </template>
                </el-table-column>
                <el-table-column prop="upload_time" label="上传时间" width="150">
                  <template #default="{ row }">
                    {{ formatTime(row.upload_time) }}
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="200">
                  <template #default="{ row }">
                    <el-button size="small" type="success" @click="approveFile(row)">
                      批准
                    </el-button>
                    <el-button size="small" type="danger" @click="rejectFile(row)">
                      拒绝
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
              
              <div v-if="pendingFiles.length === 0 && !pendingLoading" style="text-align: center; padding: 40px; color: #6b7280;">
                <el-icon :size="48"><CircleCheck /></el-icon>
                <p style="margin-top: 8px;">没有待审核的文件</p>
              </div>
            </div>
          </el-tab-pane>
          
          <!-- 已入库文档 -->
          <el-tab-pane label="已入库" name="approved">
            <div class="content-card">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <h3>📋 已入库文档</h3>
                <el-button @click="refreshDocuments">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
              
              <el-table :data="documents" style="width: 100%;" v-loading="loading">
                <el-table-column label="文件名" min-width="200">
                  <template #default="{ row }">
                    <div style="display: flex; align-items: center; gap: 8px;">
                      <el-icon :color="row.status === 'imported' ? '#059669' : row.status === 'orphan' ? '#d97706' : '#6b7280'"><Document /></el-icon>
                      <span>{{ row.name }}</span>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="状态" width="120">
                  <template #default="{ row }">
                    <el-tag :type="row.status === 'imported' ? 'success' : row.status === 'orphan' ? 'warning' : 'info'" size="small">
                      {{ row.status === 'imported' ? '已入库' : row.status === 'orphan' ? '孤立' : '未导入' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="chunks" label="Chunks" width="100" />
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
          </el-tab-pane>
        </el-tabs>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { documentsApi } from '@/api'

const documents = ref([])
const pendingFiles = ref([])
const stats = ref({ count: 0, status: '未初始化' })
const selectedCategory = ref('textbook')
const fileList = ref([])
const uploading = ref(false)
const loading = ref(false)
const pendingLoading = ref(false)
const activeTab = ref('pending')

const refreshDocuments = async () => {
  loading.value = true
  try {
    const res = await documentsApi.list()
    documents.value = res.data || []
    
    stats.value = { count: documents.value.length, status: '已加载' }
  } catch (error) {
    console.error('获取文档失败:', error)
  } finally {
    loading.value = false
  }
}

const refreshPending = async () => {
  pendingLoading.value = true
  try {
    const res = await documentsApi.pending()
    pendingFiles.value = res.data.files || []
  } catch (error) {
    console.error('获取待审核文件失败:', error)
  } finally {
    pendingLoading.value = false
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
    ElMessage.success('上传成功，等待管理员审核')
    fileList.value = []
    await refreshPending()
    await refreshDocuments()
  } catch (error) {
    ElMessage.error('上传失败: ' + error.message)
  } finally {
    uploading.value = false
  }
}

const approveFile = async (file) => {
  try {
    await ElMessageBox.confirm(`确定要批准文件 "${file.original_filename}" 吗？`, '确认批准')
    await documentsApi.approve(file.pending_id)
    ElMessage.success('文件已批准入库')
    await refreshPending()
    await refreshDocuments()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批准失败: ' + error.message)
    }
  }
}

const rejectFile = async (file) => {
  try {
    await ElMessageBox.confirm(`确定要拒绝文件 "${file.original_filename}" 吗？文件将被删除。`, '确认拒绝')
    await documentsApi.reject(file.pending_id)
    ElMessage.success('文件已拒绝并删除')
    await refreshPending()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('拒绝失败: ' + error.message)
    }
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

const formatSize = (bytes) => {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + 'B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + 'KB'
  return (bytes / 1024 / 1024).toFixed(1) + 'MB'
}

const formatTime = (timestamp) => {
  if (!timestamp) return '-'
  const date = new Date(timestamp * 1000)
  return date.toLocaleString('zh-CN')
}

onMounted(() => {
  refreshPending()
  refreshDocuments()
})
</script>

<style scoped>
.library-page {
  max-width: 1200px;
  margin: 0 auto;
}
</style>
