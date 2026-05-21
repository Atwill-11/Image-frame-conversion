<template>
  <div class="login-container">
    <div class="showcase-section">
      <div class="showcase-content">
        <div class="brand-header">
          <h1>AI图片风格转换</h1>
        </div>

        <div class="showcase-main">
          <div class="style-buttons">
            <button
              v-for="(item, index) in examples"
              :key="index"
              class="style-btn"
              :class="{ active: currentExample === index }"
              @click="switchExample(index)"
            >
              {{ item.name }}
            </button>
            <div class="style-features">
              <p>8种预设艺术风格</p>
              <p>支持自定义风格</p>
            </div>
          </div>

          <div class="images-display">
            <div class="images-wrapper">
              <div class="image-float origin-float">
                <img
                  :src="examples[currentExample].origin"
                  alt="原图"
                  class="display-img"
                  :key="'origin-' + currentExample"
                />
              </div>
              <div class="image-float result-float">
                <img
                  :src="examples[currentExample].result"
                  alt="风格修改后图片"
                  class="display-img"
                  :key="'result-' + currentExample"
                />
              </div>
            </div>
            <div class="glass-base"></div>
          </div>
        </div>
      </div>
    </div>

    <div class="form-overlay">
      <div class="login-card">
        <div class="login-header">
          <h2>欢迎登录</h2>
          <p>继续你的创作之旅</p>
        </div>

        <el-tabs v-model="activeTab" class="login-tabs">
          <el-tab-pane label="登录" name="login">
            <el-form
              ref="loginFormRef"
              :model="loginForm"
              :rules="loginRules"
              @submit.prevent="handleLogin"
            >
              <el-form-item prop="username">
                <el-input
                  v-model="loginForm.username"
                  placeholder="用户名"
                  prefix-icon="User"
                  size="large"
                />
              </el-form-item>
              <el-form-item prop="password">
                <el-input
                  v-model="loginForm.password"
                  type="password"
                  placeholder="密码"
                  prefix-icon="Lock"
                  size="large"
                  show-password
                />
              </el-form-item>
              <el-form-item>
                <el-button
                  type="primary"
                  size="large"
                  :loading="loading"
                  style="width: 100%"
                  native-type="submit"
                >
                  开始转换图片风格
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="注册" name="register">
            <el-form
              ref="registerFormRef"
              :model="registerForm"
              :rules="registerRules"
              @submit.prevent="handleRegister"
            >
              <el-form-item prop="username">
                <el-input
                  v-model="registerForm.username"
                  placeholder="用户名（至少3个字符）"
                  prefix-icon="User"
                  size="large"
                />
              </el-form-item>
              <el-form-item prop="password">
                <el-input
                  v-model="registerForm.password"
                  type="password"
                  placeholder="密码（至少6个字符）"
                  prefix-icon="Lock"
                  size="large"
                  show-password
                />
              </el-form-item>
              <el-form-item prop="confirmPassword">
                <el-input
                  v-model="registerForm.confirmPassword"
                  type="password"
                  placeholder="确认密码"
                  prefix-icon="Lock"
                  size="large"
                  show-password
                />
              </el-form-item>
              <el-form-item>
                <el-button
                  type="primary"
                  size="large"
                  :loading="loading"
                  style="width: 100%"
                  native-type="submit"
                >
                  开始转换图片风格
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>
        </el-tabs>

        <div class="login-footer">
          <p>
            登录即表示同意 <a href="#">用户协议</a> 与
            <a href="#">隐私政策</a>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { ElMessage } from "element-plus";

const router = useRouter();
const authStore = useAuthStore();

const activeTab = ref("login");
const loading = ref(false);
const loginFormRef = ref(null);
const registerFormRef = ref(null);
const currentExample = ref(0);

const examples = [
  {
    name: "素描风格",
    origin: "/example/example_origin_2.jpg",
    result: "/example/example_result_2.png",
  },
  {
    name: "像素风格",
    origin: "/example/example_origin_3.jpg",
    result: "/example/example_result_3.png",
  },
  {
    name: "印象派风格",
    origin: "/example/example_origin_1.jpg",
    result: "/example/example_result_1.png",
  },
];

function switchExample(index) {
  currentExample.value = index;
}

const loginForm = reactive({ username: "", password: "" });
const registerForm = reactive({
  username: "",
  password: "",
  confirmPassword: "",
});

const loginRules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
};

const registerRules = {
  username: [
    { required: true, message: "请输入用户名", trigger: "blur" },
    { min: 3, max: 50, message: "用户名长度3-50个字符", trigger: "blur" },
  ],
  password: [
    { required: true, message: "请输入密码", trigger: "blur" },
    { min: 6, message: "密码至少6个字符", trigger: "blur" },
  ],
  confirmPassword: [
    { required: true, message: "请确认密码", trigger: "blur" },
    {
      validator: (rule, value, callback) => {
        if (value !== registerForm.password) {
          callback(new Error("两次密码不一致"));
        } else {
          callback();
        }
      },
      trigger: "blur",
    },
  ],
};

async function handleLogin() {
  const valid = await loginFormRef.value?.validate().catch(() => false);
  if (!valid) return;

  loading.value = true;
  try {
    await authStore.login(loginForm.username, loginForm.password);
    ElMessage.success("登录成功");
    router.push("/");
  } catch (e) {
  } finally {
    loading.value = false;
  }
}

