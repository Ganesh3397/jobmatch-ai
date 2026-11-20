import { createContext, useContext, useEffect, useState } from "react";
import api from "./api";

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem("user")); } catch { return null; }
  });
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!localStorage.getItem("access")) { setReady(true); return; }
    api.get("/auth/me/")
      .then(({ data }) => save(data))
      .catch(() => logout())
      .finally(() => setReady(true));
  }, []);

  const save = (u) => { setUser(u); localStorage.setItem("user", JSON.stringify(u)); };

  const finish = (data) => {
    localStorage.setItem("access", data.access);
    localStorage.setItem("refresh", data.refresh);
    save(data.user);
    return data.user;
  };

  const login = async (username, password) => finish((await api.post("/auth/login/", { username, password })).data);
  const register = async (payload) => finish((await api.post("/auth/register/", payload)).data);
  const logout = () => { localStorage.clear(); setUser(null); };

  return (
    <AuthCtx.Provider value={{ user, ready, login, register, logout, setUser: save }}>
      {children}
    </AuthCtx.Provider>
  );
}

export const useAuth = () => useContext(AuthCtx);

export const homeFor = (role) => ({ seeker: "/dashboard", recruiter: "/recruiter", admin: "/admin" }[role] || "/");
