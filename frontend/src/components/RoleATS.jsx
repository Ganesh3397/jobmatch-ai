import { Briefcase, Target } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api";
import { Bar, Chips, ScoreRing } from "./ui";

const PRI = { high: "#f04438", medium: "#f5a524", low: "#12b76a" };

/** ATS score of the resume for a chosen target role (Full Stack, Support, Data Analyst ...). */
export default function RoleATS({ resumeId }) {
  const [role, setRole] = useState("");
  const [d, setD] = useState(null);
  const [loading, setLoading] = useState(false);

  const load = (r = role) => {
    setLoading(true);
    api.get(`/resumes/${resumeId}/role-ats/`, { params: r ? { role: r } : {} })
      .then((res) => { setD(res.data); setRole(res.data.role); })
      .finally(() => setLoading(false));
  };
  useEffect(() => { setRole(""); load(""); }, [resumeId]);
  if (!d) return null;

  return (
    <div className="card mt">
      <div className="row between" style={{ alignItems: "flex-start" }}>
        <div>
          <h3 style={{ margin: 0 }}><Target /> ATS score for a target role</h3>
          <p className="small muted" style={{ marginTop: 4 }}>Every role needs different skills. Pick the job you are applying for to see how an ATS would score your resume for it.</p>
        </div>
        <select className="select" style={{ width: 260 }} value={role} onChange={(e) => load(e.target.value)}>
          {Object.entries(d.groups).map(([g, roles]) => (
            <optgroup key={g} label={g}>{roles.map((r) => <option key={r} value={r}>{r}</option>)}</optgroup>
          ))}
        </select>
      </div>

      <div className="row mt" style={{ gap: 28, alignItems: "center", opacity: loading ? 0.5 : 1 }}>
        <div style={{ textAlign: "center" }}>
          <ScoreRing value={d.score} size={140} label={d.grade} />
          <p className="small muted" style={{ marginTop: 6, maxWidth: 160 }}>{d.role}</p>
        </div>
        <div style={{ flex: 1, minWidth: 240 }}>
          {d.breakdown.map((b) => <Bar key={b.label} label={b.label} value={b.score} max={b.max} />)}
        </div>
      </div>

      <div className="grid g-2 mt" style={{ gap: 14 }}>
        <div><div className="small muted" style={{ fontWeight: 700, marginBottom: 6 }}>✅ Must-have skills you have</div><Chips items={d.matched_core} kind="ok" /></div>
        <div><div className="small muted" style={{ fontWeight: 700, marginBottom: 6 }}>⚠️ Must-have skills missing</div><Chips items={d.missing_core} kind="miss" /></div>
        <div><div className="small muted" style={{ fontWeight: 700, marginBottom: 6 }}>Good-to-have skills you have</div><Chips items={d.matched_bonus} kind="ok" max={8} /></div>
        <div><div className="small muted" style={{ fontWeight: 700, marginBottom: 6 }}>Role keywords missing in your text</div><Chips items={d.keywords_missing} max={8} /></div>
      </div>

      {d.tips.length > 0 && (
        <div className="mt">
          {d.tips.map((t) => (
            <div className="tip" key={t.title}><div className="tip-dot" style={{ background: PRI[t.priority] }} /><div><b>{t.title}</b><p>{t.detail}</p></div></div>
          ))}
        </div>
      )}

      <div className="mt">
        <div className="row between" style={{ marginBottom: 8 }}>
          <span className="small muted" style={{ fontWeight: 700 }}><Briefcase size={13} /> Roles your resume fits best</span>
          <Link to="/roadmap" className="small">Close the skill gap with a roadmap →</Link>
        </div>
        <div className="chips">
          {d.ranking.map((r) => (
            <button key={r.role} className={`chip ${r.role === d.role ? "brand" : ""}`} style={{ cursor: "pointer", border: 0 }} onClick={() => load(r.role)}>
              {r.role} · {r.score}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
