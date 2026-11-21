import { ArrowLeft, CheckCircle2, Eye, EyeOff, KeyRound, Mail, RotateCw, ShieldCheck } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import toast from "react-hot-toast";
import { Link, useNavigate } from "react-router-dom";
import api, { errMsg } from "../api";
import ThemeToggle from "../components/ThemeToggle";
import { AuthArt, MobileLogo } from "./Login";

const STEPS = ["Email", "Code", "New password"];

function Steps({ step }) {
  return (
    <div className="stepper">
      {STEPS.map((s, i) => (
        <div key={s} className={`stepper-item ${i < step ? "done" : ""} ${i === step ? "on" : ""}`}>
          <span>{i < step ? <CheckCircle2 size={14} /> : i + 1}</span>{s}
        </div>
      ))}
    </div>
  );
}

function OtpInput({ value, onChange, disabled }) {
  const refs = useRef([]);
  const digits = value.padEnd(6, " ").slice(0, 6).split("");
  const setAt = (i, d) => {
    const arr = value.padEnd(6, " ").split("");
    arr[i] = d || " ";
    onChange(arr.join("").replace(/\s+$/, ""));
  };
  const onKey = (i, e) => {
    if (e.key === "Backspace" && !digits[i].trim() && i > 0) refs.current[i - 1]?.focus();
    if (e.key === "ArrowLeft" && i > 0) refs.current[i - 1]?.focus();
    if (e.key === "ArrowRight" && i < 5) refs.current[i + 1]?.focus();
  };
  const onInput = (i, e) => {
    const v = e.target.value.replace(/\D/g, "");
    if (v.length > 1) { // pasted the whole code
      onChange(v.slice(0, 6));
      refs.current[Math.min(v.length, 6) - 1]?.focus();
      return;
    }
    setAt(i, v);
    if (v && i < 5) refs.current[i + 1]?.focus();
  };
  return (
    <div className="otp">
      {digits.map((d, i) => (
        <input key={i} ref={(el) => (refs.current[i] = el)} inputMode="numeric" autoComplete={i === 0 ? "one-time-code" : "off"}
          maxLength={6} value={d.trim()} disabled={disabled} autoFocus={i === 0}
          onChange={(e) => onInput(i, e)} onKeyDown={(e) => onKey(i, e)} onFocus={(e) => e.target.select()}
          className={d.trim() ? "filled" : ""} aria-label={`Digit ${i + 1}`} />
      ))}
    </div>
  );
}

function strength(pw) {
  let s = 0;
  if (pw.length >= 8) s++;
  if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) s++;
  if (/\d/.test(pw)) s++;
  if (/[^A-Za-z0-9]/.test(pw)) s++;
  return [["Too short", "var(--red)"], ["Weak", "var(--red)"], ["Okay", "var(--amber)"], ["Good", "var(--brand)"], ["Strong", "var(--green)"]][pw.length < 6 ? 0 : Math.max(1, s)];
}

