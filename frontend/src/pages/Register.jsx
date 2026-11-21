import ThemeToggle from "../components/ThemeToggle";
import { useState } from "react";
import toast from "react-hot-toast";
import { Link, useNavigate } from "react-router-dom";
import { errMsg } from "../api";
import { homeFor, useAuth } from "../auth";
import { AuthArt, MobileLogo } from "./Login";

export default function Register() {
  const { register } = useAuth();
  const nav = useNavigate();
  const [f, setF] = useState({ first_name: "", last_name: "", username: "", email: "", password: "", location: "" });
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const u = await register(f);
      toast.success("Account created! 🎉");
      nav(u.role === "seeker" ? "/resume" : homeFor(u.role)); // new users go straight to resume upload
    } catch (err) { toast.error(errMsg(err)); } finally { setBusy(false); }
  };

  return (
    <div className="auth">
      <ThemeToggle />
      <AuthArt />
      <div className="auth-form">
        <form className="auth-box" onSubmit={submit}>
          <MobileLogo />
          <h1>Create your account</h1>
          <p className="muted" style={{ margin: "6px 0 20px" }}>It's free. Upload your resume next and get your ATS score in seconds.</p>
          <div className="grid g-2" style={{ gap: 12 }}>
            <div className="field"><label>First name</label><input className="input" value={f.first_name} onChange={set("first_name")} required /></div>
            <div className="field"><label>Last name</label><input className="input" value={f.last_name} onChange={set("last_name")} /></div>
          </div>
          <div className="field"><label>Username</label><input className="input" value={f.username} onChange={set("username")} required /></div>
          <div className="field"><label>Email</label><input className="input" type="email" value={f.email} onChange={set("email")} required /></div>
          <div className="field"><label>City</label><input className="input" placeholder="e.g. Pune" value={f.location} onChange={set("location")} /></div>
          <div className="field"><label>Password</label><input className="input" type="password" minLength={6} value={f.password} onChange={set("password")} required /></div>
          <button className="btn btn-primary btn-block btn-lg" disabled={busy}>{busy ? "Creating…" : "Create account"}</button>
          <p className="muted" style={{ marginTop: 16, textAlign: "center" }}>Already have an account? <Link to="/login">Login</Link></p>
        </form>
      </div>
    </div>
  );
}
