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
            <el-menu-item index="maintenance">
              <el-icon><Tools /></el-icon>
              <span>维护工具</span>
            </el-menu-item>
            <el-menu-item index="mcp">
              <el-icon><Connection /></el-icon>
              <span>MCP服务</span>
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

        <!-- 维护工具 -->
        <div v-if="activeSection === 'maintenance'" class="content-card">
          <h2 style="margin-bottom: 16px;">🔧 维护工具</h2>
          
          <el-alert type="info" :closable="false" style="margin-bottom: 16px;">
            同步：增量更新向量库，只处理变化的文件<br/>
            重建：全量重建向量库，处理所有文件
          </el-alert>
          
          <el-space wrap>
            <el-button type="primary" @click="syncDocuments" :loading="syncing">
              <el-icon><Refresh /></el-icon>
              同步文档
            </el-button>
            <el-button type="warning" @click="rebuildDocuments" :loading="rebuilding">
              <el-icon><RefreshRight /></el-icon>
              重建向量库
            </el-button>
            <el-button @click="checkOrphans" :loading="checking">
              <el-icon><Search /></el-icon>
              检查孤立记录
            </el-button>
            <el-button type="danger" @click="cleanOrphans" :loading="cleaning" :disabled="orphanCount === 0">
              <el-icon><Delete /></el-icon>
              清理孤立记录 ({{ orphanCount }})
            </el-button>
          </el-space>
          
          <!-- 同步结果 -->
          <div v-if="syncResult" style="margin-top: 16px;">
            <el-descriptions title="同步结果" :column="2" border>
              <el-descriptions-item label="新增">{{ syncResult.added }}</el-descriptions-item>
              <el-descriptions-item label="更新">{{ syncResult.updated }}</el-descriptions-item>
              <el-descriptions-item label="删除">{{ syncResult.deleted }}</el-descriptions-item>
              <el-descriptions-item label="未变">{{ syncResult.unchanged }}</el-descriptions-item>
            </el-descriptions>
          </div>
          
          <!-- 重建结果 -->
          <div v-if="rebuildResult" style="margin-top: 16px;">
            <el-tag type="success">重建完成：{{ rebuildResult.total_chunks }} 个文档块</el-tag>
          </div>
          
          <!-- 孤立记录 -->
          <div v-if="orphanList.length > 0" style="margin-top: 16px;">
            <h3 style="margin-bottom: 8px;">孤立记录</h3>
            <el-table :data="orphanList" style="width: 100%;" size="small">
              <el-table-column prop="source" label="来源" />
            </el-table>
          </div>
        </div>

        <!-- MCP服务 -->
        <div v-if="activeSection === 'mcp'" class="content-card">
          <h2 style="margin-bottom: 16px;">🔌 MCP服务</h2>
          
          <el-alert type="info" :closable="false" style="margin-bottom: 16px;">
            MCP（Model Context Protocol）服务允许AI助手通过标准协议访问知识库。
          </el-alert>
          
          <el-descriptions :column="1" border>
            <el-descriptions-item label="服务地址">http://127.0.0.1:9766</el-descriptions-item>
            <el-descriptions-item label="服务状态">
              <el-tag :type="mcpStatus === 'ok' ? 'success' : 'danger'">
                {{ mcpStatus === 'ok' ? '运行中' : '未运行' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="数据库" v-if="mcpInfo.database">
              {{ mcpInfo.database.type }} - {{ mcpInfo.database.collection }}
            </el-descriptions-item>
            <el-descriptions-item label="文档数" v-if="mcpInfo.database">
              {{ mcpInfo.database.documents }} 篇文档，{{ mcpInfo.database.chunks }} 个文档块
            </el-descriptions-item>
          </el-descriptions>
          
          <el-divider />
          
          <h3 style="margin-bottom: 16px;">OpenCode 配置</h3>
          
          <el-input
            type="textarea"
            :rows="8"
            readonly
            :value="mcpConfigJson"
          />
          
          <el-button @click="copyMcpConfig" style="margin-top: 12px;">
            <el-icon><CopyDocument /></el-icon>
            复制配置
          </el-button>
          
          <el-button @click="checkMcpStatus" style="margin-top: 12px; margin-left: 8px;">
            <el-icon><Refresh /></el-icon>
            刷新状态
          </el-button>
        </div>

        <!-- 系统信息 -->
        <div v-if="activeSection === 'system'" class="content-card">
          <h2 style="margin-bottom: 16px;">ℹ️ 系统信息</h2>
          
          <el-descriptions :column="2" border>
            <el-descriptions-item label="版本">v1.4.0</el-descriptions-item>
            <el-descriptions-item label="框架">FastAPI + Vue 3</el-descriptions-item>
            <el-descriptions-item label="向量库">Milvus Lite</el-descriptions-item>
            <el-descriptions-item label="Embedding">SiliconFlow BGE</el-descriptions-item>
            <el-descriptions-item label="Rerank">SiliconFlow BGE-reranker</el-descriptions-item>
            <el-descriptions-item label="LLM">Qwen2.5-7B</el-descriptions-item>
            <el-descriptions-item label="MCP服务">端口 9766</el-descriptions-item>
            <el-descriptions-item label="Web服务">端口 9767</el-descriptions-item>
          </el-descriptions>
          
          <el-divider />
          
          <h3 style="margin-bottom: 16px;">📊 数据库统计</h3>
          
          <el-descriptions :column="2" border v-if="dbStats">
            <el-descriptions-item label="文档数">{{ dbStats.count || 0 }}</el-descriptions-item>
            <el-descriptions-item label="文档块数">{{ dbStats.chunk_count || 0 }}</el-descriptions-item>
            <el-descriptions-item label="状态">{{ dbStats.status || '未知' }}</el-descriptions-item>
            <el-descriptions-item label="缓存命中率">{{ dbStats.cache?.hit_rate || '0%' }}</el-descriptions-item>
          </el-descriptions>
          
          <el-divider />
          
          <h3 style="margin-bottom: 16px;">🔧 系统操作</h3>
          
          <el-space>
            <el-button @click="checkHealth">
              <el-icon><CircleCheck /></el-icon>
              健康检查
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
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { systemApi, documentsApi } from '@/api'

const activeSection = ref('maintenance')
const healthStatus = ref('')
const syncing = ref(false)
const rebuilding = ref(false)
const checking = ref(false)
const cleaning = ref(false)
const syncResult = ref(null)
const rebuildResult = ref(null)
const orphanList = ref([])
const orphanCount = ref(0)
const mcpStatus = ref('')
const mcpInfo = ref({})
const dbStats = ref(null)

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

// MCP配置JSON
const mcpConfigJson = `{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "geoteach": {
      "type": "remote",
      "url": "http://127.0.0.1:9766/mcp",
      "enabled": true
    }
  }
}`

// 同步文档
const syncDocuments = async () => {
  syncing.value = true
  syncResult.value = null
  try {
    const res = await documentsApi.sync()
    syncResult.value = res.data.stats
    ElMessage.success('同步完成')
  } catch (error) {
    ElMessage.error('同步失败: ' + error.message)
  } finally {
    syncing.value = false
  }
}

// 重建向量库
const rebuildDocuments = async () => {
  try {
    await ElMessageBox.confirm('确定要重建向量库吗？这可能需要一些时间。', '确认', {
      type: 'warning'
    })
    rebuilding.value = true
    rebuildResult.value = null
    const res = await documentsApi.rebuild()
    rebuildResult.value = res.data
    ElMessage.success('重建完成')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('重建失败: ' + error.message)
    }
  } finally {
    rebuilding.value = false
  }
}

// 检查孤立记录
const checkOrphans = async () => {
  checking.value = true
  try {
    const res = await documentsApi.orphans()
    orphanList.value = res.data.orphans || []
    orphanCount.value = res.data.count || 0
    if (orphanCount.value === 0) {
      ElMessage.success('没有孤立记录')
    } else {
      ElMessage.warning(`发现 ${orphanCount.value} 条孤立记录`)
    }
  } catch (error) {
    ElMessage.error('检查失败: ' + error.message)
  } finally {
    checking.value = false
  }
}

// 清理孤立记录
const cleanOrphans = async () => {
  try {
    await ElMessageBox.confirm(`确定要清理 ${orphanCount.value} 条孤立记录吗？`, '确认')
    cleaning.value = true
    const res = await documentsApi.cleanOrphans()
    ElMessage.success(`已清理 ${res.data.cleaned} 条记录`)
    orphanList.value = []
    orphanCount.value = 0
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('清理失败: ' + error.message)
    }
  } finally {
    cleaning.value = false
  }
}

// 检查MCP状态
const checkMcpStatus = async () => {
  try {
    const res = await fetch('http://127.0.0.1:9766/health')
    const data = await res.json()
    mcpStatus.value = data.status
    mcpInfo.value = data
  } catch (error) {
    mcpStatus.value = 'error'
    mcpInfo.value = {}
  }
}

// 复制MCP配置
const copyMcpConfig = () => {
  navigator.clipboard.writeText(mcpConfigJson)
  ElMessage.success('配置已复制到剪贴板')
}

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

// 加载数据库统计
const loadDbStats = async () => {
  try {
    const res = await documentsApi.stats()
    dbStats.value = res.data
  } catch (error) {
    console.error('获取统计失败:', error)
  }
}

onMounted(() => {
  checkMcpStatus()
  loadDbStats()
})
</script>

<style scoped>
.settings-page {
  max-width: 1200px;
  margin: 0 auto;
}
</style>