export default function ForgotPassword() {
  const nav = useNavigate();
  const [step, setStep] = useState(0);
  const [email, setEmail] = useState("");
  const [info, setInfo] = useState(null);
  const [code, setCode] = useState("");
  const [pw, setPw] = useState("");
  const [pw2, setPw2] = useState("");
  const [show, setShow] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [wait, setWait] = useState(0);

  useEffect(() => {
    if (wait <= 0) return undefined;
    const t = setTimeout(() => setWait(wait - 1), 1000);
    return () => clearTimeout(t);
  }, [wait]);

  const sendCode = async (e) => {
    e?.preventDefault();
    setBusy(true); setError("");
    try {
      const { data } = await api.post("/auth/password-reset/", { email });
      setInfo(data); setCode(""); setStep(1); setWait(60);
      toast.success(data.dev_code ? "Development mode: code shown below" : "Code sent! Check your email 📩");
    } catch (err) {
      const d = err?.response?.data;
      if (d?.wait) setWait(d.wait);
      setError(errMsg(err));
    } finally { setBusy(false); }
  };

  const verify = async (e) => {
    e.preventDefault();
    if (code.length !== 6) return setError("Enter all 6 digits of the code.");
    setBusy(true); setError("");
    try {
      await api.post("/auth/password-reset/verify/", { email, code });
      setStep(2);
    } catch (err) { setError(errMsg(err)); } finally { setBusy(false); }
  };

  const save = async (e) => {
    e.preventDefault();
    if (pw !== pw2) return setError("The two passwords do not match.");
    setBusy(true); setError("");
    try {
      await api.post("/auth/password-reset/confirm/", { email, code, new_password: pw });
      setStep(3);
      toast.success("Password changed!");
    } catch (err) {
      const d = err?.response?.data;
      if (d?.code) setStep(1);
      setError(errMsg(err));
    } finally { setBusy(false); }
  };

  const [label, color] = strength(pw);

  return (
    <div className="auth">
      <ThemeToggle />
      <AuthArt />
      <div className="auth-form">
        <div className="auth-box">
          <MobileLogo />
          {step < 3 && (
            <>
              <div className="auth-icon"><KeyRound /></div>
              <h1>Reset your password</h1>
              <p className="muted" style={{ margin: "6px 0 18px" }}>
                {step === 0 && "Enter the email you registered with. We'll send you a 6-digit code."}
                {step === 1 && <>Enter the 6-digit code we sent to <b>{info?.email}</b>.</>}
                {step === 2 && "Code verified ✅ Now choose a new password."}
              </p>
              <Steps step={step} />
            </>
          )}

          {error && <div className="alert alert-error">{error}</div>}

          {step === 0 && (
            <form onSubmit={sendCode}>
              <div className="field"><label>Email</label>
                <div className="input-icon"><Mail />
                  <input className="input" type="email" placeholder="you@gmail.com" value={email}
                    onChange={(e) => setEmail(e.target.value)} required autoFocus /></div></div>
              <button className="btn btn-primary btn-block btn-lg" disabled={busy || wait > 0}>
                {busy ? "Sending code…" : wait > 0 ? `Try again in ${wait}s` : "Send code"}</button>
            </form>
          )}

          {step === 1 && (
            <form onSubmit={verify}>
              {info?.dev_code && (
                <div className="alert alert-info">
                  <b>Development mode</b>: email is not set up on this computer, so your code is <b className="mono">{info.dev_code}</b>.
                  On the live site the code arrives by email.
                </div>
              )}
              <OtpInput value={code} onChange={setCode} disabled={busy} />
              <button className="btn btn-primary btn-block btn-lg" disabled={busy || code.length !== 6}>
                <ShieldCheck />{busy ? "Checking…" : "Verify code"}</button>
              <div className="row between mt small">
                <span className="muted">Valid for {info?.minutes || 10} minutes. Check spam too.</span>
                <button type="button" className="link-btn" disabled={wait > 0 || busy} onClick={sendCode}>
                  <RotateCw size={13} />{wait > 0 ? `Resend in ${wait}s` : "Resend code"}</button>
              </div>
              <button type="button" className="link-btn mt" onClick={() => { setStep(0); setError(""); }}>Use a different email</button>
            </form>
          )}

          {step === 2 && (
            <form onSubmit={save}>
              <div className="field"><label>New password</label>
                <div className="input-icon right">
                  <input className="input" type={show ? "text" : "password"} minLength={6} value={pw}
                    onChange={(e) => setPw(e.target.value)} required autoFocus />
                  <button type="button" onClick={() => setShow(!show)} aria-label="Show password">{show ? <EyeOff /> : <Eye />}</button>
                </div>
                {pw && <div className="pw-meter"><div style={{ width: `${Math.max(1, ["Too short", "Weak", "Okay", "Good", "Strong"].indexOf(label)) * 25}%`, background: color }} /><span style={{ color }}>{label}</span></div>}
              </div>
              <div className="field"><label>Confirm new password</label>
                <input className="input" type={show ? "text" : "password"} minLength={6} value={pw2} onChange={(e) => setPw2(e.target.value)} required />
                {pw2 && pw !== pw2 && <span className="error">Passwords do not match</span>}
              </div>
              <button className="btn btn-primary btn-block btn-lg" disabled={busy}><KeyRound />{busy ? "Saving…" : "Change password"}</button>
            </form>
          )}

          {step === 3 && (
            <div className="success-box">
              <div className="success-icon"><CheckCircle2 /></div>
              <h1>Password changed!</h1>
              <p className="muted">You can now log in with your new password.</p>
              <button className="btn btn-primary btn-block btn-lg mt" onClick={() => nav("/login")}>Go to login</button>
            </div>
          )}

          {step < 3 && <p className="muted" style={{ marginTop: 22, textAlign: "center" }}>
            <Link to="/login" className="row" style={{ justifyContent: "center", gap: 6 }}><ArrowLeft size={14} /> Back to login</Link></p>}
        </div>
      </div>
    </div>
  );
}
