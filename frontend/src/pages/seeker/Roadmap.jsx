import { CheckCircle2, Circle, ExternalLink, Flag, Hammer, Map, Rocket } from "lucide-react";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { Link } from "react-router-dom";
import api, { errMsg } from "../../api";
import { Chips, Empty, Loader, ScoreRing } from "../../components/ui";

export default function Roadmap() {
  const [role, setRole] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = async (r = role) => {
    setLoading(true);
    try {
      const res = await api.get("/resumes/roadmap/", { params: r ? { role: r } : {} });
      setData(res.data);
      setRole(res.data.role);
    } catch (e) { toast.error(errMsg(e)); } finally { setLoading(false); }
  };
  useEffect(() => { load(""); }, []);

  const toggle = async (step) => {
    const done = !step.done;
    setData((d) => ({ ...d, steps: d.steps.map((s) => (s.skill === step.skill ? { ...s, done } : s)) }));
    try {
      await api.post("/resumes/roadmap/", { skill: step.skill, done });
      if (done) toast.success(`Nice! ${step.skill} marked as learned. Add it to your resume 🎉`);
      load(role);
    } catch (e) { toast.error(errMsg(e)); }
  };

  if (!data && loading) return <Loader />;
  if (!data) return null;
  const doneCount = data.steps.filter((s) => s.done).length;

  return (
    <>
      <div className="page-head">
        <div><h1>Skill Roadmap</h1><p>Your personal week-by-week plan to become job-ready for a role</p></div>
        <select className="select" style={{ width: 260 }} value={role} onChange={(e) => load(e.target.value)}>
          {data.roles.map((r) => <option key={r} value={r}>{r}</option>)}
        </select>
      </div>

      {!data.has_resume && (
        <div className="info-strip" style={{ marginBottom: 18 }}>
          Upload your resume first so the roadmap can skip the skills you already have. <Link to="/resume">Upload resume →</Link>
        </div>
      )}

      {data.suggested_roles?.length > 0 && (
        <div className="row" style={{ marginBottom: 16, gap: 8 }}>
          <span className="small muted">Best-fit roles for you:</span>
          {data.suggested_roles.map((r) => (
            <button key={r} className={`chip ${r === role ? "brand" : ""}`} style={{ cursor: "pointer", border: 0 }} onClick={() => load(r)}>{r}</button>
          ))}
        </div>
      )}

      <div className="grid g-side">
        <div>
          {loading && <div className="skeleton" style={{ height: 120 }} />}
          {!loading && data.steps.length === 0 && (
            <div className="card"><Empty icon={Rocket} title={`You already have all the key skills for ${role}! 🎉`}
              text="Start applying to live jobs for this role." action={<Link className="btn btn-primary" to="/jobs">See live jobs</Link>} /></div>
          )}
          <div className="roadmap">
            {!loading && data.steps.map((s, i) => (
              <div key={s.skill} className={`rm-step ${s.done ? "done" : ""}`}>
                <div className="rm-dot">{s.done ? <CheckCircle2 /> : <span>{i + 1}</span>}</div>
                <div className="card rm-card">
                  <div className="row between" style={{ alignItems: "flex-start" }}>
                    <div>
                      <div className="row" style={{ gap: 8 }}>
                        <h3 style={{ margin: 0 }}>{s.skill}</h3>
                        <span className={`badge ${s.priority === "core" ? "b-red" : "b-gray"}`}>{s.priority === "core" ? "Must have" : "Good to have"}</span>
                        <span className="badge b-brand">{s.category}</span>
                      </div>
                      <p className="small muted" style={{ marginTop: 4 }}>
                        Week {s.week_start}{s.week_end > s.week_start ? `–${s.week_end}` : ""} • ~{s.weeks} week{s.weeks > 1 ? "s" : ""}
                      </p>
                    </div>
                    <button className={`btn btn-sm ${s.done ? "btn-success" : "btn-ghost"}`} onClick={() => toggle(s)}>
                      {s.done ? <><CheckCircle2 />Learned</> : <><Circle />Mark learned</>}
                    </button>
                  </div>
                  <p style={{ margin: "10px 0" }}>{s.why}</p>
                  <div className="tip" style={{ marginBottom: 10 }}>
                    <Hammer size={18} color="var(--brand)" />
                    <div><b>Mini project</b><p>{s.project}</p></div>
                  </div>
                  <div className="chips">
                    {s.links.map((l) => (
                      <a key={l.url} className="chip brand" href={l.url} target="_blank" rel="noreferrer">{l.title} <ExternalLink size={11} /></a>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ alignSelf: "start", display: "grid", gap: 18 }}>
          <div className="card" style={{ textAlign: "center" }}>
            <h3 style={{ justifyContent: "center" }}><Flag /> Job readiness</h3>
            <div className="center" style={{ padding: 8 }}><ScoreRing value={data.readiness} size={140} label="Ready" /></div>
            <p className="muted small">{role}</p>
            <div className="grid g-2 mt" style={{ gap: 10 }}>
              <div className="card" style={{ padding: 12, boxShadow: "none" }}><b style={{ fontSize: 20 }}>{data.remaining_weeks}</b><div className="small muted">weeks left</div></div>
              <div className="card" style={{ padding: 12, boxShadow: "none" }}><b style={{ fontSize: 20 }}>{doneCount}/{data.steps.length}</b><div className="small muted">skills learned</div></div>
            </div>
          </div>
          <div className="card">
            <h3><Map /> Skills you already have</h3>
            <Chips items={data.already_have} kind="ok" />
            <p className="small muted mt">Tip: when you finish a skill, add it to your resume and re-upload it to raise your ATS and match scores.</p>
          </div>
        </div>
      </div>
    </>
  );
}
