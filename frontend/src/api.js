import axios from "axios";

// In dev, Vite proxies /api -> Django (see vite.config.js).
// For production set VITE_API_URL=https://your-backend.com
const api = axios.create({ baseURL: (import.meta.env.VITE_API_URL || "") + "/api" });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let refreshing = null;
api.interceptors.response.use(
  (r) => r,
  async (error) => {
    const original = error.config;
    const refresh = localStorage.getItem("refresh");
    if (error.response?.status === 401 && refresh && !original._retry && !original.url.includes("/auth/")) {
      original._retry = true;
      try {
        refreshing = refreshing || axios.post(api.defaults.baseURL + "/auth/refresh/", { refresh });
        const { data } = await refreshing;
        localStorage.setItem("access", data.access);
        original.headers.Authorization = `Bearer ${data.access}`;
        return api(original);
      } catch {
        localStorage.clear();
        window.location.href = "/login";
      } finally {
        refreshing = null;
      }
    }
    return Promise.reject(error);
  }
);

export function errMsg(e, fallback = "Something went wrong") {
  const d = e?.response?.data;
  if (!d) return e?.message || fallback;
  if (typeof d === "string") return fallback;
  if (d.detail) return d.detail;
  const first = Object.entries(d)[0];
  if (first) {
    const [k, v] = first;
    const msg = String(Array.isArray(v) ? v[0] : v);
    if (k === "non_field_errors" || !/^(This field|This password|Ensure|Enter a valid|A user with|user with)/i.test(msg)) return msg;
    const label = k.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase());
    return `${label}: ${msg}`;
  }
  return fallback;
}

export const fmtSalary = (min, max) => {
  if (!min && !max) return null;
  const f = (n) => (n >= 100000 ? `${(n / 100000).toFixed(n % 100000 ? 1 : 0)}L` : `${Math.round(n / 1000)}K`);
  if (min && max && min !== max) return `₹${f(min)} - ${f(max)}`;
  return `₹${f(min || max)}`;
};

export const timeAgo = (iso) => {
  if (!iso) return "";
  const s = (Date.now() - new Date(iso).getTime()) / 1000;
  if (s < 3600) return `${Math.max(1, Math.round(s / 60))}m ago`;
  if (s < 86400) return `${Math.round(s / 3600)}h ago`;
  return `${Math.round(s / 86400)}d ago`;
};

export default api;
