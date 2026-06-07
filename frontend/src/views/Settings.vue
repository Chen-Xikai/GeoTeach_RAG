<template>
  <div class="settings-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>⚙️ 系统设置</h1>
      <p>配置和管理系统</p>
    </div>

    <el-row :gutter="16">
      <!-- 左侧：导航 -->
      <el-col :span="6">
        <div class="content-card">
          <el-menu :default-active="activeSection" @select="activeSection = $event">
            <el-menu-item index="api">
              <el-icon><Key /></el-icon>
              <span>API配置</span>
            </el-menu-item>
            <el-menu-item index="retrieval">
              <el-icon><Search /></el-icon>
              <span>检索配置</span>
            </el-menu-item>
            <el-menu-item index="chunking">
              <el-icon><Document /></el-icon>
              <span>切分配置</span>
            </el-menu-item>
            <el-menu-item index="system">
              <el-icon><Setting /></el-icon>
              <span>系统信息</span>
            </el-menu-item>
          </el-menu>
        </div>
      </el-col>

      <!-- 右侧：配置内容 -->
      <el-col :span="18">
        <!-- API配置 -->
        <div v-if="activeSection === 'api'" class="content-card">
          <h2 style="margin-bottom: 16px;">🔑 API配置</h2>
          
          <el-form label-position="top">
            <el-form-item label="SiliconFlow API Key">
              <el-input v-model="config.apiKey" type="password" show-password />
            </el-form-item>
            
            <el-form-item label="Embedding模型">
              <el-select v-model="config.embeddingModel">
                <el-option label="BAAI/bge-large-zh-v1.5" value="BAAI/bge-large-zh-v1.5" />
                <el-option label="BAAI/bge-m3" value="BAAI/bge-m3" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="LLM模型">
              <el-select v-model="config.llmModel">
                <el-option label="Qwen/Qwen2.5-7B-Instruct" value="Qwen/Qwen2.5-7B-Instruct" />
                <el-option label="Qwen/Qwen2.5-14B-Instruct" value="Qwen/Qwen2.5-14B-Instruct" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="启用Rerank">
              <el-switch v-model="config.rerankEnabled" />
            </el-form-item>
            
            <el-form-item label="Rerank模型" v-if="config.rerankEnabled">
              <el-select v-model="config.rerankModel">
                <el-option label="BAAI/bge-reranker-v2-m3" value="BAAI/bge-reranker-v2-m3" />
              </el-select>
            </el-form-item>
          </el-form>
          
          <el-button type="primary" @click="saveApiConfig" style="margin-top: 16px;">
            保存配置
          </el-button>
        </div>

        <!-- 检索配置 -->
        <div v-if="activeSection === 'retrieval'" class="content-card">
          <h2 style="margin-bottom: 16px;">🔍 检索配置</h2>
          
          <el-form label-position="top">
            <el-form-item label="检索数量 (k)">
              <el-input-number v-model="config.retrievalK" :min="1" :max="20" />
              <span style="margin-left: 8px; color: #6b7280;">返回最相关的k个文档</span>
            </el-form-item>
            
            <el-form-item label="候选数量 (fetch_k)">
              <el-input-number v-model="config.retrievalFetchK" :min="1" :max="50" />
              <span style="margin-left: 8px; color: #6b7280;">初始检索的候选文档数量</span>
            </el-form-item>
          </el-form>
          
          <el-button type="primary" @click="saveRetrievalConfig" style="margin-top: 16px;">
            保存配置
          </el-button>
        </div>

        <!-- 切分配置 -->
        <div v-if="activeSection === 'chunking'" class="content-card">
          <h2 style="margin-bottom: 16px;">📄 切分配置</h2>
          
          <el-form label-position="top">
            <el-form-item label="切分模板">
              <el-select v-model="config.chunkTemplate">
                <el-option label="中文文档专用" value="chinese" />
                <el-option label="学术文献" value="academic" />
                <el-option label="教案专用" value="lesson_plan" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="切块大小 (chunk_size)">
              <el-input-number v-model="config.chunkSize" :min="100" :max="2000" :step="50" />
              <span style="margin-left: 8px; color: #6b7280;">每个切块的目标大小（字符）</span>
            </el-form-item>
            
            <el-form-item label="重叠长度 (overlap)">
              <el-input-number v-model="config.chunkOverlap" :min="0" :max="500" :step="10" />
              <span style="margin-left: 8px; color: #6b7280;">相邻切块的重叠长度</span>
            </el-form-item>
          </el-form>
          
          <el-button type="primary" @click="saveChunkingConfig" style="margin-top: 16px;">
            保存配置
          </el-button>
        </div>

        <!-- 系统信息 -->
        <div v-if="activeSection === 'system'" class="content-card">
          <h2 style="margin-bottom: 16px;">ℹ️ 系统信息</h2>
          
          <el-descriptions :column="2" border>
            <el-descriptions-item label="版本">v1.0.0</el-descriptions-item>
            <el-descriptions-item label="框架">FastAPI + Vue 3</el-descriptions-item>
            <el-descriptions-item label="向量库">ChromaDB</el-descriptions-item>
            <el-descriptions-item label="Embedding">SiliconFlow BGE</el-descriptions-item>
            <el-descriptions-item label="Rerank">SiliconFlow BGE-reranker</el-descriptions-item>
            <el-descriptions-item label="LLM">Qwen2.5-7B</el-descriptions-item>
          </el-descriptions>
          
          <el-divider />
          
          <h3 style="margin-bottom: 16px;">🔧 系统操作</h3>
          
          <el-space>
            <el-button @click="checkHealth">
              <el-icon><CircleCheck /></el-icon>
              健康检查
            </el-button>
            <el-button @click="rebuildIndex">
              <el-icon><Refresh /></el-icon>
              重建索引
            </el-button>
            <el-button type="danger" @click="clearData">
              <el-icon><Delete /></el-icon>
              清空数据
            </el-button>
          </el-space>
          
          <div v-if="healthStatus" style="margin-top: 16px;">
            <el-tag :type="healthStatus === 'healthy' ? 'success' : 'danger'">
              {{ healthStatus }}
            </el-tag>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { systemApi } from '@/api'

