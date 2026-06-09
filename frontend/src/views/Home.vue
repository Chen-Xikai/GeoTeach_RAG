<template>
  <div class="home-page">
    <div class="page-header">
      <h1>🌍 GeoTeach AI Agent - 地理教学助手</h1>
      <p>智能文档管理 · AI内容生成 · 知识问答</p>
    </div>

    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: #ede9fe;">
            <el-icon :size="24" color="#7c3aed"><Document /></el-icon>
          </div>
          <div class="stat-info">
            <h3>{{ stats.documentCount || 0 }}</h3>
            <p>文档总数</p>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: #dbeafe;">
            <el-icon :size="24" color="#2563eb"><Collection /></el-icon>
          </div>
          <div class="stat-info">
            <h3>{{ stats.chapterCount || 0 }}</h3>
            <p>教材章节</p>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: #fce7f3;">
            <el-icon :size="24" color="#db2777"><Edit /></el-icon>
          </div>
          <div class="stat-info">
            <h3>{{ stats.generatedCount || 0 }}</h3>
            <p>生成内容</p>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: #d1fae5;">
            <el-icon :size="24" color="#059669"><CircleCheck /></el-icon>
          </div>
          <div class="stat-info">
            <h3>{{ stats.status || '正常' }}</h3>
            <p>系统状态</p>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :span="16">
        <div class="content-card">
          <h2 style="margin-bottom: 16px;">🚀 快速操作</h2>
          <el-row :gutter="16">
            <el-col :span="8">
              <div class="action-card" @click="$router.push('/library')">
                <el-icon :size="40" color="#7c3aed"><Collection /></el-icon>
                <div>
                  <h3>资料库管理</h3>
                  <p>上传和管理教学资料</p>
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="action-card" @click="$router.push('/generator')">
                <el-icon :size="40" color="#2563eb"><Edit /></el-icon>
                <div>
                  <h3>内容生成</h3>
                  <p>生成说课稿、教案等</p>
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="action-card" @click="$router.push('/qa')">
                <el-icon :size="40" color="#059669"><ChatDotRound /></el-icon>
                <div>
                  <h3>智能问答</h3>
                  <p>解答教学问题</p>
                </div>
              </div>
            </el-col>
          </el-row>
          <el-row :gutter="16" style="margin-top: 16px;">
            <el-col :span="8">
              <div class="action-card" @click="$router.push('/library')">
                <el-icon :size="40" color="#d97706"><Download /></el-icon>
                <div>
                  <h3>网页爬取</h3>
                  <p>抓取网页内容入库</p>
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="action-card" @click="$router.push('/settings')">
                <el-icon :size="40" color="#6b7280"><Setting /></el-icon>
                <div>
                  <h3>系统设置</h3>
                  <p>配置和管理</p>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
      </el-col>
      
      <el-col :span="8">
        <div class="content-card">
          <h2 style="margin-bottom: 16px;">📖 教材支持</h2>
          <el-collapse>
            <el-collapse-item title="初中地理" name="junior">
              <ul class="grade-list">
                <li>七年级上册、下册</li>
                <li>八年级上册、下册</li>
              </ul>
            </el-collapse-item>
            <el-collapse-item title="高中地理" name="senior">
              <ul class="grade-list">
                <li>必修第一册、第二册</li>
                <li>选择性必修第一册、第二册、第三册</li>
              </ul>
            </el-collapse-item>
          </el-collapse>
        </div>
        
        <div class="content-card" style="margin-top: 16px;">
          <h2 style="margin-bottom: 16px;">ℹ️ 系统信息</h2>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="版本">{{ systemInfo.version || '加载中...' }}</el-descriptions-item>
            <el-descriptions-item label="Embedding">SiliconFlow BGE</el-descriptions-item>
            <el-descriptions-item label="Rerank">SiliconFlow BGE-reranker</el-descriptions-item>
            <el-descriptions-item label="向量库">Milvus Lite</el-descriptions-item>
            <el-descriptions-item label="LLM">Qwen2.5-7B</el-descriptions-item>
          </el-descriptions>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { systemApi, documentsApi } from '@/api'

const stats = ref({
  documentCount: 0,
  chapterCount: 0,
  generatedCount: 0,
  status: '正常'
})

const systemInfo = ref({
  version: ''
})

onMounted(async () => {
  try {
    const statusRes = await systemApi.status()
    if (statusRes.data) {
      stats.value.documentCount = statusRes.data.database?.count || 0
      stats.value.status = statusRes.data.database?.status || '正常'
      systemInfo.value.version = statusRes.data.version || ''
    }
  } catch (error) {
    console.error('获取状态失败:', error)
  }
})
</script>

<style scoped>
.home-page {
  max-width: 1200px;
  margin: 0 auto;
}

.stats-row {
  margin-bottom: 24px;
}

.action-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-card:hover {
  background: #f3f4f6;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.action-card h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 4px 0;
  color: #1f2937;
}

.action-card p {
  font-size: 12px;
  color: #6b7280;
  margin: 0;
}

.grade-list {
  padding-left: 20px;
  font-size: 14px;
  color: #4b5563;
}

.grade-list li {
  margin-bottom: 4px;
}
</style>
