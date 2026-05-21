<template>
  <div class="convert-page">
    <div v-if="!sessionStore.currentSessionId" class="no-session">
      <el-empty description="请先创建或选择一个会话">
        <el-button type="primary" @click="sessionStore.addSession()"
          >创建会话</el-button
        >
      </el-empty>
    </div>

    <template v-else>
      <!-- 历史记录区域 -->
      <div class="history-area">
        <div
          v-if="historyLoading && historyRecords.length === 0"
          class="history-loading"
        >
          <el-skeleton :rows="4" animated />
        </div>

        <div v-else-if="historyRecords.length === 0" class="history-empty">
          <el-empty
            description="暂无历史记录，开始您的第一次风格转换吧"
            :image-size="80"
          />
        </div>

        <div v-else class="history-list">
          <div
            v-for="record in historyRecords"
            :key="record.id"
            class="history-item"
          >
            <div class="history-prompt" v-if="record.prompt">
              <span class="prompt-label">提示词：</span>
              <span class="prompt-text">{{ record.prompt }}</span>
            </div>

            <div class="history-images">
              <div class="image-block">
                <el-image
                  :src="getImageUrl(record.original_image_path)"
                  fit="cover"
                  class="history-image"
                  :preview-src-list="[getImageUrl(record.original_image_path)]"
                >
                  <template #error
                    ><div class="image-error">
                      <el-icon><Picture /></el-icon></div
                  ></template>
                </el-image>
                <div class="image-label">内容图</div>
              </div>
              <div class="image-block">
                <el-image
                  :src="getImageUrl(record.style_image_path)"
                  fit="cover"
                  class="history-image"
                  :preview-src-list="[getImageUrl(record.style_image_path)]"
                >
                  <template #error
                    ><div class="image-error">
                      <el-icon><Picture /></el-icon></div
                  ></template>
                </el-image>
                <div class="image-label">风格图</div>
              </div>
              <div class="image-block">
                <el-image
                  v-if="getResultImageUrl(record)"
                  :src="getResultImageUrl(record)"
                  fit="cover"
                  class="history-image result-image"
                  :preview-src-list="[getResultImageUrl(record)]"
                >
                  <template #error
                    ><div class="image-error">
                      <el-icon><Picture /></el-icon></div
                  ></template>
                </el-image>
                <div v-else class="image-error">
                  <el-icon><Picture /></el-icon>
                </div>
                <div class="image-label">结果图</div>
              </div>

              <div class="history-actions">
                <el-button
                  v-if="getResultImageUrl(record)"
                  type="primary"
                  :icon="Download"
                  size="small"
                  plain
                  round
                  class="action-btn download-btn"
                  @click="downloadImage(getResultImageUrl(record))"
                  >下载</el-button
                >
                <el-button
                  type="danger"
                  :icon="Delete"
                  size="small"
                  plain
                  round
                  class="action-btn delete-btn"
                  @click="handleDeleteRecord(record.id)"
                  >删除</el-button
                >
              </div>
            </div>

            <div class="history-meta">
              <span class="meta-time">{{ formatTime(record.created_at) }}</span>
              <span v-if="record.api_duration" class="meta-duration"
                >耗时 {{ record.api_duration }}s</span
              >
            </div>
          </div>
        </div>
      </div>

      <!-- 底部输入区域 -->
      <div class="input-area">
        <div class="input-box">
          <div class="upload-icon" @click="triggerContentUpload">
            <el-icon :size="24"><Plus /></el-icon>
          </div>
          <input
            ref="contentInputRef"
            type="file"
            accept=".jpg,.jpeg,.png,.webp,.bmp"
            style="display: none"
            @change="handleContentFileSelect"
          />

          <div class="input-content">
            <div v-if="contentPreview" class="content-preview-wrapper">
              <img :src="contentPreview" class="content-preview-image" />
              <div
                class="content-preview-overlay"
                @click="
                  contentFile = null;
                  contentPreview = '';
                "
              >
                <el-icon><Close /></el-icon>
              </div>
            </div>
            <textarea
              v-model="prompt"
              class="prompt-input"
              :placeholder="
                contentPreview
                  ? '输入额外需求描述...'
                  : '输入想法、描述或上传参考，开始风格转换...'
              "
              rows="3"
              @keydown.enter.prevent="handleConvert"
            />
            <div class="input-toolbar">
              <div class="toolbar-left">
                <el-button
                  type="primary"
                  size="small"
                  plain
                  round
                  @click="styleDialogVisible = true"
                >
                  <el-icon><Brush /></el-icon>
                  风格选择
                </el-button>
                <span v-if="selectedStyleName" class="selected-style">
                  {{ selectedStyleName }}
                </span>
                <span v-if="contentFile" class="file-tag">
                  <el-icon><Document /></el-icon>
                  {{ contentFile.name }}
                </span>
              </div>
              <el-button
                type="primary"
                round
                :loading="converting"
                :disabled="!contentFile || !hasStyleImage"
                @click="handleConvert"
                class="send-btn"
              >
                <el-icon v-if="!converting"><Top /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 风格选择弹窗 -->
      <el-dialog
        v-model="styleDialogVisible"
        title="选择风格"
        width="600px"
        class="style-dialog"
      >
        <el-tabs v-model="styleMode" class="style-tabs">
          <el-tab-pane label="预设风格" name="preset">
            <div class="style-grid">
              <div
                v-for="preset in presetStyles"
                :key="preset.id"
                class="style-item"
                :class="{ active: selectedPreset?.id === preset.id }"
                @click="selectPreset(preset)"
              >
                <div class="style-image-wrapper">
                  <el-image
                    v-if="preset.image_url"
                    :src="preset.image_url"
                    fit="cover"
                    class="style-preview-image"
                  >
                    <template #error
                      ><div class="style-image-error">
                        <el-icon><Picture /></el-icon></div
                    ></template>
                  </el-image>
                  <div v-else class="style-image-error">
                    <el-icon><Picture /></el-icon>
                  </div>
                </div>
                <div class="style-name">{{ preset.name }}</div>
              </div>
              <div v-if="presetStyles.length === 0" class="no-styles">
                <el-empty description="暂无预设风格" :image-size="40" />
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="自定义风格" name="custom">
            <div class="custom-style-section">
              <div class="style-grid">
                <div
                  v-for="custom in customStyles"
                  :key="custom.id"
                  class="style-item"
                  :class="{ active: selectedCustom?.id === custom.id }"
                  @click="selectCustom(custom)"
                >
                  <div class="style-image-wrapper">
                    <el-image
                      :src="custom.image_url"
                      fit="cover"
                      class="style-preview-image"
                    >
                      <template #error
                        ><div class="style-image-error">
                          <el-icon><Picture /></el-icon></div
                      ></template>
                    </el-image>
                  </div>
                  <div class="style-name">{{ custom.name }}</div>
                  <el-icon
                    class="delete-custom"
                    @click.stop="handleDeleteCustomStyle(custom.id)"
                    ><Close
                  /></el-icon>
                </div>
              </div>

              <div class="add-custom-style">
                <el-upload
                  class="custom-upload"
                  :auto-upload="false"
                  :show-file-list="false"
                  accept=".jpg,.jpeg,.png,.webp,.bmp"
                  :on-change="handleCustomStyleUpload"
                >
                  <el-button type="primary" :icon="Plus" size="small"
                    >添加自定义风格</el-button
                  >
                </el-upload>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="上传图片" name="upload">
            <div class="upload-style-area">
              <el-upload
                class="style-uploader"
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
          </el-tab-pane>
        </el-tabs>

        <template #footer>
          <el-button @click="styleDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmStyleSelect">确定</el-button>
        </template>
      </el-dialog>

      <!-- 添加自定义风格弹窗 -->
      <el-dialog
        v-model="customStyleDialogVisible"
        title="添加自定义风格"
        width="400px"
      >
        <el-form :model="customStyleForm">
          <el-form-item label="风格名称">
            <el-input
              v-model="customStyleForm.name"
              placeholder="请输入风格名称"
            />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="customStyleDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            @click="submitCustomStyle"
            :loading="customStyleLoading"
            >确定</el-button
          >
        </template>
      </el-dialog>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from "vue";
