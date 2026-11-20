import { Save, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useNavigate, useParams } from "react-router-dom";
import api, { errMsg } from "../../api";
import { Loader } from "../../components/ui";

const EMPTY = { title: "", company: "", location: "", description: "", skills: [], job_type: "full_time", work_mode: "onsite",
  min_experience: 0, salary_min: "", salary_max: "", apply_url: "" };

export default function JobForm() {
  const { id } = useParams();
  const nav = useNavigate();
  const [f, setF] = useState(id ? null : EMPTY);
  const [skillsText, setSkillsText] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (id) api.get(`/jobs/${id}/`).then((r) => { setF({ ...r.data, salary_min: r.data.salary_min || "", salary_max: r.data.salary_max || "" }); setSkillsText(r.data.skills.join(", ")); });
  }, [id]);
  if (!f) return <Loader />;
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    const payload = {
      ...f,
      skills: skillsText.split(",").map((s) => s.trim()).filter(Boolean),
      salary_min: f.salary_min || null, salary_max: f.salary_max || null, min_experience: Number(f.min_experience || 0),
    };
    try {
      if (id) await api.put(`/jobs/${id}/`, payload); else await api.post("/jobs/", payload);
      toast.success(id ? "Job updated" : "Job posted! Candidates can now apply.");
      nav("/recruiter/jobs");
    } catch (err) { toast.error(errMsg(err)); } finally { setBusy(false); }
  };

  return (
    <>
      <div className="page-head"><div><h1>{id ? "Edit job" : "Post a new job"}</h1><p>AI automatically detects required skills from your description</p></div></div>
      <form className="card" onSubmit={submit} style={{ maxWidth: 900 }}>
        <div className="grid g-2" style={{ gap: 14 }}>
          <div className="field"><label>Job title *</label><input className="input" value={f.title} onChange={set("title")} required placeholder="e.g. Python Django Developer" /></div>
          <div className="field"><label>Company (default: your company)</label><input className="input" value={f.company} onChange={set("company")} /></div>
          <div className="field"><label>Location</label><input className="input" value={f.location} onChange={set("location")} placeholder="Pune" /></div>
          <div className="grid g-2" style={{ gap: 10 }}>
            <div className="field"><label>Job type</label><select className="select" value={f.job_type} onChange={set("job_type")}>
              <option value="full_time">Full Time</option><option value="internship">Internship</option><option value="part_time">Part Time</option><option value="contract">Contract</option></select></div>
            <div className="field"><label>Work mode</label><select className="select" value={f.work_mode} onChange={set("work_mode")}>
              <option value="onsite">On-site</option><option value="hybrid">Hybrid</option><option value="remote">Remote</option></select></div>
          </div>
          <div className="field"><label>Min. experience (years)</label><input className="input" type="number" step="0.5" min="0" value={f.min_experience} onChange={set("min_experience")} /></div>
          <div className="grid g-2" style={{ gap: 10 }}>
            <div className="field"><label>Salary min (₹/yr)</label><input className="input" type="number" value={f.salary_min} onChange={set("salary_min")} /></div>
            <div className="field"><label>Salary max (₹/yr)</label><input className="input" type="number" value={f.salary_max} onChange={set("salary_max")} /></div>
          </div>
        </div>
        <div className="field"><label>Job description *</label>
          <textarea className="textarea" style={{ minHeight: 220 }} value={f.description} onChange={set("description")} required
            placeholder="Responsibilities, requirements, required skills…" /></div>
        <div className="field"><label><Sparkles size={13} /> Required skills (comma separated — leave empty to auto-detect with AI)</label>
          <input className="input" value={skillsText} onChange={(e) => setSkillsText(e.target.value)} placeholder="Python, Django, PostgreSQL, REST API" /></div>
        <button className="btn btn-primary" disabled={busy}><Save />{busy ? "Saving…" : id ? "Update job" : "Publish job"}</button>
      </form>
    </>
  );
}
