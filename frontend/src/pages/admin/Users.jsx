import { CheckCircle2, KeyRound, Mail, Search, Send, UserPlus, X } from "lucide-react";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import api, { errMsg } from "../../api";
import { Loader, Modal } from "../../components/ui";

const EMPTY = { first_name: "", last_name: "", username: "", email: "", company_name: "", password: "", role: "recruiter" };

function AddUserModal({ onClose, onDone }) {
  const [f, setF] = useState(EMPTY);
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api.post("/auth/users/create/", f);
      toast.success(`Recruiter "${f.username}" created`);
      onDone();
      onClose();
    } catch (err) { toast.error(errMsg(err)); } finally { setBusy(false); }
  };
  return (
    <Modal onClose={onClose}>
      <div className="modal-head"><div><h2 style={{ fontSize: 20 }}>Add recruiter</h2>
        <p className="muted">Public sign-up creates students only. Recruiter accounts are created here by the admin.</p></div>
        <button className="btn btn-ghost btn-sm" onClick={onClose}><X /></button></div>
      <form className="modal-body" onSubmit={submit}>
        <div className="grid g-2" style={{ gap: 12 }}>
          <div className="field"><label>First name</label><input className="input" value={f.first_name} onChange={set("first_name")} required /></div>
          <div className="field"><label>Last name</label><input className="input" value={f.last_name} onChange={set("last_name")} /></div>
          <div className="field"><label>Username</label><input className="input" value={f.username} onChange={set("username")} required /></div>
          <div className="field"><label>Email</label><input className="input" type="email" value={f.email} onChange={set("email")} required /></div>
          <div className="field"><label>Company name</label><input className="input" value={f.company_name} onChange={set("company_name")} required /></div>
          <div className="field"><label>Password</label><input className="input" type="password" minLength={6} value={f.password} onChange={set("password")} required /></div>
        </div>
        <button className="btn btn-primary" disabled={busy}><UserPlus />{busy ? "Creating…" : "Create recruiter"}</button>
      </form>
    </Modal>
  );
}

function SetPasswordModal({ user, onClose }) {
  const [pw, setPw] = useState("");
  const [busy, setBusy] = useState(false);
  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api.post(`/auth/users/${user.id}/set-password/`, { password: pw });
      toast.success(`New password set for ${user.username}. Share it with them privately.`);
      onClose();
    } catch (err) { toast.error(errMsg(err)); } finally { setBusy(false); }
  };
  return (
    <Modal onClose={onClose}>
      <div className="modal-head"><div><h2 style={{ fontSize: 20 }}>Set new password</h2>
        <p className="muted">For @{user.username} ({user.email})</p></div>
        <button className="btn btn-ghost btn-sm" onClick={onClose}><X /></button></div>
      <form className="modal-body" onSubmit={submit}>
        <div className="field"><label>New password</label>
          <input className="input" type="text" minLength={6} value={pw} onChange={(e) => setPw(e.target.value)} required autoFocus /></div>
        <button className="btn btn-primary" disabled={busy}><KeyRound />{busy ? "Saving…" : "Set password"}</button>
      </form>
    </Modal>
  );
}