import { useSessionStore } from "../stores/session";
import { styleConvert, getHistory, deleteHistory } from "../api/style";
import {
  getPresetStyles,
  getCustomStyles,
  createCustomStyle,
  deleteCustomStyle,
} from "../api/styles";
import { ElMessage } from "element-plus";
import {
  Plus,
  Download,
  Picture,
  Delete,
  Close,
  Brush,
  Top,
  Document,
} from "@element-plus/icons-vue";

const sessionStore = useSessionStore();

const contentFile = ref(null);
const styleFile = ref(null);
const contentPreview = ref("");
const stylePreview = ref("");
const prompt = ref("");
const converting = ref(false);

const historyRecords = ref([]);
const historyLoading = ref(false);

const styleMode = ref("preset");
const presetStyles = ref([]);
const customStyles = ref([]);
const selectedPreset = ref(null);
const selectedCustom = ref(null);
const styleDialogVisible = ref(false);
const customStyleDialogVisible = ref(false);
const customStyleForm = ref({ name: "", file: null });
const customStyleLoading = ref(false);
const contentInputRef = ref(null);

const hasStyleImage = computed(() => {
  if (styleMode.value === "preset") return !!selectedPreset.value;
  if (styleMode.value === "custom") return !!selectedCustom.value;
  return !!styleFile.value;
});