async function handleRegister() {
  const valid = await registerFormRef.value?.validate().catch(() => false);
  if (!valid) return;

  loading.value = true;
  try {
    await authStore.register(registerForm.username, registerForm.password);
    ElMessage.success("注册成功，请登录");
    activeTab.value = "login";
    loginForm.username = registerForm.username;
    loginForm.password = "";
  } catch (e) {
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  position: relative;
  background: linear-gradient(135deg, #2980b9 0%, #6dd5fa 100%);
}

.showcase-section {
  flex: 7;
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  padding: 40px 40px 40px 60px;
}

.showcase-content {
  max-width: 800px;
  width: 100%;
}

.brand-header {
  margin-bottom: 50px;
  margin-left: -10px;
}

.brand-header h1 {
  font-size: 56px;
  color: #fff;
  margin: 0;
  font-weight: 700;
  text-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);
  letter-spacing: 2px;
}

.showcase-main {
  display: flex;
  gap: 40px;
  align-items: flex-start;
  margin-top: 160px;
}

.style-buttons {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 140px;
  margin-left: 10px;
}

.style-btn {
  padding: 12px 24px;
  border: 2px solid rgba(255, 255, 255, 0.5);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s;
  backdrop-filter: blur(10px);
}

.style-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.8);
}

.style-btn.active {
  background: rgba(255, 255, 255, 0.9);
  color: #2980b9;
  border-color: #fff;
  font-weight: 600;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.style-features {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.3);
}

.style-features p {
  color: rgba(255, 255, 255, 0.9);
  font-size: 18px;
  margin: 10px 0;
  line-height: 1.6;
  font-weight: 500;
}

.images-display {
  position: relative;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-bottom: 30px;
}

.images-wrapper {
  position: relative;
  width: 420px;
  height: 420px;
}

.image-float {
  position: absolute;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.25);
  transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.origin-float {
  width: 280px;
  height: 240px;
  top: 20px;
  left: 0;
  transform: rotate(-8deg);
  z-index: 2;
}

.result-float {
  width: 280px;
  height: 240px;
  top: 140px;
  right: 0;
  transform: rotate(8deg);
  z-index: 3;
}

.display-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  animation: slideFadeIn 0.6s ease-out;
}

@keyframes slideFadeIn {
  0% {
    opacity: 0;
    transform: translateY(-20px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

.glass-base {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  width: 500px;
  height: 450px;
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(40px) saturate(1.2);
  -webkit-backdrop-filter: blur(40px) saturate(1.2);
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.35);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  z-index: 1;
}

.form-overlay {
  flex: 3;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  position: relative;
}

.form-overlay::before {
  content: "";
  position: absolute;
  top: 0;
  left: -300px;
  width: 300px;
  height: 100%;
  background: linear-gradient(
    to right,
    rgba(255, 255, 255, 0) 0%,
    rgba(255, 255, 255, 0.2) 30%,
    rgba(255, 255, 255, 0.6) 65%,
    rgba(255, 255, 255, 1) 100%
  );
  pointer-events: none;
}

.login-card {
  width: 100%;
  height: 100%;
  max-width: none;
  background: #fff;
  border-radius: 0;
  padding: 60px 48px;
  box-shadow: none;
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  z-index: 1;
}

.login-header {
  text-align: center;
  margin-bottom: 28px;
}

.login-header h2 {
  font-size: 26px;
  color: #303133;
  margin: 0 0 8px;
  font-weight: 600;
}

.login-header p {
  color: #909399;
  font-size: 14px;
  margin: 0;
}

.login-tabs :deep(.el-tabs__nav) {
  width: 100%;
}

.login-tabs :deep(.el-tabs__item) {
  width: 50%;
  text-align: center;
  font-size: 15px;
}

.login-tabs :deep(.el-tabs__active-bar) {
  background: linear-gradient(90deg, #2980b9, #6dd5fa);
}

.login-tabs :deep(.el-tabs__item.is-active) {
  color: #2980b9;
}

.login-footer {
  text-align: center;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

.login-footer p {
  font-size: 12px;
  color: #909399;
  margin: 0;
}

.login-footer a {
  color: #2980b9;
  text-decoration: none;
}

.login-footer a:hover {
  text-decoration: underline;
}

@media (max-width: 1024px) {
  .login-container {
    flex-direction: column;
  }

  .showcase-section {
    flex: none;
    padding: 30px 20px;
  }

  .brand-header h1 {
    font-size: 36px;
  }

  .showcase-main {
    flex-direction: column;
    align-items: center;
    margin-top: 30px;
  }

  .style-buttons {
    flex-direction: row;
    flex-wrap: wrap;
    justify-content: center;
    margin-left: 0;
  }

  .style-features {
    display: none;
  }

  .images-wrapper {
    width: 320px;
    height: 300px;
  }

  .origin-float,
  .result-float {
    width: 200px;
    height: 170px;
  }

  .glass-base {
    width: 340px;
    height: 90px;
  }

  .form-overlay {
    flex: none;
    padding: 30px 20px;
  }

  .form-overlay::before {
    display: none;
  }
}
</style>
