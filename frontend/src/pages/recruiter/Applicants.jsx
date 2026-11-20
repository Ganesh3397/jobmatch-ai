import { ArrowLeft, FileText, Mail, Users } from "lucide-react";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { Link, useParams } from "react-router-dom";
import api from "../../api";
import { Chips, Empty, Loader, Modal, ScoreRing, Bar, StatusBadge } from "../../components/ui";

const STATUSES = ["applied", "shortlisted", "interview", "rejected", "hired"];

export default function Applicants() {
  const { id } = useParams();
  const [job, setJob] = useState(null);
  const [apps, setApps] = useState(null);
  const [filter, setFilter] = useState("");
  const [view, setView] = useState(null);

  const load = () => api.get(`/jobs/${id}/applicants/`, { params: filter ? { status: filter } : {} }).then((r) => setApps(r.data));
  useEffect(() => { api.get(`/jobs/${id}/`).then((r) => setJob(r.data)); }, [id]);
  useEffect(() => { load(); }, [filter]);

  const setStatus = async (a, status) => {
    await api.patch(`/jobs/applications/${a.id}/`, { status });
    toast.success(`Marked as ${status}`);
    load();
  };

  if (!apps || !job) return <Loader />;
  return (
    <>
      <Link to="/recruiter/jobs" className="btn btn-ghost btn-sm" style={{ marginBottom: 14 }}><ArrowLeft />Back</Link>
      <div className="page-head">
        <div><h1>{job.title}</h1><p>{apps.length} applicants • ranked by AI match score</p></div>
        <div className="tabs">
          <button className={!filter ? "on" : ""} onClick={() => setFilter("")}>All</button>
          {STATUSES.map((s) => <button key={s} className={filter === s ? "on" : ""} onClick={() => setFilter(s)} style={{ textTransform: "capitalize" }}>{s}</button>)}
        </div>
      </div>
      <div className="card">
        {apps.length === 0 ? <Empty icon={Users} title="No applicants yet" /> : (
          <div className="table-wrap"><table>
            <thead><tr><th>#</th><th>Candidate</th><th>AI match</th><th>Matched skills</th><th>Missing</th><th>Exp</th><th>ATS</th><th>Status</th><th></th></tr></thead>
            <tbody>{apps.map((a, i) => (
              <tr key={a.id}>
                <td><b>{i + 1}</b></td>
                <td><b>{a.seeker_name}</b><div className="small muted">{a.seeker_email}</div></td>
                <td><ScoreRing value={a.match_score} size={54} stroke={6} label="" /></td>
                <td><Chips items={a.match_result.matched_skills || []} kind="ok" max={4} /></td>
                <td><Chips items={a.match_result.missing_skills || []} kind="miss" max={3} /></td>
                <td>{a.experience_years}y</td>
                <td>{a.resume_ats}</td>
                <td><select className="select" style={{ padding: "6px 8px", width: 130 }} value={a.status} onChange={(e) => setStatus(a, e.target.value)}>
                  {STATUSES.map((s) => <option key={s} value={s}>{s[0].toUpperCase() + s.slice(1)}</option>)}</select></td>
                <td><button className="btn btn-soft btn-sm" onClick={() => setView(a)}>View</button></td>
              </tr>
            ))}</tbody>
          </table></div>
        )}
      </div>

      {view && (
        <Modal onClose={() => setView(null)}>
          <div className="modal-head"><div><h2 style={{ fontSize: 20 }}>{view.seeker_name}</h2><p className="muted">{view.seeker_email}</p></div><StatusBadge s={view.status} /></div>
          <div className="modal-body">
            <div className="row" style={{ gap: 24 }}>
              <ScoreRing value={view.match_score} size={120} label="Match" />
              <div style={{ flex: 1, minWidth: 220 }}>
                <Bar label="Skill match" value={view.match_result.skill_score} right={`${view.match_result.skill_score}%`} />
                <Bar label="AI similarity" value={view.match_result.semantic_score} right={`${view.match_result.semantic_score}%`} />
                <Bar label="Experience fit" value={view.match_result.experience_score} right={`${view.match_result.experience_score}%`} />
              </div>
            </div>
            <div className="mt"><div className="small muted" style={{ marginBottom: 6 }}>All candidate skills</div><Chips items={view.resume_skills || []} kind="brand" /></div>
            {view.cover_note && <div className="tip mt"><Mail size={18} /><div><b>Cover note</b><p>{view.cover_note}</p></div></div>}
            <div className="row mt">
              {view.resume_url && <a className="btn btn-primary" href={view.resume_url} target="_blank" rel="noreferrer"><FileText />Open resume</a>}
              <a className="btn btn-ghost" href={`mailto:${view.seeker_email}`}><Mail />Email candidate</a>
            </div>
          </div>
        </Modal>
      )}
    </>
  );
}