const selectedStyleName = computed(() => {
  if (styleMode.value === "preset" && selectedPreset.value)
    return selectedPreset.value.name;
  if (styleMode.value === "custom" && selectedCustom.value)
    return selectedCustom.value.name;
  if (styleMode.value === "upload" && styleFile.value) return "自定义图片";
  return "";
});

function triggerContentUpload() {
  contentInputRef.value?.click();
}

function handleContentFileSelect(e) {
  const file = e.target.files[0];
  if (!file) return;
  handleFileChange({ raw: file }, "content");
  e.target.value = "";
}

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
      selectedPreset.value = null;
      selectedCustom.value = null;
    }
  };
  reader.readAsDataURL(raw);
}

function selectPreset(preset) {
  selectedPreset.value = preset;
  selectedCustom.value = null;
  styleFile.value = null;
  stylePreview.value = "";
}

function selectCustom(custom) {
  selectedCustom.value = custom;
  selectedPreset.value = null;
  styleFile.value = null;
  stylePreview.value = "";
}

function confirmStyleSelect() {
  if (!hasStyleImage.value) {
    ElMessage.warning("请选择或上传风格图片");
    return;
  }
  styleDialogVisible.value = false;
}

function handleCustomStyleUpload(file) {
  customStyleForm.value.file = file.raw;
  customStyleForm.value.name = "";
  customStyleDialogVisible.value = true;
}

async function submitCustomStyle() {
  if (!customStyleForm.value.name.trim()) {
    ElMessage.warning("请输入风格名称");
    return;
  }
  if (!customStyleForm.value.file) {
    ElMessage.warning("请选择图片");
    return;
  }

  customStyleLoading.value = true;
  try {
    const formData = new FormData();
    formData.append("name", customStyleForm.value.name.trim());
    formData.append("image", customStyleForm.value.file);
    await createCustomStyle(formData);
    ElMessage.success("添加成功");
    customStyleDialogVisible.value = false;
    await fetchCustomStyles();
  } catch (e) {
    // handled by interceptor
  } finally {
    customStyleLoading.value = false;
  }
}

