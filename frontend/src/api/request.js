import axios from "axios";
import { ElMessage } from "element-plus";
import router from "../router";

const request = axios.create({
  baseURL: "",
  timeout: 120000,
});

request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

request.interceptors.response.use(
  (response) => {
    const res = response.data;
    if (res.code !== 0) {
      ElMessage.error(res.message || "请求失败");
      return Promise.reject(new Error(res.message));
    }
    return res;
  },
  (error) => {
    if (error.response) {
      const status = error.response.status;
      if (status === 401) {
        const detail = error.response.data?.detail;
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        router.push("/login");
        ElMessage.error(detail || "登录已过期，请重新登录");
      } else {
        ElMessage.error(error.response.data?.detail || "请求失败");
      }
    } else {
      ElMessage.error("网络错误，请检查网络连接");
    }
    return Promise.reject(error);
  },
);

export default request;
