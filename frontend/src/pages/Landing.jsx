import { BellRing, Brain, FileSearch, Radar, Sparkles, Target, Users, Zap } from "lucide-react";
import { Link } from "react-router-dom";
import { CompanyLogo } from "../components/ui";

const FEATURES = [
  [FileSearch, "AI Resume Parsing", "Upload a PDF/DOCX. NLP extracts your name, contact, skills, education and experience automatically.", "#5b5bf7", "#eef0ff"],
  [Target, "ATS Score & Tips", "Get a 0-100 ATS score with a detailed breakdown and personalised tips to improve your resume.", "#ff7a59", "#fff1ec"],
  [Radar, "Real-Time Jobs", "Live jobs pulled from Adzuna & JSearch (LinkedIn, Indeed, Glassdoor) for your profile, refreshed automatically.", "#12b76a", "#e8f8f0"],
  [Brain, "Smart Match %", "Hybrid AI matcher: skill overlap + semantic similarity (TF-IDF / BERT) + experience fit.", "#8b5cf6", "#f3edff"],
  [Zap, "Skill Gap Analysis", "See exactly which skills you are missing for each job, with links to learn them.", "#f5a524", "#fff6e5"],
  [Users, "Recruiter Panel", "Recruiters post jobs and see applicants automatically ranked by AI match score.", "#0ea5e9", "#e6f6fe"],
  [BellRing, "Job Alerts", "Daily email alerts with new jobs that match your resume (Celery + Redis background jobs).", "#ec4899", "#fdeaf4"],
  [Sparkles, "Analytics", "Dashboards for seekers, recruiters and admins — skill demand, ATS trends and more.", "#14b8a6", "#e6f7f5"],
];

export default function Landing() {
  return (
    <div className="landing">
      <div className="land-nav">
        <div className="logo" style={{ padding: 0 }}>
          <div className="logo-mark"><Sparkles size={18} /></div>JobMatch AI
        </div>
        <div className="row">
          <Link className="btn btn-ghost" to="/login">Login</Link>
          <Link className="btn btn-primary" to="/register">Get Started</Link>
        </div>
      </div>

      <section className="hero">
        <div>
          <div className="pill"><Sparkles size={14} /> AI-Powered • Real-Time • Free</div>
          <h1>Upload your resume.<br /><em>Get matched to live jobs</em><br />in seconds.</h1>
          <p>JobMatch AI reads your resume like a recruiter, scores it like an ATS, finds jobs that are open right now,
            and tells you exactly which skills you need to land them.</p>
          <div className="row">
            <Link className="btn btn-primary" to="/register" style={{ padding: "13px 22px" }}>Analyze my resume — free</Link>
            <Link className="btn btn-ghost" to="/login" style={{ padding: "13px 22px" }}>Login</Link>
          </div>
        </div>
        <div className="hero-card">
          <div className="row between">
            <div><b style={{ fontSize: 15 }}>Rahul Patil</b><p style={{ color: "#a9abd0", fontSize: 13 }}>Python Developer • ATS 91/100</p></div>
            <span className="badge b-green">Excellent</span>
          </div>
          {[["Python Developer", "TechNova Solutions", 92], ["Full Stack (React + Django)", "CloudNine Labs", 84], ["Backend Engineer", "Quantum Leap IT", 71]].map(([t, c, s]) => (
            <div className="hero-job" key={t}>
              <CompanyLogo name={c} />
              <div style={{ flex: 1 }}><b style={{ fontSize: 14 }}>{t}</b><p style={{ color: "#a9abd0", fontSize: 12.5 }}>{c} • Pune</p></div>
              <span className="badge" style={{ background: "rgba(18,183,106,.18)", color: "#6ce9a6" }}>{s}%</span>
            </div>
          ))}
        </div>
      </section>

      <section className="features">
        <h2>Everything you need to get hired</h2>
        <p className="muted" style={{ textAlign: "center", marginTop: 8 }}>Built with Python • Django • React • PostgreSQL • Redis • Celery • Machine Learning</p>
        <div className="grid g-4" style={{ marginTop: 36 }}>
          {FEATURES.map(([Icon, t, d, c, bg]) => (
            <div className="card feature" key={t}>
              <div className="stat-icon" style={{ background: bg, color: c }}><Icon /></div>
              <h4>{t}</h4><p>{d}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
