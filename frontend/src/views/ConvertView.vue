<template>
  <div class="convert-page">
    <div v-if="!sessionStore.currentSessionId" class="no-session">
      <el-empty description="请先创建或选择一个会话">
        <el-button type="primary" @click="sessionStore.addSession()">创建会话</el-button>
      </el-empty>
    </div>

    <template v-else>
      <el-card class="history-card">
        <template #header>
          <div class="history-header">
            <span>历史记录</span>
            <el-button :icon="Refresh" @click="fetchHistory" :loading="historyLoading" text size="small">刷新</el-button>
          </div>
        </template>

        <div v-if="historyLoading && historyRecords.length === 0" class="history-loading">
          <el-skeleton :rows="4" animated />
        </div>

        <div v-else-if="historyRecords.length === 0" class="history-empty">
          <el-empty description="暂无历史记录，开始您的第一次风格转换吧" :image-size="80" />
        </div>

        <div v-else class="history-list">
          <div v-for="record in historyRecords" :key="record.id" class="history-item">
            <div class="history-images">
              <div class="image-block">
                <el-image
                  :src="getImageUrl(record.original_image_path)"
                  fit="cover"
                  class="history-image"
                  :preview-src-list="[getImageUrl(record.original_image_path)]"
                >
                  <template #error><div class="image-error"><el-icon><Picture /></el-icon></div></template>
                </el-image>
                <div class="image-label">内容图</div>
              </div>
              <el-icon class="arrow-icon"><Right /></el-icon>
              <div class="image-block">
                <el-image
                  :src="getImageUrl(record.style_image_path)"
                  fit="cover"
                  class="history-image"
                  :preview-src-list="[getImageUrl(record.style_image_path)]"
                >
                  <template #error><div class="image-error"><el-icon><Picture /></el-icon></div></template>
                </el-image>
                <div class="image-label">风格图</div>
              </div>
              <el-icon class="arrow-icon"><Right /></el-icon>
              <div class="image-block">
                <el-image
                  v-if="getResultImageUrl(record)"
                  :src="getResultImageUrl(record)"
                  fit="cover"
                  class="history-image result-image-border"
                  :preview-src-list="[getResultImageUrl(record)]"
                >
                  <template #error><div class="image-error"><el-icon><Picture /></el-icon></div></template>
                </el-image>
                <div v-else class="image-error"><el-icon><Picture /></el-icon></div>
                <div class="image-label">结果图</div>
              </div>
            </div>

            <div class="history-content">
              <div class="history-prompt" v-if="record.prompt">
                <span class="prompt-label">提示词：</span>
                <span class="prompt-text">{{ record.prompt }}</span>
              </div>
              <div class="history-meta">
                <span class="meta-time">{{ formatTime(record.created_at) }}</span>
                <span v-if="record.api_duration" class="meta-duration">耗时 {{ record.api_duration }}s</span>
                <el-tag :type="record.api_status === 200 ? 'success' : 'danger'" size="small">
                  {{ record.api_status === 200 ? "成功" : "失败" }}
                </el-tag>
              </div>
            </div>

            <div class="history-actions">
              <el-button
                v-if="getResultImageUrl(record)"
                type="primary"
                :icon="Download"
                size="small"
                @click="downloadImage(getResultImageUrl(record))"
              >
                下载
              </el-button>
              <el-button type="danger" :icon="Delete" size="small" text @click="handleDeleteRecord(record.id)">
                删除
              </el-button>
            </div>
          </div>
        </div>
      </el-card>

      <el-card class="upload-card">
        <template #header>
          <div class="card-header">
            <span>新建风格转换</span>
            <el-tag type="info" size="small">支持 JPG / PNG 格式</el-tag>
          </div>
        </template>

        <el-row :gutter="24">
          <el-col :xs="24" :sm="12">
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
          <el-col :xs="24" :sm="12">
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
          <el-input v-model="prompt" type="textarea" :rows="2" placeholder="请输入风格转换提示词" />
        </div>

        <div class="action-section">
          <el-button
            type="primary"
            size="large"
            :loading="converting"
            :disabled="!contentFile || !styleFile"
            @click="handleConvert"
          >
            {{ converting ? "转换中..." : "开始风格转换" }}
          </el-button>
        </div>
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from "vue";
import { useSessionStore } from "../stores/session";
import { styleConvert, getHistory, deleteHistory } from "../api/style";
import { ElMessage } from "element-plus";
import { Plus, Download, Refresh, Picture, Right, Delete } from "@element-plus/icons-vue";

const sessionStore = useSessionStore();

