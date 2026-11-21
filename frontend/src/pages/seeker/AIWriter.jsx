import { Copy, Download, FileSignature, History, Sparkles, Wand2 } from "lucide-react";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useSearchParams } from "react-router-dom";
import api, { errMsg } from "../../api";
import { Chips, Empty } from "../../components/ui";

const copy = (t) => navigator.clipboard.writeText(t).then(() => toast.success("Copied"));
const download = (name, text) => {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([text], { type: "text/plain" }));
  a.download = name;
  a.click();
};

function Improver() {
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(false);
  const run = async () => {
    setBusy(true);
    try { setData((await api.post("/ai/improve-resume/", {})).data); } catch (e) { toast.error(errMsg(e)); } finally { setBusy(false); }
  };
  return (
    <>
      <div className="card">
        <div className="row between">
          <div><h3 style={{ margin: 0 }}><Wand2 /> Resume Improver</h3>
            <p className="small muted" style={{ marginTop: 4 }}>AI finds weak bullet points in your primary resume and rewrites them with action verbs and measurable impact.</p></div>
          <button className="btn btn-primary" disabled={busy} onClick={run}><Sparkles />{busy ? "Improving…" : data ? "Run again" : "Improve my resume"}</button>
        </div>
      </div>
      {data && (
        <>
          <div className="card mt">
            <div className="row between"><h3 style={{ margin: 0 }}>✨ Suggested professional summary</h3>
              <button className="btn btn-ghost btn-sm" onClick={() => copy(data.summary)}><Copy />Copy</button></div>
            <p className="mt" style={{ lineHeight: 1.6 }}>{data.summary}</p>
          </div>
          <div className="card mt">
            <h3>Bullet points to improve ({data.items.length})</h3>
            {data.items.length === 0 && <p className="muted">Your bullet points already look strong 🎉</p>}
            {data.items.map((it, i) => (
              <div key={i} className="grid g-2" style={{ gap: 12, padding: "12px 0", borderBottom: "1px solid var(--line)" }}>
                <div><div className="small muted" style={{ fontWeight: 700, marginBottom: 4 }}>Before</div><p style={{ color: "var(--muted)", textDecoration: "line-through" }}>{it.original}</p></div>
                <div>
                  <div className="row between"><span className="small" style={{ fontWeight: 700, color: "var(--green)" }}>After</span>
                    <button className="btn btn-ghost btn-sm" onClick={() => copy(it.improved)}><Copy /></button></div>
                  <p style={{ fontWeight: 600 }}>{it.improved}</p>
                  {it.why?.filter(Boolean).length > 0 && <p className="small muted" style={{ marginTop: 4 }}>💡 {it.why.join(" • ")}</p>}
                </div>
              </div>
            ))}
            <p className="small muted mt">Replace placeholders like [X]% with your real numbers, then update your resume and re-upload it. Engine: {data.engine}</p>
          </div>
        </>
      )}
    </>
  );
}