function EmailCard() {
  const [st, setSt] = useState(null);
  const [to, setTo] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  useEffect(() => { api.get("/auth/email/status/").then((r) => setSt(r.data)).catch(() => {}); }, []);
  const test = async (e) => {
    e.preventDefault();
    setBusy(true); setResult(null);
    try { const { data } = await api.post("/auth/email/test/", { to }); setResult({ ok: true, msg: data.detail }); }
    catch (err) { setResult({ ok: false, msg: errMsg(err) }); } finally { setBusy(false); }
  };
  if (!st) return null;
  const names = { brevo: "Brevo API", gmail: "Gmail SMTP", smtp: "SMTP" };
  return (
    <div className="card email-card">
      <div className="row between" style={{ alignItems: "flex-start" }}>
        <div className="row" style={{ alignItems: "flex-start", flexWrap: "nowrap" }}>
          <div className="stat-icon" style={{ background: st.configured ? "var(--green-soft)" : "var(--amber-soft)", color: st.configured ? "var(--green)" : "var(--amber)" }}><Mail /></div>
          <div>
            <h3 style={{ margin: 0 }}>Email for "Forgot password"</h3>
            {st.configured
              ? <p className="small muted"><CheckCircle2 size={13} style={{ verticalAlign: -2, color: "var(--green)" }} /> Active via <b>{names[st.provider]}</b>, sending from <b>{st.sender}</b></p>
              : <p className="small muted">Not set up. Users can't get reset codes. Add <code>BREVO_API_KEY</code> (Render) or a Gmail App Password (laptop). See README → Email setup. You can still reset passwords with 🔑 below.</p>}
          </div>
        </div>
        {st.configured && (
          <form className="row" onSubmit={test}>
            <input className="input" type="email" placeholder="Send a test to…" value={to} onChange={(e) => setTo(e.target.value)} required style={{ width: 220 }} />
            <button className="btn btn-soft" disabled={busy}><Send />{busy ? "Sending…" : "Send test"}</button>
          </form>
        )}
      </div>
      {result && <div className={`alert ${result.ok ? "alert-ok" : "alert-error"} mt`}>{result.msg}</div>}
    </div>
  );
}

export default function AdminUsers() {
  const [data, setData] = useState(null);
  const [search, setSearch] = useState("");
  const [role, setRole] = useState("");
  const [adding, setAdding] = useState(false);
  const [pwUser, setPwUser] = useState(null);

  const load = () => api.get("/auth/users/", { params: { search, role } }).then((r) => setData(r.data));
  useEffect(() => { load(); }, [role]);

  const toggle = async (u) => {
    try { await api.post(`/auth/users/${u.id}/toggle/`); toast.success("Updated"); load(); } catch (e) { toast.error(errMsg(e)); }
  };

  return (
    <>
      <div className="page-head">
        <div><h1>Users</h1><p>Manage all platform users. Public sign-up creates job seekers only.</p></div>
        <button className="btn btn-primary" onClick={() => setAdding(true)}><UserPlus />Add recruiter</button>
      </div>
      {adding && <AddUserModal onClose={() => setAdding(false)} onDone={load} />}
      {pwUser && <SetPasswordModal user={pwUser} onClose={() => setPwUser(null)} />}
      <EmailCard />
      <form className="card search-bar mt" onSubmit={(e) => { e.preventDefault(); load(); }}>
        <div className="search-input"><Search /><input className="input" placeholder="Search name, username or email" value={search} onChange={(e) => setSearch(e.target.value)} /></div>
        <select className="select" style={{ width: 170 }} value={role} onChange={(e) => setRole(e.target.value)}>
          <option value="">All roles</option><option value="seeker">Job seekers</option><option value="recruiter">Recruiters</option><option value="admin">Admins</option>
        </select>
        <button className="btn btn-primary">Search</button>
      </form>
      <div className="card mt">
        {!data ? <Loader /> : (
          <div className="table-wrap"><table>
            <thead><tr><th>User</th><th>Email</th><th>Role</th><th>Company / City</th><th>Joined</th><th>Last login</th><th>Status</th><th></th></tr></thead>
            <tbody>{data.results.map((u) => (
              <tr key={u.id}>
                <td><b>{u.first_name} {u.last_name}</b><div className="small muted">@{u.username}</div></td>
                <td className="muted">{u.email}</td>
                <td><span className="badge b-brand" style={{ textTransform: "capitalize" }}>{u.role}</span></td>
                <td className="muted">{u.company_name || u.location || "—"}</td>
                <td className="muted">{new Date(u.date_joined).toLocaleDateString()}</td>
                <td className="muted">{u.last_login ? new Date(u.last_login).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }) : "Never"}</td>
                <td><span className={`badge ${u.is_active !== false ? "b-green" : "b-red"}`}>{u.is_active !== false ? "Active" : "Disabled"}</span></td>
                <td><div className="row" style={{ gap: 6, flexWrap: "nowrap" }}>
                  <button className="btn btn-ghost btn-sm" title="Set new password" onClick={() => setPwUser(u)}><KeyRound /></button>
                  {u.role !== "admin" && <button className="btn btn-ghost btn-sm" onClick={() => toggle(u)}>{u.is_active !== false ? "Disable" : "Enable"}</button>}
                </div></td>
              </tr>
            ))}</tbody>
          </table></div>
        )}
        {data && <p className="small muted mt">{data.count} users</p>}
      </div>
    </>
  );
}
