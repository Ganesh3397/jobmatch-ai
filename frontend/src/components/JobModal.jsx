import { BookOpen, ExternalLink, Send, X } from "lucide-react";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import api, { errMsg, fmtSalary } from "../api";
import { Bar, Chips, CompanyLogo, Modal, ScoreRing } from "./ui";

const learn = (skill) => `https://www.youtube.com/results?search_query=learn+${encodeURIComponent(skill)}+full+course`;

export default function JobModal({ job: initial, match, onClose, onApplied }) {
  const [job, setJob] = useState(initial);
  const [applying, setApplying] = useState(false);
  // list endpoints send a short description -> load the full job
  useEffect(() => {
    if (!initial.description) {
      api.get(`/jobs/${initial.id}/`).then((r) => setJob({ ...initial, ...r.data })).catch(() => {});
    }
  }, [initial.id]);
  const [note, setNote] = useState("");
  const salary = fmtSalary(job.salary_min, job.salary_max);

  const apply = async () => {
    setApplying(true);
    try {
      await api.post(`/jobs/${job.id}/apply/`, { cover_note: note });
      toast.success("Applied successfully! 🎉");
      onApplied?.();
      onClose();
    } catch (e) { toast.error(errMsg(e)); } finally { setApplying(false); }
  };

  return (
    <Modal onClose={onClose}>
      <div className="modal-head">
        <div className="row" style={{ gap: 14, alignItems: "flex-start" }}>
          <CompanyLogo name={job.company || job.title} />
          <div>
            <h2 style={{ fontSize: 21 }}>{job.title}</h2>
            <p className="muted">{job.company} • {job.location} • {job.job_type_label} • {job.work_mode_label}</p>
            {salary && <p style={{ marginTop: 4, fontWeight: 700 }}>{salary} / year</p>}
          </div>
        </div>
        <button className="btn btn-ghost btn-sm" onClick={onClose}><X /></button>
      </div>
      <div className="modal-body">
        {match && (
          <div className="card" style={{ background: "#fafbff", marginBottom: 18 }}>
            <div className="row" style={{ gap: 24, alignItems: "center" }}>
              <ScoreRing value={match.score} size={110} label={match.label?.split(" ")[0] || "Match"} />
              <div style={{ flex: 1, minWidth: 220 }}>
                <Bar label="Skill match (60%)" value={match.skill_score} right={`${match.skill_score}%`} />
                <Bar label="Content similarity – AI (30%)" value={match.semantic_score} right={`${match.semantic_score}%`} />
                <Bar label="Experience fit (10%)" value={match.experience_score} right={`${match.experience_score}%`} />
              </div>
            </div>
            <div className="grid g-2 mt">
              <div><div className="small muted" style={{ marginBottom: 6 }}>✅ Matched skills</div><Chips items={match.matched_skills} kind="ok" /></div>
              <div><div className="small muted" style={{ marginBottom: 6 }}>⚠️ Missing skills</div><Chips items={match.missing_skills} kind="miss" /></div>
            </div>
            {match.missing_skills?.length > 0 && (
              <div className="mt">
                <div className="small muted" style={{ marginBottom: 6 }}><BookOpen size={13} /> Learn missing skills</div>
                <div className="chips">
                  {match.missing_skills.slice(0, 5).map((s) => (
                    <a key={s} className="chip brand" href={learn(s)} target="_blank" rel="noreferrer">{s} ↗</a>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        <h4 style={{ marginBottom: 8 }}>Job description</h4>
        <div className="desc">{job.description || job.short_description}</div>

        <div className="mt">
          {job.source === "internal" ? (
            job.applied ? <span className="badge b-green">You have already applied</span> : (
              <>
                <div className="field"><label>Cover note (optional)</label>
                  <textarea className="textarea" style={{ minHeight: 80 }} value={note} onChange={(e) => setNote(e.target.value)}
                    placeholder="Why are you a good fit?" /></div>
                <button className="btn btn-primary" disabled={applying} onClick={apply}><Send />{applying ? "Applying…" : "Easy Apply with my resume"}</button>
              </>
            )
          ) : job.apply_url ? (
            <>
              <a className="btn btn-primary" href={job.apply_url} target="_blank" rel="noreferrer">Apply now — open original job post <ExternalLink /></a>
              <p className="small muted" style={{ marginTop: 8 }}>Opens the real job posting ({job.source_label}) in a new tab. Complete your application there.</p>
            </>
          ) : job.source === "demo" ? (
            <p className="small muted">This is a sample job used for demonstration. Real live jobs show an Apply button.</p>
          ) : null}
        </div>
      </div>
    </Modal>
  );
}
