<template>
  <div class="history-page">
    <div v-if="!sessionStore.currentSessionId" class="no-session">
      <el-empty description="请先选择一个会话" />
    </div>

    <template v-else>
      <div class="history-header">
        <h3>历史记录</h3>
        <el-button :icon="Refresh" @click="fetchHistory" :loading="loading" text>刷新</el-button>
      </div>

      <div v-if="loading && records.length === 0" class="loading-state">
        <el-skeleton :rows="5" animated />
      </div>

      <div v-else-if="records.length === 0" class="empty-state">
        <el-empty description="暂无历史记录" />
      </div>

      <div v-else class="history-list">
        <el-card
          v-for="record in records"
          :key="record.id"
          class="history-card"
          shadow="hover"
        >
          <div class="record-content">
            <div class="record-images">
              <div class="record-image-item">
                <div class="image-label">内容图</div>
                <el-image
                  :src="getImageUrl(record.original_image_path)"
                  fit="cover"
                  class="record-image"
                  :preview-src-list="[getImageUrl(record.original_image_path)]"
                >
                  <template #error>
                    <div class="image-error"><el-icon><Picture /></el-icon></div>
                  </template>
                </el-image>
              </div>
              <div class="record-image-item">
                <div class="image-label">风格图</div>
                <el-image
                  :src="getImageUrl(record.style_image_path)"
                  fit="cover"
                  class="record-image"
                  :preview-src-list="[getImageUrl(record.style_image_path)]"
                >
                  <template #error>
                    <div class="image-error"><el-icon><Picture /></el-icon></div>
                  </template>
                </el-image>
              </div>
              <div class="record-image-item" v-if="record.result_image_url">
                <div class="image-label">结果图</div>
                <el-image
                  :src="record.result_image_url"
                  fit="cover"
                  class="record-image result"
                  :preview-src-list="[record.result_image_url]"
                >
                  <template #error>
                    <div class="image-error"><el-icon><Picture /></el-icon></div>
                  </template>
                </el-image>
              </div>
            </div>

            <div class="record-info">
              <div class="record-meta">
                <span class="record-time">
                  <el-icon><Clock /></el-icon>
                  {{ formatTime(record.created_at) }}
                </span>
                <el-tag
                  :type="record.api_status === 200 ? 'success' : 'danger'"
                  size="small"
                >
                  {{ record.api_status === 200 ? '成功' : '失败' }}
                </el-tag>
                <span v-if="record.api_duration" class="record-duration">
                  耗时 {{ record.api_duration }}s
                </span>
              </div>
              <div class="record-prompt" v-if="record.prompt">
                <el-text size="small" type="info" truncated>{{ record.prompt }}</el-text>
              </div>
              <div class="record-actions">
                <el-button
                  v-if="record.result_image_url"
                  type="primary"
                  :icon="Download"
                  size="small"
                  text
                  @click="downloadImage(record.result_image_url)"
                >
                  下载
                </el-button>
                <el-popconfirm
                  title="确定删除该记录吗？"
                  confirm-button-text="删除"
                  cancel-button-text="取消"
                  confirm-button-type="danger"
                  @confirm="handleDelete(record.id)"
                >
                  <template #reference>
                    <el-button type="danger" :icon="Delete" size="small" text>
                      删除
                    </el-button>
                  </template>
                </el-popconfirm>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useSessionStore } from '../stores/session'
import { getHistory, deleteHistory } from '../api/style'
import { ElMessage } from 'element-plus'
import { Refresh, Clock, Picture, Download, Delete } from '@element-plus/icons-vue'

const sessionStore = useSessionStore()

const records = ref([])
const loading = ref(false)

async function fetchHistory() {
  if (!sessionStore.currentSessionId) return
  loading.value = true
  try {
    const res = await getHistory(sessionStore.currentSessionId)
    records.value = res.data.records
  } catch (e) {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}

async function handleDelete(recordId) {
  try {
    await deleteHistory(recordId)
    records.value = records.value.filter((r) => r.id !== recordId)
    ElMessage.success('删除成功')
  } catch (e) {
    // handled by interceptor
  }
}

function getImageUrl(path) {
  if (!path) return ''
  const filename = path.split(/[/\\]/).pop()
  return `/uploads/${filename}`
}

function formatTime(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleString('zh-CN')
}

function downloadImage(url) {
  const link = document.createElement('a')
  link.href = url
  link.target = '_blank'
  link.download = 'styled_image.png'
  link.click()
}

watch(() => sessionStore.currentSessionId, () => {
  fetchHistory()
})

onMounted(() => {
  fetchHistory()
})
</script>

<style scoped>
.history-page {
  max-width: 1000px;
  margin: 0 auto;
}

.no-session {
  display: flex;
  justify-content: center;
  padding: 80px 0;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.history-header h3 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.history-card {
  border-radius: 12px;
}

.record-content {
  display: flex;
  gap: 20px;
}

.record-images {
  display: flex;
  gap: 12px;
  flex-shrink: 0;
}

.record-image-item {
  text-align: center;
}

.image-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.record-image {
  width: 100px;
  height: 100px;
  border-radius: 8px;
  overflow: hidden;
}

.record-image.result {
  border: 2px solid #667eea;
}

.image-error {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100px;
  height: 100px;
  background: #f5f7fa;
  color: #c0c4cc;
  font-size: 24px;
}

.record-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.record-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.record-time {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #909399;
}

.record-duration {
  font-size: 13px;
  color: #909399;
}

.record-prompt {
  max-width: 400px;
}

.record-actions {
  margin-top: auto;
  display: flex;
  gap: 8px;
}

.loading-state,
.empty-state {
  padding: 40px 0;
}

@media (max-width: 768px) {
  .record-content {
    flex-direction: column;
  }

  .record-images {
    justify-content: center;
  }
}
</style>
