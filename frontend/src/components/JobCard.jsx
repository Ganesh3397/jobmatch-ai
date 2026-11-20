import { Bookmark, BookmarkCheck, Briefcase, Clock, ExternalLink, IndianRupee, MapPin, Wifi } from "lucide-react";
import { fmtSalary, timeAgo } from "../api";
import { Chips, CompanyLogo, MatchBadge } from "./ui";

export const LIVE = ["adzuna", "jsearch", "remotive", "jobicy", "arbeitnow"];

export default function JobCard({ job, match, onOpen, onSave }) {
  const salary = fmtSalary(job.salary_min, job.salary_max);
  return (
    <div className="card job-card" onClick={onOpen}>
      <CompanyLogo name={job.company || job.title} />
      <div className="job-body">
        <div className="row" style={{ gap: 8 }}>
          <h4>{job.title}</h4>
          {job.source === "internal" && <span className="badge b-green">Easy Apply</span>}
          {LIVE.includes(job.source) && <span className="badge b-brand">● Live · via {job.source_label}</span>}
          {job.source === "demo" && <span className="badge b-gray">Demo</span>}
          {job.applied && <span className="badge b-gray">Applied</span>}
        </div>
        <div className="job-meta">
          <span><Briefcase />{job.company || "—"}</span>
          <span><MapPin />{job.location || "India"}</span>
          {job.work_mode === "remote" && <span><Wifi />Remote</span>}
          {salary && <span><IndianRupee />{salary.replace("₹", "")}</span>}
          <span><Clock />{timeAgo(job.posted_at || job.created_at)}</span>
          <span className="badge b-gray">{job.job_type_label}</span>
        </div>
        {match ? (
          <div className="grid g-2" style={{ gap: 10 }}>
            <div><div className="small muted" style={{ marginBottom: 5 }}>✅ You have</div><Chips items={match.matched_skills} kind="ok" max={6} /></div>
            <div><div className="small muted" style={{ marginBottom: 5 }}>⚠️ Skill gap</div><Chips items={match.missing_skills} kind="miss" max={5} /></div>
          </div>
        ) : (
          <Chips items={job.skills || []} max={8} />
        )}
      </div>
      <div className="job-side" onClick={(e) => e.stopPropagation()}>
        {match && <MatchBadge score={match.score} />}
        <div className="row" style={{ gap: 6 }}>
          {onSave && (
            <button className="btn btn-ghost btn-sm" onClick={onSave} title="Save to tracker">
              {job.saved_status ? <BookmarkCheck color="#5b5bf7" /> : <Bookmark />}
            </button>
          )}
          {job.apply_url && LIVE.includes(job.source) && (
            <a className="btn btn-soft btn-sm" href={job.apply_url} target="_blank" rel="noreferrer">Apply <ExternalLink /></a>
          )}
          {job.source === "internal" && !job.applied && <button className="btn btn-success btn-sm" onClick={onOpen}>Easy Apply</button>}
        </div>
      </div>
    </div>
  );
}
