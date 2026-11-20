import { Sparkles } from "lucide-react";
import { useState } from "react";
import toast from "react-hot-toast";
import { Link, useNavigate } from "react-router-dom";
import { errMsg } from "../api";
import { homeFor, useAuth } from "../auth";

export function AuthArt() {
  return (
    <div className="auth-art">
      <div className="logo" style={{ padding: 0 }}><div className="logo-mark"><Sparkles size={18} /></div>JobMatch AI</div>
      <div>
        <h2>Your resume, analysed by AI. Your next job, found in real time.</h2>
        <p>ATS scoring, skill-gap analysis and live job recommendations from across the web — all in one place.</p>
      </div>
      <p style={{ fontSize: 13 }}>MCA Project • Python • Django • React • PostgreSQL • Redis • ML</p>
    </div>
  );
}

export function MobileLogo() {
  return (
    <div className="mobile-logo">
      <div className="logo-mark"><Sparkles size={18} /></div><b>JobMatch AI</b>
    </div>
  );
}

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [f, setF] = useState({ username: "", password: "" });
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const u = await login(f.username, f.password);
      toast.success(`Welcome back, ${u.first_name || u.username}!`);
      nav(homeFor(u.role));
    } catch (err) {
      toast.error(err?.response?.status === 401 ? "Invalid username or password" : errMsg(err));
    } finally { setBusy(false); }
  };

  const demo = (u, p) => setF({ username: u, password: p });

  return (
    <div className="auth">
      <AuthArt />
      <div className="auth-form">
        <form className="auth-box" onSubmit={submit}>
          <MobileLogo />
          <h1>Welcome back 👋</h1>
          <p className="muted" style={{ margin: "6px 0 24px" }}>Login to continue to your dashboard</p>
          <div className="field"><label>Username or email</label>
            <input className="input" value={f.username} onChange={(e) => setF({ ...f, username: e.target.value })} required autoFocus /></div>
          <div className="field"><label>Password</label>
            <input className="input" type="password" value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} required /></div>
          <button className="btn btn-primary btn-block" disabled={busy}>{busy ? "Logging in…" : "Login"}</button>
          <p className="muted" style={{ marginTop: 16, textAlign: "center" }}>New here? <Link to="/register">Create an account</Link></p>
          <div className="demo-logins">
            <b>Demo logins:</b>
            <button type="button" onClick={() => demo("student", "student123")}>Student</button>•
            <button type="button" onClick={() => demo("recruiter", "recruiter123")}>Recruiter</button>
          </div>
        </form>
      </div>
    </div>
  );
}
