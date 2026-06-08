<template>
  <div class="library-page">
    <div class="page-header">
      <h1>📚 资料库管理</h1>
      <p>上传和管理教学资料</p>
    </div>

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
          <div class="stat-icon" style="background: #d1fae5;">
            <el-icon :size="24" color="#059669"><CircleCheck /></el-icon>
          </div>
          <div class="stat-info">
            <h3>{{ importedCount }}</h3>
            <p>已入库</p>
          </div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card">
          <div class="stat-icon" style="background: #fef3c7;">
            <el-icon :size="24" color="#d97706"><Clock /></el-icon>
          </div>
          <div class="stat-info">
            <h3>{{ stats.chunks || 0 }}</h3>
            <p>总切片数</p>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :span="6">
        <div class="content-card">
          <h3 style="margin-bottom: 16px;">📤 上传资料</h3>
          
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
            <div style="font-size: 12px; color: #6b7280;">支持 PDF, DOCX, TXT, MD, PPTX</div>
          </el-upload>
          
          <el-button 
            type="primary" 
            style="width: 100%; margin-top: 16px;"
            :loading="uploading"
            @click="uploadFiles"
          >
            上传并入库
          </el-button>
        </div>
      </el-col>

      <el-col :span="18">
        <div class="content-card">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <h3>📋 已入库文档</h3>
            <el-button @click="refreshDocuments">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
          
          <el-table :data="documents" style="width: 100%;" v-loading="loading" row-key="path">
            <el-table-column label="文件名" min-width="250">
              <template #default="{ row }">
                <div style="display: flex; align-items: center; gap: 8px; cursor: pointer; color: #409eff;" @click="viewDetail(row)">
                  <el-icon color="#059669"><Document /></el-icon>
                  <span>{{ row.name }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'imported' ? 'success' : row.status === 'orphan' ? 'warning' : 'info'" size="small">
                  {{ row.status === 'imported' ? '已入库' : row.status === 'orphan' ? '孤立' : '未导入' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="chunks" label="切片" width="80" />
            <el-table-column label="操作" width="220">
              <template #default="{ row }">
                <el-button size="small" type="primary" @click="viewDetail(row)">
                  查看详情
                </el-button>
                <el-button size="small" type="warning" @click="reimportDoc(row)">
                  重新切片
                </el-button>
                <el-button size="small" type="danger" @click="deleteDoc(row)">
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

    <!-- 文档详情对话框 -->
    <el-dialog v-model="detailVisible" title="文档详情" width="70%" top="5vh">
      <div v-if="detailLoading" v-loading="true" style="height: 200px;"></div>
      <div v-else-if="detailInfo">
        <el-descriptions :column="2" border style="margin-bottom: 16px;">
          <el-descriptions-item label="文件名">{{ detailInfo.source_name }}</el-descriptions-item>
          <el-descriptions-item label="切片数">{{ detailInfo.chunks }}</el-descriptions-item>
          <el-descriptions-item label="分类">{{ detailInfo.category || '未分类' }}</el-descriptions-item>
          <el-descriptions-item label="状态">已入库</el-descriptions-item>
        </el-descriptions>
        
        <h3 style="margin-bottom: 12px;">📄 切片内容（共 {{ detailChunks.length }} 个）</h3>
        
        <el-scrollbar max-height="400px">
          <div v-for="chunk in detailChunks" :key="chunk.index" class="chunk-item">
            <div class="chunk-header">
              <el-tag size="small" type="info">#{{ chunk.index }}</el-tag>
              <span style="color: #6b7280; font-size: 12px;">{{ chunk.content.length }} 字</span>
            </div>
            <div class="chunk-content">{{ chunk.content }}</div>
          </div>
        </el-scrollbar>
        
        <div v-if="detailChunks.length === 0" style="text-align: center; padding: 40px; color: #6b7280;">
          <p>该文档没有切片记录</p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { documentsApi } from '@/api'

const documents = ref([])
const stats = ref({ count: 0, chunks: 0, status: '未初始化' })
const selectedCategory = ref('textbook')
const fileList = ref([])
const uploading = ref(false)
const loading = ref(false)

// 详情对话框
const detailVisible = ref(false)
const detailLoading = ref(false)
const detailInfo = ref(null)
const detailChunks = ref([])

const importedCount = computed(() => {
  return documents.value.filter(d => d.status === 'imported').length
})

const refreshDocuments = async () => {
  loading.value = true
  try {
    const res = await documentsApi.list()
    // 只显示已入库文档
    documents.value = (res.data || []).filter(d => d.status === 'imported')
    
    const statsRes = await documentsApi.stats()
    const s = statsRes.data || {}
    stats.value = { 
      count: documents.value.length, 
      chunks: s.chunk_count || 0,
      status: '已加载' 
    }
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
    ElMessage.success(`上传成功：${fileList.value.length} 个文件已入库`)
    fileList.value = []
    await refreshDocuments()
  } catch (error) {
    ElMessage.error('上传失败: ' + error.message)
  } finally {
    uploading.value = false
  }
}

const viewDetail = async (doc) => {
  detailVisible.value = true
  detailLoading.value = true
  detailInfo.value = null
  detailChunks.value = []
  
  try {
    const [infoRes, chunksRes] = await Promise.all([
      documentsApi.detail(doc.path),
      documentsApi.chunks(doc.path)
    ])
    detailInfo.value = infoRes.data
    detailChunks.value = chunksRes.data?.chunks || []
  } catch (error) {
    ElMessage.error('获取详情失败: ' + error.message)
  } finally {
    detailLoading.value = false
  }
}

const deleteDoc = async (doc) => {
  try {
    await ElMessageBox.confirm(`确定要删除 "${doc.name}" 吗？文件将从磁盘移除。`, '确认删除', { type: 'warning' })
    await documentsApi.delete(doc.path)
    ElMessage.success('删除成功')
    await refreshDocuments()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + error.message)
    }
  }
}

const reimportDoc = async (doc) => {
  try {
    await ElMessageBox.confirm(`确定要重新切片 "${doc.name}" 吗？`, '确认重新切片', { type: 'info' })
    await documentsApi.importFiles([doc.path])
    ElMessage.success('重新切片成功')
    await refreshDocuments()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('重新切片失败: ' + error.message)
    }
  }
}

onMounted(() => {
  refreshDocuments()
})
</script>

<style scoped>
.library-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.page-header p {
  color: #6b7280;
  font-size: 14px;
  margin: 0;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-info h3 {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  color: #1f2937;
}

.stat-info p {
  font-size: 12px;
  color: #6b7280;
  margin: 4px 0 0 0;
}

.content-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.chunk-item {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
}

.chunk-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.chunk-content {
  font-size: 13px;
  color: #374151;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 150px;
  overflow-y: auto;
}
</style>
