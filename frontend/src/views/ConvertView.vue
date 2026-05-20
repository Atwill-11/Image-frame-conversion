<template>
  <div class="convert-page">
    <div v-if="!sessionStore.currentSessionId" class="no-session">
      <el-empty description="请先创建或选择一个会话">
        <el-button type="primary" @click="sessionStore.addSession()">创建会话</el-button>
      </el-empty>
    </div>

    <template v-else>
      <el-row :gutter="24">
        <el-col :xs="24" :lg="16">
          <el-card class="upload-card">
            <template #header>
              <div class="card-header">
                <span>上传图片</span>
                <el-tag type="info" size="small">支持 JPG / PNG 格式</el-tag>
              </div>
            </template>

            <el-row :gutter="20">
              <el-col :span="12">
                <div class="upload-area">
                  <div class="upload-label">内容图片</div>
                  <el-upload
                    class="image-uploader"
                    :auto-upload="false"
                    :show-file-list="false"
                    accept=".jpg,.jpeg,.png,.webp,.bmp"
                    :on-change="(file) => handleFileChange(file, 'content')"
                  >
                    <div v-if="contentPreview" class="preview-wrapper">
                      <img :src="contentPreview" class="preview-image" />
                      <div class="preview-overlay">点击更换</div>
                    </div>
                    <div v-else class="upload-placeholder">
                      <el-icon :size="40"><Plus /></el-icon>
                      <span>上传内容图片</span>
                    </div>
                  </el-upload>
                </div>
              </el-col>
              <el-col :span="12">
                <div class="upload-area">
                  <div class="upload-label">风格图片</div>
                  <el-upload
                    class="image-uploader"
                    :auto-upload="false"
                    :show-file-list="false"
                    accept=".jpg,.jpeg,.png,.webp,.bmp"
                    :on-change="(file) => handleFileChange(file, 'style')"
                  >
                    <div v-if="stylePreview" class="preview-wrapper">
                      <img :src="stylePreview" class="preview-image" />
                      <div class="preview-overlay">点击更换</div>
                    </div>
                    <div v-else class="upload-placeholder">
                      <el-icon :size="40"><Plus /></el-icon>
                      <span>上传风格图片</span>
                    </div>
                  </el-upload>
                </div>
              </el-col>
            </el-row>

            <div class="prompt-section">
              <div class="prompt-label">转换提示词</div>
              <el-input
                v-model="prompt"
                type="textarea"
                :rows="2"
                placeholder="请输入风格转换提示词"
              />
            </div>

            <div class="action-section">
              <el-button
                type="primary"
                size="large"
                :loading="converting"
                :disabled="!contentFile || !styleFile"
                @click="handleConvert"
              >
                {{ converting ? '转换中...' : '开始风格转换' }}
              </el-button>
            </div>
          </el-card>
        </el-col>

        <el-col :xs="24" :lg="8">
          <el-card class="result-card">
            <template #header>
              <span>转换结果</span>
            </template>
            <div v-if="resultImage" class="result-wrapper">
              <img :src="resultImage" class="result-image" />
              <div class="result-actions">
                <el-button type="primary" :icon="Download" @click="downloadResult" size="small">
                  下载图片
                </el-button>
              </div>
              <div class="result-info" v-if="lastRecord">
                <el-descriptions :column="1" size="small" border>
                  <el-descriptions-item label="耗时">{{ lastRecord.api_duration }}秒</el-descriptions-item>
                  <el-descriptions-item label="状态">
                    <el-tag :type="lastRecord.api_status === 200 ? 'success' : 'danger'" size="small">
                      {{ lastRecord.api_status === 200 ? '成功' : '失败' }}
                    </el-tag>
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </div>
            <div v-else class="result-empty">
              <el-empty description="转换结果将在此显示" :image-size="80" />
            </div>
          </el-card>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useSessionStore } from '../stores/session'
import { styleConvert } from '../api/style'
import { ElMessage } from 'element-plus'
import { Plus, Download } from '@element-plus/icons-vue'

const sessionStore = useSessionStore()

const contentFile = ref(null)
const styleFile = ref(null)
const contentPreview = ref('')
const stylePreview = ref('')
const prompt = ref('请将第一张图片的风格转换为第二张图片的艺术风格，保持人物和构图等内容主体不变。')
const converting = ref(false)
const resultImage = ref('')
const lastRecord = ref(null)

function handleFileChange(uploadFile, type) {
  const raw = uploadFile.raw
  if (!raw) return

  const reader = new FileReader()
  reader.onload = (e) => {
    if (type === 'content') {
      contentFile.value = raw
      contentPreview.value = e.target.result
    } else {
      styleFile.value = raw
      stylePreview.value = e.target.result
    }
  }
  reader.readAsDataURL(raw)
}

async function handleConvert() {
  if (!contentFile.value || !styleFile.value) {
    ElMessage.warning('请上传内容图片和风格图片')
    return
  }

  converting.value = true
  resultImage.value = ''
  lastRecord.value = null

  try {
    const formData = new FormData()
    formData.append('session_id', sessionStore.currentSessionId)
    formData.append('content_image', contentFile.value)
    formData.append('style_image', styleFile.value)
    formData.append('prompt', prompt.value)

    const res = await styleConvert(formData)
    lastRecord.value = res.data

    if (res.data.result_image_url) {
      resultImage.value = res.data.result_image_url
      ElMessage.success('风格转换完成')
    } else {
      ElMessage.warning('转换完成但未生成图片，请重试')
    }
  } catch (e) {
    // handled by interceptor
  } finally {
    converting.value = false
  }
}

function downloadResult() {
  if (!resultImage.value) return
  const link = document.createElement('a')
  link.href = resultImage.value
  link.target = '_blank'
  link.download = 'styled_image.png'
  link.click()
}
</script>

<style scoped>
.convert-page {
  max-width: 1200px;
  margin: 0 auto;
}

.no-session {
  display: flex;
  justify-content: center;
  padding: 80px 0;
}

.upload-card,
.result-card {
  border-radius: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.upload-area {
  margin-bottom: 16px;
}

.upload-label {
  font-size: 14px;
  font-weight: 500;
  color: #606266;
  margin-bottom: 8px;
}

.image-uploader :deep(.el-upload) {
  width: 100%;
  border: 2px dashed #dcdfe6;
  border-radius: 12px;
  cursor: pointer;
  transition: border-color 0.3s;
  overflow: hidden;
}

.image-uploader :deep(.el-upload:hover) {
  border-color: #667eea;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px 20px;
  color: #909399;
  font-size: 14px;
}

.preview-wrapper {
  position: relative;
  width: 100%;
}

.preview-image {
  width: 100%;
  height: 200px;
  object-fit: cover;
  display: block;
}

.preview-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 14px;
  opacity: 0;
  transition: opacity 0.3s;
}

.preview-wrapper:hover .preview-overlay {
  opacity: 1;
}

.prompt-section {
  margin: 20px 0;
}

.prompt-label {
  font-size: 14px;
  font-weight: 500;
  color: #606266;
  margin-bottom: 8px;
}

.action-section {
  text-align: center;
  padding: 8px 0;
}

.action-section .el-button {
  width: 240px;
  font-size: 16px;
  height: 48px;
  border-radius: 24px;
}

.result-wrapper {
  text-align: center;
}

.result-image {
  max-width: 100%;
  max-height: 400px;
  border-radius: 8px;
  object-fit: contain;
}

.result-actions {
  margin-top: 12px;
}

.result-info {
  margin-top: 16px;
  text-align: left;
}

.result-empty {
  padding: 40px 0;
}
</style>
