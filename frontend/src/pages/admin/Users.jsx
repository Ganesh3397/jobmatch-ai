import { Search, UserPlus, X } from "lucide-react";
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
        <p className="muted">Only admins can create recruiter accounts</p></div>
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

export default function AdminUsers() {
  const [data, setData] = useState(null);
  const [search, setSearch] = useState("");
  const [role, setRole] = useState("");
  const [adding, setAdding] = useState(false);

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
      <form className="card search-bar" onSubmit={(e) => { e.preventDefault(); load(); }}>
        <div className="search-input"><Search /><input className="input" placeholder="Search name, username or email" value={search} onChange={(e) => setSearch(e.target.value)} /></div>
        <select className="select" style={{ width: 170 }} value={role} onChange={(e) => setRole(e.target.value)}>
          <option value="">All roles</option><option value="seeker">Job seekers</option><option value="recruiter">Recruiters</option><option value="admin">Admins</option>
        </select>
        <button className="btn btn-primary">Search</button>
      </form>
      <div className="card mt">
        {!data ? <Loader /> : (
          <div className="table-wrap"><table>
            <thead><tr><th>User</th><th>Email</th><th>Role</th><th>Company / City</th><th>Joined</th><th>Status</th><th></th></tr></thead>
            <tbody>{data.results.map((u) => (
              <tr key={u.id}>
                <td><b>{u.first_name} {u.last_name}</b><div className="small muted">@{u.username}</div></td>
                <td className="muted">{u.email}</td>
                <td><span className="badge b-brand" style={{ textTransform: "capitalize" }}>{u.role}</span></td>
                <td className="muted">{u.company_name || u.location || "—"}</td>
                <td className="muted">{new Date(u.date_joined).toLocaleDateString()}</td>
                <td><span className={`badge ${u.is_active !== false ? "b-green" : "b-red"}`}>{u.is_active !== false ? "Active" : "Disabled"}</span></td>
                <td>{u.role !== "admin" && <button className="btn btn-ghost btn-sm" onClick={() => toggle(u)}>{u.is_active !== false ? "Disable" : "Enable"}</button>}</td>
              </tr>
            ))}</tbody>
          </table></div>
        )}
        {data && <p className="small muted mt">{data.count} users</p>}
      </div>
    </>
  );
}