function CoverLetter() {
  const [params] = useSearchParams();
  const [jobs, setJobs] = useState([]);
  const [f, setF] = useState({ job_id: params.get("job") || "", job_title: "", company: "", description: "", tone: "professional" });
  const [out, setOut] = useState(null);
  const [busy, setBusy] = useState(false);
  const [history, setHistory] = useState([]);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  useEffect(() => {
    api.get("/jobs/saved/").then((r) => setJobs(r.data.map((s) => s.job))).catch(() => {});
    api.get("/ai/cover-letters/").then((r) => setHistory(r.data));
  }, []);

  const run = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const payload = f.job_id ? { job_id: f.job_id, tone: f.tone } : f;
      const { data } = await api.post("/ai/cover-letters/", payload);
      setOut(data);
      api.get("/ai/cover-letters/").then((r) => setHistory(r.data));
    } catch (err) { toast.error(errMsg(err)); } finally { setBusy(false); }
  };

  return (
    <div className="grid g-2">
      <form className="card" onSubmit={run}>
        <h3><FileSignature /> Cover Letter Generator</h3>
        <div className="field"><label>Pick a saved job (optional)</label>
          <select className="select" value={f.job_id} onChange={set("job_id")}>
            <option value="">— Type job details manually —</option>
            {jobs.map((j) => <option key={j.id} value={j.id}>{j.title} • {j.company}</option>)}
            {params.get("job") && !jobs.find((j) => String(j.id) === params.get("job")) && <option value={params.get("job")}>Selected job</option>}
          </select></div>
        {!f.job_id && (
          <>
            <div className="grid g-2" style={{ gap: 12 }}>
              <div className="field"><label>Job title</label><input className="input" value={f.job_title} onChange={set("job_title")} required placeholder="Python Developer" /></div>
              <div className="field"><label>Company</label><input className="input" value={f.company} onChange={set("company")} placeholder="Infosys" /></div>
            </div>
            <div className="field"><label>Job description (optional, better results)</label>
              <textarea className="textarea" style={{ minHeight: 100 }} value={f.description} onChange={set("description")} /></div>
          </>
        )}
        <div className="field"><label>Tone</label>
          <div className="tabs">{["professional", "enthusiastic", "confident"].map((t) => (
            <button type="button" key={t} className={f.tone === t ? "on" : ""} onClick={() => setF({ ...f, tone: t })} style={{ textTransform: "capitalize" }}>{t}</button>
          ))}</div></div>
        <button className="btn btn-primary" disabled={busy}><Sparkles />{busy ? "Writing…" : "Generate cover letter"}</button>
      </form>

      <div className="card">
        {!out ? <Empty icon={FileSignature} title="Your cover letter will appear here" text="Pick a job or enter the details and click Generate." /> : (
          <>
            <div className="row between"><h3 style={{ margin: 0 }}>{out.job_title} • {out.company}</h3>
              <div className="row" style={{ gap: 6 }}>
                <button className="btn btn-ghost btn-sm" onClick={() => copy(out.letter)}><Copy />Copy</button>
                <button className="btn btn-ghost btn-sm" onClick={() => download(`Cover_Letter_${out.company}.txt`, out.letter)}><Download /></button>
              </div></div>
            <textarea className="textarea mt" style={{ minHeight: 360 }} value={out.letter} onChange={(e) => setOut({ ...out, letter: e.target.value })} />
            {out.matched_skills?.length > 0 && <div className="mt"><div className="small muted" style={{ marginBottom: 6 }}>Highlighted skills</div><Chips items={out.matched_skills} kind="ok" /></div>}
            <p className="small muted mt">You can edit the text above before copying. Engine: {out.engine}</p>
          </>
        )}
        {history.length > 0 && (
          <div className="mt">
            <div className="small muted" style={{ fontWeight: 700, marginBottom: 6 }}><History size={13} /> Recent letters</div>
            {history.slice(0, 5).map((h) => (
              <div key={h.id} className="row between" style={{ padding: "6px 0", cursor: "pointer" }} onClick={() => setOut({ ...h, matched_skills: [] })}>
                <span className="small">{h.job_title} • {h.company}</span><span className="small muted">{new Date(h.created_at).toLocaleDateString()}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function AIWriter() {
  const [params] = useSearchParams();
  const [tab, setTab] = useState(params.get("job") ? "letter" : "improve");
  return (
    <>
      <div className="page-head">
        <div><h1>AI Resume Writer</h1><p>Make your resume stronger and write job-specific cover letters in seconds</p></div>
        <div className="tabs">
          <button className={tab === "improve" ? "on" : ""} onClick={() => setTab("improve")}>Resume Improver</button>
          <button className={tab === "letter" ? "on" : ""} onClick={() => setTab("letter")}>Cover Letter</button>
        </div>
      </div>
      {tab === "improve" ? <Improver /> : <CoverLetter />}
    </>
  );
}
