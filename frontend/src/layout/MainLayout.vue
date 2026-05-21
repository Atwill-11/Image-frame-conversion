<template>
  <el-container class="main-layout">
    <el-aside :width="isCollapsed ? '64px' : '260px'" class="sidebar">
      <div class="sidebar-header">
        <h2 v-if="!isCollapsed">🎨 风格转换</h2>
        <span v-else>🎨</span>
      </div>

      <div class="session-section" v-if="!isCollapsed">
        <div class="session-header">
          <span class="session-title">会话列表</span>
          <el-button
            type="primary"
            :icon="Plus"
            circle
            size="small"
            @click="handleAddSession"
          />
        </div>
        <div class="session-list">
          <div
            v-for="session in sessionStore.sessions"
            :key="session.id"
            class="session-item"
            :class="{ active: session.id === sessionStore.currentSessionId }"
            @click="handleSessionClick(session.id)"
          >
            <el-icon><ChatDotRound /></el-icon>
            <span class="session-name">{{ session.name }}</span>
            <el-dropdown
              trigger="click"
              @command="(cmd) => handleSessionCommand(cmd, session)"
            >
              <el-icon class="session-more" @click.stop><MoreFilled /></el-icon>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="rename">重命名</el-dropdown-item>
                  <el-dropdown-item command="delete" style="color: #f56c6c"
                    >删除</el-dropdown-item
                  >
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          <div v-if="sessionStore.sessions.length === 0" class="session-empty">
            暂无会话，点击上方 + 创建
          </div>
        </div>
      </div>

      <div class="sidebar-footer" v-if="!isCollapsed">
        <div class="user-info">
          <el-icon><UserFilled /></el-icon>
          <span>{{ authStore.user?.username }}</span>
        </div>
        <el-button text @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
          退出
        </el-button>
      </div>
    </el-aside>

    <el-container>
      <el-header class="top-bar">
        <el-button :icon="Fold" text @click="isCollapsed = !isCollapsed" />
        <span class="page-title">{{ pageTitle }}</span>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>

    <el-dialog v-model="renameDialogVisible" title="重命名会话" width="400px">
      <el-input
        v-model="renameValue"
        placeholder="请输入新名称"
        @keyup.enter="confirmRename"
      />
      <template #footer>
        <el-button @click="renameDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmRename">确定</el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { useSessionStore } from "../stores/session";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  Plus,
  ChatDotRound,
  MoreFilled,
  UserFilled,
  SwitchButton,
  Fold,
} from "@element-plus/icons-vue";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const sessionStore = useSessionStore();

const isCollapsed = ref(false);
const renameDialogVisible = ref(false);
const renameValue = ref("");
const renameSessionId = ref(null);

const pageTitle = computed(() => {
  if (route.name === "History") return "历史记录";
  return "风格转换";
});

onMounted(async () => {
  await sessionStore.fetchSessions();
});

async function handleAddSession() {
  try {
    await sessionStore.addSession();
    ElMessage.success("会话创建成功");
  } catch (e) {
    // handled by interceptor
  }
}

function handleSessionClick(sessionId) {
  sessionStore.setCurrentSession(sessionId);
}

function handleSessionCommand(cmd, session) {
  if (cmd === "rename") {
    renameSessionId.value = session.id;
    renameValue.value = session.name;
    renameDialogVisible.value = true;
  } else if (cmd === "delete") {
    ElMessageBox.confirm("确定删除该会话及其所有历史记录吗？", "删除确认", {
      confirmButtonText: "删除",
      cancelButtonText: "取消",
      type: "warning",
    })
      .then(async () => {
        await sessionStore.removeSession(session.id);
        ElMessage.success("删除成功");
      })
      .catch(() => {});
  }
}

async function confirmRename() {
  if (!renameValue.value.trim()) {
    ElMessage.warning("会话名称不能为空");
    return;
  }
  await sessionStore.renameSession(
    renameSessionId.value,
    renameValue.value.trim(),
  );
  renameDialogVisible.value = false;
  ElMessage.success("重命名成功");
}

async function handleLogout() {
  await authStore.logout();
  ElMessage.success("已退出登录");
  router.push("/login");
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
}

.sidebar {
  background: linear-gradient(180deg, #2980b9 0%, #6dd5fa 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
  transition: width 0.3s;
  overflow: hidden;
}

.sidebar-header {
  padding: 20px 16px;
  text-align: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.15);
}

.sidebar-header h2 {
  margin: 0;
  font-size: 20px;
  color: #fff;
  white-space: nowrap;
}

.session-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.session-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
}

.session-title {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 2px;
  color: rgba(255, 255, 255, 0.9);
}

.session-item:hover {
  background: rgba(255, 255, 255, 0.15);
}

.session-item.active {
  background: rgba(255, 255, 255, 0.25);
  color: #fff;
}

.session-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
}

.session-more {
  opacity: 0;
  transition: opacity 0.2s;
  color: rgba(255, 255, 255, 0.7);
}

.session-item:hover .session-more {
  opacity: 1;
}

.session-empty {
  text-align: center;
  color: rgba(255, 255, 255, 0.6);
  font-size: 13px;
  padding: 20px;
}

.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.15);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
}

.sidebar-footer .el-button {
  color: rgba(255, 255, 255, 0.8);
}

.top-bar {
  display: flex;
  align-items: center;
  border-bottom: 1px solid #ebeef5;
  background: #fff;
  padding: 0 16px;
}

.page-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  margin-left: 8px;
}

.main-content {
  background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%);
  overflow-y: auto;
}
</style>
