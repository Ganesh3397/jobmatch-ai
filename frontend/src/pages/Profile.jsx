import { useState } from "react";
import toast from "react-hot-toast";
import api, { errMsg } from "../api";
import { useAuth } from "../auth";

export default function Profile() {
  const { user, setUser } = useAuth();
  const [f, setF] = useState({ ...user });
  const [pw, setPw] = useState({ old_password: "", new_password: "" });
  const set = (k) => (e) => setF({ ...f, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value });

  const save = async (e) => {
    e.preventDefault();
    try {
      const { data } = await api.patch("/auth/me/", f);
      setUser(data);
      toast.success("Profile updated");
    } catch (err) { toast.error(errMsg(err)); }
  };

  const changePw = async (e) => {
    e.preventDefault();
    try {
      await api.post("/auth/change-password/", pw);
      toast.success("Password changed");
      setPw({ old_password: "", new_password: "" });
    } catch (err) { toast.error(errMsg(err)); }
  };

  return (
    <>
      <div className="page-head"><div><h1>Profile</h1><p>Manage your account details</p></div></div>
      <div className="grid g-side">
        <form className="card" onSubmit={save}>
          <h3>Personal details</h3>
          <div className="grid g-2" style={{ gap: 12 }}>
            <div className="field"><label>First name</label><input className="input" value={f.first_name || ""} onChange={set("first_name")} /></div>
            <div className="field"><label>Last name</label><input className="input" value={f.last_name || ""} onChange={set("last_name")} /></div>
            <div className="field"><label>Email</label><input className="input" value={f.email || ""} onChange={set("email")} /></div>
            <div className="field"><label>Phone</label><input className="input" value={f.phone || ""} onChange={set("phone")} /></div>
            <div className="field"><label>City</label><input className="input" value={f.location || ""} onChange={set("location")} /></div>
            {user.role === "recruiter"
              ? <div className="field"><label>Company</label><input className="input" value={f.company_name || ""} onChange={set("company_name")} /></div>
              : <div className="field"><label>Headline</label><input className="input" value={f.headline || ""} onChange={set("headline")} placeholder="MCA Student | Python Developer" /></div>}
          </div>
          {user.role === "seeker" && (
            <label className="row" style={{ marginBottom: 16, cursor: "pointer" }}>
              <input type="checkbox" checked={!!f.job_alerts_enabled} onChange={set("job_alerts_enabled")} />
              Email me daily job alerts that match my resume
            </label>
          )}
          <button className="btn btn-primary">Save changes</button>
        </form>
        <form className="card" onSubmit={changePw} style={{ alignSelf: "start" }}>
          <h3>Change password</h3>
          <div className="field"><label>Current password</label><input className="input" type="password" value={pw.old_password} onChange={(e) => setPw({ ...pw, old_password: e.target.value })} required /></div>
          <div className="field"><label>New password</label><input className="input" type="password" minLength={6} value={pw.new_password} onChange={(e) => setPw({ ...pw, new_password: e.target.value })} required /></div>
          <button className="btn btn-ghost">Update password</button>
        </form>
      </div>
    </>
  );
}
