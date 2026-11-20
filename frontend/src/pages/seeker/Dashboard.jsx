import { Award, Briefcase, CalendarCheck, FileText, Radar, TrendingUp, Upload } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Bar as RBar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import api from "../../api";
import { useAuth } from "../../auth";
import { Empty, Loader, ScoreRing, Stat } from "../../components/ui";

export default function SeekerDashboard() {
  const { user } = useAuth();
  const [d, setD] = useState(null);
  useEffect(() => { api.get("/analytics/seeker/").then((r) => setD(r.data)); }, []);
  if (!d) return <Loader />;

  const p = d.primary_resume;
  const cats = p ? Object.entries(p.skills_by_category).map(([k, v]) => ({ name: k, count: v })) : [];

  return (
    <>
      <div className="banner">
        <h2>Hi {user.first_name || user.username} 👋</h2>
        <p>{p ? `Your resume scores ${p.ats_score}/100. Best fit role: ${p.predicted_roles?.[0]?.role || "—"}.`
          : "Upload your resume to get your ATS score and live job matches."}</p>
        <div className="row" style={{ marginTop: 16 }}>
          <Link to={p ? "/jobs" : "/resume"} className="btn btn-primary">{p ? <><Radar /> See live jobs for me</> : <><Upload /> Upload resume</>}</Link>
          {p && <Link to="/resume" className="btn btn-ghost">View resume analysis</Link>}
        </div>
      </div>

      {!p ? (
        <div className="card mt"><Empty icon={FileText} title="No resume yet" text="Upload a PDF or DOCX resume to unlock your dashboard."
          action={<Link className="btn btn-primary" to="/resume">Upload now</Link>} /></div>
      ) : (
        <>
          <div className="grid g-4 mt">
            <Stat icon={Award} value={`${p.ats_score}/100`} label={`ATS Score • ${p.grade}`} />
            <Stat icon={TrendingUp} value={p.skills_count} label="Skills detected" color="#12b76a" bg="#e8f8f0" />
            <Stat icon={Briefcase} value={d.applications} label="Applications sent" color="#ff7a59" bg="#fff1ec" />
            <Stat icon={CalendarCheck} value={d.tracker.interview || 0} label="Interviews" color="#8b5cf6" bg="#f3edff" />
          </div>

          <div className="grid g-3 mt">
            <div className="card" style={{ textAlign: "center" }}>
              <h3>Resume Strength</h3>
              <div className="center" style={{ padding: 10 }}><ScoreRing value={p.ats_score} size={150} label={p.grade} /></div>
              <p className="muted small">Experience detected: {p.experience_years} yrs</p>
            </div>
            <div className="card">
              <h3>🎯 Best-fit job roles</h3>
              {p.predicted_roles.map((r) => (
                <div key={r.role} className="bar-row">
                  <div className="row between"><span>{r.role}</span><b>{r.fit}%</b></div>
                  <div className="bar"><div style={{ width: `${r.fit}%` }} /></div>
                  {r.missing_core_skills.length > 0 && <p className="small muted" style={{ marginTop: 4 }}>Learn: {r.missing_core_skills.join(", ")}</p>}
                </div>
              ))}
            </div>
            <div className="card">
              <h3>🔥 In-demand skills you lack</h3>
              <p className="small muted" style={{ marginBottom: 10 }}>Based on current job postings</p>
              <div className="chips">
                {d.skills_in_demand_you_lack.map((s) => <span key={s.skill} className="chip miss">{s.skill} · {s.count}</span>)}
                {!d.skills_in_demand_you_lack.length && <span className="muted">You have all top skills! 🎉</span>}
              </div>
            </div>
          </div>

          <div className="grid g-2 mt">
            <div className="card">
              <h3>Skills by category</h3>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={cats}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} angle={-15} textAnchor="end" height={50} />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <RBar dataKey="count" fill="#5b5bf7" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="card">
              <h3>ATS score history</h3>
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={d.ats_history}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Line type="monotone" dataKey="score" stroke="#ff7a59" strokeWidth={3} dot={{ r: 5 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </>
  );
}