const contentFile = ref(null);
const styleFile = ref(null);
const contentPreview = ref("");
const stylePreview = ref("");
const prompt = ref("请将第一张图片的风格转换为第二张图片的艺术风格，保持人物和构图等内容主体不变。");
const converting = ref(false);

const historyRecords = ref([]);
const historyLoading = ref(false);

function handleFileChange(uploadFile, type) {
  const raw = uploadFile.raw;
  if (!raw) return;
  const reader = new FileReader();
  reader.onload = (e) => {
    if (type === "content") {
      contentFile.value = raw;
      contentPreview.value = e.target.result;
    } else {
      styleFile.value = raw;
      stylePreview.value = e.target.result;
    }
  };
  reader.readAsDataURL(raw);
}

function getImageUrl(path) {
  if (!path) return "";
  const parts = path.split(/[/\\]/);
  const uploadsIndex = parts.findIndex((p) => p === "uploads");
  if (uploadsIndex !== -1 && uploadsIndex < parts.length - 1) {
    return "/" + parts.slice(uploadsIndex).join("/");
  }
  return "/uploads/" + parts[parts.length - 1];
}

function getResultImageUrl(record) {
  if (record.result_image_path) {
    return getImageUrl(record.result_image_path);
  }
  return record.result_image_url || "";
}

function formatTime(dateStr) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  return d.toLocaleString("zh-CN", { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}

async function fetchHistory() {
  if (!sessionStore.currentSessionId) return;
  historyLoading.value = true;
  try {
    const res = await getHistory(sessionStore.currentSessionId);
    historyRecords.value = res.data.records;
  } catch (e) {
    // handled by interceptor
  } finally {
    historyLoading.value = false;
  }
}

async function handleConvert() {
  if (!contentFile.value || !styleFile.value) {
    ElMessage.warning("请上传内容图片和风格图片");
    return;
  }

  converting.value = true;

  try {
    const formData = new FormData();
    formData.append("session_id", sessionStore.currentSessionId);
    formData.append("content_image", contentFile.value);
    formData.append("style_image", styleFile.value);
    formData.append("prompt", prompt.value);

    const res = await styleConvert(formData);
    ElMessage.success("风格转换完成");
    await fetchHistory();
  } catch (e) {
    // handled by interceptor
  } finally {
    converting.value = false;
  }
}

async function handleDeleteRecord(recordId) {
  try {
    await deleteHistory(recordId);
    historyRecords.value = historyRecords.value.filter((r) => r.id !== recordId);
    ElMessage.success("删除成功");
  } catch (e) {
    // handled by interceptor
  }
}

function downloadImage(url) {
  if (!url) return;
  const link = document.createElement("a");
  link.href = url;
  link.target = "_blank";
  link.download = "styled_image.png";
  link.click();
}

watch(
  () => sessionStore.currentSessionId,
  () => {
    fetchHistory();
  }
);

onMounted(() => {
  fetchHistory();
});
</script>

<style scoped>
.convert-page {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.no-session {
  display: flex;
  justify-content: center;
  padding: 80px 0;
}

.history-card,
.upload-card {
  border-radius: 12px;
}

.history-header,
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.history-loading,
.history-empty {
  padding: 40px 0;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.history-item {
  display: flex;
  gap: 20px;
  padding: 16px;
  border-radius: 12px;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  transition: all 0.2s;
}

.history-item:hover {
  background: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.history-images {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.image-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.history-image {
  width: 80px;
  height: 80px;
  border-radius: 8px;
  overflow: hidden;
}

.result-image-border {
  border: 2px solid #667eea;
}

.image-error {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  background: #e4e7ed;
  color: #c0c4cc;
  border-radius: 8px;
  font-size: 24px;
}

.image-label {
  font-size: 11px;
  color: #909399;
}

.arrow-icon {
  color: #c0c4cc;
  font-size: 16px;
}

.history-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}

.history-prompt {
  font-size: 13px;
  line-height: 1.5;
}

.prompt-label {
  color: #606266;
  font-weight: 500;
}

.prompt-text {
  color: #303133;
}

.history-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.meta-time {
  font-size: 12px;
  color: #909399;
}

.meta-duration {
  font-size: 12px;
  color: #67c23a;
}

.history-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex-shrink: 0;
}

.upload-area {
  margin-bottom: 16px;
}

.upload-label,
.prompt-label {
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
  height: 180px;
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

@media (max-width: 768px) {
  .history-item {
    flex-direction: column;
  }

  .history-images {
    justify-content: center;
  }

  .history-actions {
    flex-direction: row;
    justify-content: flex-end;
  }
}
</style>
