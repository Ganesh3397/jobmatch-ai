import { BookOpen, History, Target, Wand2 } from "lucide-react";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import api, { errMsg } from "../../api";
import { Bar, Chips, Empty, MatchBadge, ScoreRing } from "../../components/ui";

const SAMPLE = `We are hiring a Python Django Developer.
Requirements:
- 1+ years experience with Python and Django / Django REST Framework
- Strong knowledge of PostgreSQL and REST API design
- Experience with Docker and AWS is a plus
- Familiarity with React for frontend integration
- Good communication and teamwork skills`;

export default function JDMatch() {
  const [title, setTitle] = useState("");
  const [jd, setJd] = useState("");
  const [busy, setBusy] = useState(false);
  const [res, setRes] = useState(null);
  const [history, setHistory] = useState([]);

  const loadHistory = () => api.get("/resumes/match-history/").then((r) => setHistory(r.data.results || []));
  useEffect(() => { loadHistory(); }, []);

  const run = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const { data } = await api.post("/resumes/match-jd/", { job_title: title, job_description: jd });
      setRes(data.result);
      loadHistory();
    } catch (err) { toast.error(errMsg(err)); } finally { setBusy(false); }
  };

  return (
    <>
      <div className="page-head"><div><h1>JD Matcher</h1><p>Paste any job description — AI tells you how well your resume fits</p></div></div>
      <div className="grid g-2">
        <form className="card" onSubmit={run}>
          <h3><Target /> Job description</h3>
          <div className="field"><label>Job title (optional)</label><input className="input" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Python Developer" /></div>
          <div className="field">
            <div className="row between"><label>Description</label>
              <button type="button" className="btn btn-soft btn-sm" onClick={() => { setTitle("Python Django Developer"); setJd(SAMPLE); }}>Use sample</button></div>
            <textarea className="textarea" style={{ minHeight: 260 }} value={jd} onChange={(e) => setJd(e.target.value)} placeholder="Paste the full job description from LinkedIn, Naukri, etc." required minLength={30} />
          </div>
          <button className="btn btn-primary" disabled={busy}><Wand2 />{busy ? "Analysing…" : "Check my match"}</button>
        </form>

        <div className="card">
          {!res ? <Empty icon={Target} title="Your match report will appear here" text="Paste a job description and click Check my match." /> : (
            <>
              <div className="row" style={{ gap: 24 }}>
                <ScoreRing value={res.score} size={140} label={res.label.split(" ")[0]} />
                <div style={{ flex: 1, minWidth: 200 }}>
                  <h3 style={{ marginBottom: 10 }}>{res.label}</h3>
                  <Bar label="Skill match" value={res.skill_score} right={`${res.skill_score}%`} />
                  <Bar label="AI content similarity" value={res.semantic_score} right={`${res.semantic_score}%`} />
                  <Bar label="Experience fit" value={res.experience_score} right={`${res.experience_score}%`} />
                </div>
              </div>
              <div className="mt"><div className="small muted" style={{ marginBottom: 6 }}>✅ Skills you have</div><Chips items={res.matched_skills} kind="ok" /></div>
              <div className="mt"><div className="small muted" style={{ marginBottom: 6 }}>⚠️ Skills to add / learn</div><Chips items={res.missing_skills} kind="miss" /></div>
              {res.missing_skills.length > 0 && (
                <div className="tip mt"><BookOpen size={18} color="#5b5bf7" />
                  <div><b>Tip</b><p>If you know {res.missing_skills.slice(0, 3).join(", ")}, add them to your resume skills section. Otherwise, learning them will raise your match score.</p></div>
                </div>
              )}
              <p className="small muted mt">AI engine: {res.engine}</p>
            </>
          )}
        </div>
      </div>

      {history.length > 0 && (
        <div className="card mt">
          <h3><History /> Recent checks</h3>
          <div className="table-wrap"><table>
            <thead><tr><th>Job title</th><th>Resume</th><th>Missing skills</th><th>Score</th><th>Date</th></tr></thead>
            <tbody>{history.map((h) => (
              <tr key={h.id}>
                <td><b>{h.job_title || "Untitled"}</b></td><td className="muted">{h.resume_name}</td>
                <td><Chips items={h.result.missing_skills || []} kind="miss" max={4} /></td>
                <td><MatchBadge score={h.score} /></td><td className="muted">{new Date(h.created_at).toLocaleDateString()}</td>
              </tr>
            ))}</tbody>
          </table></div>
        </div>
      )}
    </>
  );
}
