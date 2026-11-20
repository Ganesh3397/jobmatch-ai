import { CheckCircle2, ExternalLink, FileText, Github, GraduationCap, Linkedin, Mail, Phone, RefreshCw, Star, Trash2, UploadCloud, User } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import toast from "react-hot-toast";
import { Link } from "react-router-dom";
import api, { errMsg } from "../../api";
import { Bar, Chips, Empty, Loader, ScoreRing, StatusBadge } from "../../components/ui";

const PRI = { high: "#f04438", medium: "#f5a524", low: "#12b76a" };

export default function ResumePage() {
  const [list, setList] = useState(null);
  const [sel, setSel] = useState(null);
  const [detail, setDetail] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [drag, setDrag] = useState(false);
  const input = useRef();

  const load = async (selectId) => {
    const { data } = await api.get("/resumes/");
    setList(data);
    const exists = (x) => x && data.some((r) => r.id === x);
    const id = [selectId, sel, data.find((r) => r.is_primary)?.id, data[0]?.id].find(exists);
    if (id) open(id); else { setSel(null); setDetail(null); }
  };
  const open = async (id) => {
    setSel(id);
    let data;
    try { ({ data } = await api.get(`/resumes/${id}/`)); } catch { setSel(null); setDetail(null); return; }
    setDetail(data);
    if (data.status === "pending" || data.status === "processing") setTimeout(() => open(id), 2000); // Celery mode polling
  };
  useEffect(() => { load(); }, []);

  const upload = async (file) => {
    if (!file) return;
    if (!/\.(pdf|docx|txt)$/i.test(file.name)) return toast.error("Please upload a PDF, DOCX or TXT file");
    const fd = new FormData();
    fd.append("file", file);
    setUploading(true);
    try {
      const { data } = await api.post("/resumes/", fd);
      if (data.status === "failed") toast.error(data.error || "Could not analyse resume");
      else toast.success("Resume analysed by AI ✨");
      load(data.id);
    } catch (e) { toast.error(errMsg(e)); } finally { setUploading(false); }
  };

  const del = async (id) => {
    if (!window.confirm("Delete this resume?")) return;
    await api.delete(`/resumes/${id}/`);
    setDetail(null); setSel(null);
    const { data } = await api.get("/resumes/");
    setList(data);
    const next = data.find((r) => r.is_primary) || data[0];
    if (next) open(next.id);
  };
  const primary = async (id) => { await api.post(`/resumes/${id}/set-primary/`); toast.success("Set as primary resume"); load(id); };
  const rerun = async (id) => { const { data } = await api.post(`/resumes/${id}/reanalyze/`); setDetail(data); toast.success("Re-analysed"); };

  if (!list) return <Loader />;
  const a = detail?.analysis;

  return (
    <>
      <div className="page-head">
        <div><h1>My Resume & ATS Report</h1><p>AI parses your resume, scores it and suggests improvements</p></div>
      </div>

      <div className="grid g-side">
        <div>
          <div className={`dropzone ${drag ? "drag" : ""}`} onClick={() => input.current.click()}
            onDragOver={(e) => { e.preventDefault(); setDrag(true); }} onDragLeave={() => setDrag(false)}
            onDrop={(e) => { e.preventDefault(); setDrag(false); upload(e.dataTransfer.files[0]); }}>
            <input ref={input} type="file" hidden accept=".pdf,.docx,.txt" onChange={(e) => upload(e.target.files[0])} />
            {uploading ? <><div className="center" style={{ padding: 10 }}><div className="spinner" /></div><b>AI is reading your resume…</b></> : (
              <><UploadCloud /><h4 style={{ marginBottom: 4 }}>Drop your resume here or click to upload</h4>
                <p className="muted small">PDF, DOCX or TXT • max 5 MB</p></>
            )}
          </div>

          {detail && detail.status === "failed" && <div className="info-strip mt">⚠️ {detail.error}</div>}
          {detail && (detail.status === "pending" || detail.status === "processing") && (
            <div className="card mt"><div className="row"><div className="spinner" /> Analysing in background (Celery worker)…</div></div>
          )}

          {detail && detail.status === "done" && a && (
            <>
              <div className="card mt">
                <div className="row" style={{ gap: 28, alignItems: "center" }}>
                  <ScoreRing value={detail.ats_score} size={150} label="ATS Score" />
                  <div style={{ flex: 1, minWidth: 260 }}>
                    <div className="row between" style={{ marginBottom: 10 }}>
                      <h3 style={{ margin: 0 }}>Score breakdown</h3>
                      <span className={`badge ${detail.ats_score >= 80 ? "b-green" : detail.ats_score >= 60 ? "b-brand" : "b-amber"}`}>{a.grade}</span>
                    </div>
                    {a.breakdown.map((b) => <Bar key={b.label} label={b.label} value={b.score} max={b.max} />)}
                  </div>
                </div>
              </div>

              <div className="grid g-2 mt">
                <div className="card">
                  <h3><User /> Extracted details</h3>
                  <div style={{ display: "grid", gap: 10 }}>
                    <div className="row"><User size={15} className="muted" /> {detail.candidate_name || <span className="muted">Name not found</span>}</div>
                    <div className="row"><Mail size={15} className="muted" /> {detail.email || <span className="muted">Not found</span>}</div>
                    <div className="row"><Phone size={15} className="muted" /> {detail.phone || <span className="muted">Not found</span>}</div>
                    <div className="row"><Linkedin size={15} className="muted" /> {detail.links?.linkedin || <span className="muted">Not found</span>}</div>
                    <div className="row"><Github size={15} className="muted" /> {detail.links?.github || <span className="muted">Not found</span>}</div>
                    <div className="row"><GraduationCap size={15} className="muted" /> {detail.education?.join(", ") || <span className="muted">Not found</span>}</div>
                    <div className="row"><Star size={15} className="muted" /> {detail.experience_years} years experience</div>
                  </div>
                  <div className="small muted mt">Sections found</div>
                  <Chips items={detail.sections_found} kind="brand" />
                </div>
                <div className="card">
                  <h3><CheckCircle2 /> Improvement tips</h3>
                  {a.tips.length === 0 && <p className="muted">Great job! No major issues found. 🎉</p>}
                  {a.tips.map((t) => (
                    <div className="tip" key={t.title}>
                      <div className="tip-dot" style={{ background: PRI[t.priority] }} />
                      <div><b>{t.title}</b><p>{t.detail}</p></div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="card mt">
                <h3>Skills detected by AI ({detail.skills.length})</h3>
                <div className="grid g-2">
                  {Object.entries(detail.skills_by_category).map(([cat, skills]) => (
                    <div key={cat}><div className="small muted" style={{ marginBottom: 6, fontWeight: 600 }}>{cat}</div><Chips items={skills} kind="brand" /></div>
                  ))}
                </div>
              </div>

              <div className="card mt">
                <div className="row between">
                  <h3 style={{ margin: 0 }}>🎯 Recommended roles</h3>
                  <Link to="/jobs" className="btn btn-primary btn-sm">Find live jobs</Link>
                </div>
                <div className="grid g-3 mt">
                  {detail.predicted_roles.map((r) => (
                    <div key={r.role} className="card" style={{ background: "#fafbff", boxShadow: "none" }}>
                      <b>{r.role}</b>
                      <div className="bar" style={{ margin: "10px 0 6px" }}><div style={{ width: `${r.fit}%` }} /></div>
                      <p className="small muted">{r.fit}% fit{r.missing_core_skills.length ? ` • Learn ${r.missing_core_skills.join(", ")}` : ""}</p>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>

        <div className="card" style={{ alignSelf: "start" }}>
          <h3><FileText /> My resumes</h3>
          {list.length === 0 && <Empty title="No resumes" text="Upload your first resume" />}
          {list.map((r) => (
            <div key={r.id} onClick={() => open(r.id)} style={{
              padding: 12, borderRadius: 12, marginBottom: 8, cursor: "pointer",
              border: `1.5px solid ${sel === r.id ? "#5b5bf7" : "#e6e8f2"}`, background: sel === r.id ? "#f6f6ff" : "#fff",
            }}>
              <div className="row between">
                <b style={{ fontSize: 13.5, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: 180 }}>{r.original_name}</b>
                {r.is_primary && <span className="badge b-brand">Primary</span>}
              </div>
              <div className="row between small muted" style={{ marginTop: 6 }}>
                <span>{new Date(r.created_at).toLocaleDateString()}</span>
                {r.status === "done" ? <b style={{ color: "#1b1f33" }}>ATS {r.ats_score}</b> : <StatusBadge s={r.status} />}
              </div>
              {sel === r.id && (
                <div className="row" style={{ marginTop: 10, gap: 6 }} onClick={(e) => e.stopPropagation()}>
                  {!r.is_primary && <button className="btn btn-soft btn-sm" onClick={() => primary(r.id)}><Star />Primary</button>}
                  <button className="btn btn-ghost btn-sm" title="Re-analyse" onClick={() => rerun(r.id)}><RefreshCw /></button>
                  {detail?.file_url && <a className="btn btn-ghost btn-sm" href={detail.file_url} target="_blank" rel="noreferrer"><ExternalLink /></a>}
                  <button className="btn btn-danger btn-sm" onClick={() => del(r.id)}><Trash2 /></button>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