async function handleDeleteCustomStyle(styleId) {
  try {
    await deleteCustomStyle(styleId);
    customStyles.value = customStyles.value.filter((s) => s.id !== styleId);
    if (selectedCustom.value?.id === styleId) {
      selectedCustom.value = null;
    }
    ElMessage.success("删除成功");
  } catch (e) {
    // handled by interceptor
  }
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
  return d.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
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

async function fetchPresetStyles() {
  try {
    const res = await getPresetStyles();
    presetStyles.value = res.data;
  } catch (e) {
    // handled by interceptor
  }
}

async function fetchCustomStyles() {
  try {
    const res = await getCustomStyles();
    customStyles.value = res.data.styles;
  } catch (e) {
    // handled by interceptor
  }
}

async function handleConvert() {
  if (!contentFile.value) {
    ElMessage.warning("请上传内容图片");
    return;
  }

  if (!hasStyleImage.value) {
    ElMessage.warning("请选择或上传风格图片");
    return;
  }

  converting.value = true;

  try {
    const formData = new FormData();
    formData.append("session_id", sessionStore.currentSessionId);
    formData.append("content_image", contentFile.value);
    formData.append("prompt", prompt.value);

    if (styleMode.value === "preset" && selectedPreset.value) {
      const response = await fetch(selectedPreset.value.image_url);
      const blob = await response.blob();
      const file = new File([blob], selectedPreset.value.filename, {
        type: blob.type,
      });
      formData.append("style_image", file);
    } else if (styleMode.value === "custom" && selectedCustom.value) {
      const response = await fetch(selectedCustom.value.image_url);
      const blob = await response.blob();
      const file = new File([blob], "custom_style.jpg", { type: blob.type });
      formData.append("style_image", file);
    } else if (styleFile.value) {
      formData.append("style_image", styleFile.value);
    }

    await styleConvert(formData);
    ElMessage.success("风格转换完成");
    prompt.value = "";
    contentFile.value = null;
    contentPreview.value = "";
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
    historyRecords.value = historyRecords.value.filter(
      (r) => r.id !== recordId,
    );
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
  },
);

onMounted(() => {
  fetchHistory();
  fetchPresetStyles();
  fetchCustomStyles();
});
</script>

<style scoped>
.convert-page {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.no-session {
  display: flex;
  justify-content: center;
  padding: 80px 0;
}

/* 历史记录区域 */
.history-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px 0;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.history-area::-webkit-scrollbar {
  display: none;
}

.history-loading,
.history-empty {
  padding: 40px 0;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.history-item {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.history-item:last-child {
  border-bottom: none;
}

.history-prompt {
  font-size: 14px;
  line-height: 1.6;
  color: #303133;
}

.prompt-label {
  color: #606266;
  font-weight: 500;
}

.prompt-text {
  color: #303133;
}

.history-images {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.image-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.history-image {
  width: 120px;
  height: 120px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.result-image {
  border: 2px solid #2980b9;
}

.image-error {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 120px;
  height: 120px;
  background: #e4e7ed;
  color: #c0c4cc;
  border-radius: 12px;
  font-size: 24px;
}

.image-label {
  font-size: 12px;
  color: #909399;
}

.history-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-left: auto;
  justify-content: center;
}

.action-btn {
  font-size: 12px;
  padding: 6px 14px;
  height: auto;
}

.action-btn.download-btn {
  background: rgba(41, 128, 185, 0.1);
  border-color: rgba(41, 128, 185, 0.2);
  color: #2980b9;
}

.action-btn.download-btn:hover {
  background: #2980b9;
  border-color: #2980b9;
  color: #fff;
}

.action-btn.delete-btn {
  background: rgba(245, 108, 108, 0.1);
  border-color: rgba(245, 108, 108, 0.2);
  color: #f56c6c;
}

.action-btn.delete-btn:hover {
  background: #f56c6c;
  border-color: #f56c6c;
  color: #fff;
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

/* 底部输入区域 */
.input-area {
  padding: 16px 0;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  border-radius: 16px 16px 0 0;
}

.input-area :deep(.el-dialog) {
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
}

.input-area :deep(.el-dialog__header) {
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  padding: 20px 24px;
}

.input-area :deep(.el-dialog__body) {
  padding: 24px;
}

.input-area :deep(.el-dialog__footer) {
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  padding: 16px 24px;
}

.input-box {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  background: transparent;
  border-radius: 16px;
  padding: 12px 16px;
  box-shadow: none;
  border: none;
}

.upload-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  border-radius: 10px;
  cursor: pointer;
  color: #606266;
  transition: all 0.2s;
  flex-shrink: 0;
}

.upload-icon:hover {
  background: #e6f0ff;
  color: #2980b9;
}

.input-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: #fff;
  border-radius: 16px;
  padding: 12px 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: 1px solid #e4e7ed;
}

.content-preview-wrapper {
  position: relative;
  width: 80px;
  height: 80px;
  border-radius: 10px;
  overflow: hidden;
  flex-shrink: 0;
}

.content-preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.content-preview-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  opacity: 0;
  transition: opacity 0.2s;
  cursor: pointer;
}

.content-preview-wrapper:hover .content-preview-overlay {
  opacity: 1;
}

.prompt-input {
  width: 100%;
  border: none;
  outline: none;
  font-size: 14px;
  line-height: 1.6;
  color: #303133;
  resize: none;
  background: transparent;
  font-family: inherit;
  min-height: 60px;
}

.prompt-input::placeholder {
  color: #909399;
}

.input-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.selected-style {
  font-size: 12px;
  color: #2980b9;
  background: rgba(41, 128, 185, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
}

.file-tag {
  font-size: 12px;
  color: #67c23a;
  background: rgba(103, 194, 58, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.send-btn {
  width: 36px;
  height: 36px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 风格选择弹窗 */
.style-dialog :deep(.el-dialog__body) {
  padding-top: 10px;
}

.style-tabs :deep(.el-tabs__content) {
  padding: 16px 0;
}

.style-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  max-height: 320px;
  overflow-y: auto;
}

.style-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 12px;
  border-radius: 12px;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.style-item:hover {
  background: #f5f7fa;
}

.style-item.active {
  border-color: #2980b9;
  background: rgba(41, 128, 185, 0.08);
}

.style-image-wrapper {
  width: 80px;
  height: 80px;
  border-radius: 10px;
  overflow: hidden;
}

.style-preview-image {
  width: 100%;
  height: 100%;
}

.style-image-error {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  background: #e4e7ed;
  color: #c0c4cc;
  border-radius: 10px;
  font-size: 24px;
}

.style-name {
  font-size: 13px;
  color: #606266;
  text-align: center;
  max-width: 90px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.delete-custom {
  position: absolute;
  top: 4px;
  right: 4px;
  font-size: 14px;
  color: #f56c6c;
  opacity: 0;
  transition: opacity 0.2s;
}

.style-item:hover .delete-custom {
  opacity: 1;
}

.no-styles {
  grid-column: span 4;
  padding: 20px 0;
}

.custom-style-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.add-custom-style {
  text-align: center;
}

.custom-upload :deep(.el-upload) {
  display: inline-block;
}

.upload-style-area {
  padding: 20px 0;
}

.style-uploader :deep(.el-upload) {
  width: 100%;
  border: 2px dashed #dcdfe6;
  border-radius: 12px;
  cursor: pointer;
  transition: border-color 0.3s;
  overflow: hidden;
}

.style-uploader :deep(.el-upload:hover) {
  border-color: #2980b9;
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

@media (max-width: 768px) {
  .history-images {
    flex-wrap: wrap;
  }

  .history-actions {
    flex-direction: row;
    width: 100%;
    margin-left: 0;
    justify-content: flex-end;
  }

  .style-grid {
    grid-template-columns: repeat(3, 1fr);
  }

  .input-box {
    flex-direction: column;
  }
}
</style>