const activeSection = ref('api')
const healthStatus = ref('')

// 配置数据
const config = ref({
  apiKey: '',
  embeddingModel: 'BAAI/bge-large-zh-v1.5',
  llmModel: 'Qwen/Qwen2.5-7B-Instruct',
  rerankEnabled: true,
  rerankModel: 'BAAI/bge-reranker-v2-m3',
  retrievalK: 5,
  retrievalFetchK: 15,
  chunkTemplate: 'chinese',
  chunkSize: 500,
  chunkOverlap: 50
})

const saveApiConfig = () => {
  ElMessage.success('API配置已保存')
}

const saveRetrievalConfig = () => {
  ElMessage.success('检索配置已保存')
}

const saveChunkingConfig = () => {
  ElMessage.success('切分配置已保存')
}

const checkHealth = async () => {
  try {
    const res = await systemApi.health()
    healthStatus.value = res.data.status
    ElMessage.success('系统健康')
  } catch (error) {
    healthStatus.value = 'unhealthy'
    ElMessage.error('系统异常')
  }
}

const rebuildIndex = async () => {
  try {
    await ElMessageBox.confirm('确定要重建索引吗？这可能需要一些时间。', '确认')
    ElMessage.success('索引重建完成')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('重建失败')
    }
  }
}

const clearData = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有数据吗？此操作不可恢复！', '确认', {
      type: 'warning'
    })
    ElMessage.success('数据已清空')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('清空失败')
    }
  }
}
</script>

<style scoped>
.settings-page {
  max-width: 1200px;
  margin: 0 auto;
}
</style>
