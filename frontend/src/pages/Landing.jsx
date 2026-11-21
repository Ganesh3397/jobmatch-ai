import {
  BriefcaseBusiness, FileSearch, KanbanSquare, Map, Mic, Radar, Smartphone, Sparkles, Target, Wand2, Gauge, Layers,
} from "lucide-react";
import { Link } from "react-router-dom";
import ThemeToggle from "../components/ThemeToggle";

const STEPS = [
  ["Upload your resume", "PDF or Word. We read your contact details, skills, education and experience."],
  ["Get your ATS score", "A score out of 100 with clear tips, plus a separate score for the role you want."],
  ["See jobs that fit you", "Live openings from five job boards, ranked by how well you match each one."],
  ["Practise and apply", "Rehearse the interview with AI, write a cover letter, then apply on the company's page."],
];

const GROUPS = [
  ["Improve your resume", [
    [Gauge, "ATS score and tips", "Know exactly what is costing you points and how to fix it."],
    [Layers, "Score for each role", "The same CV scores differently for Full Stack, Support or Data roles. See all of them."],
    [Wand2, "AI resume writer", "Turn weak bullet points into strong ones and get a cover letter for any job."],
  ]],
  ["Find the right job", [
    [Radar, "Live jobs for you", "Real openings, with the skills you have and the ones you are missing."],
    [Target, "Job description matcher", "Paste a job post from LinkedIn or Naukri and see how well you fit."],
    [KanbanSquare, "Job tracker", "Keep track of every job from saved to offer."],
  ]],
  ["Get interview-ready", [
    [Mic, "AI mock interview", "Answer HR and technical questions and get a score and feedback on each answer."],
    [Map, "Skill roadmap", "A week-by-week plan with free courses for the skills you are missing."],
    [Smartphone, "Works as a phone app", "Install it from Chrome and use it like any other app."],
  ]],
];

export function ResumeSheet({ compact = false }) {
  return (
    <div className={`sheet ${compact ? "sheet-compact" : ""}`} aria-hidden="true">
      <div className="sheet-paper">
        <div className="sheet-head">
          <div>
            <b>Ganesh Sawant</b>
            <span>MCA, Python Developer, Pune</span>
          </div>
          <div className="sheet-stamp"><b>91</b><span>ATS</span></div>
        </div>
        <div className="sheet-lines"><i style={{ width: "92%" }} /><i style={{ width: "78%" }} /><i style={{ width: "85%" }} /></div>
        <div className="sheet-label">Skills found</div>
        <div className="sheet-skills">
          {["Python", "Django", "React", "PostgreSQL", "REST APIs"].map((s) => <mark key={s}>{s}</mark>)}
          <span className="missing">Docker</span>
        </div>
        {!compact && <>
          <div className="sheet-label">Experience</div>
          <div className="sheet-lines"><i style={{ width: "88%" }} /><i style={{ width: "70%" }} /><i style={{ width: "80%" }} /><i style={{ width: "55%" }} /></div>
        </>}
      </div>
      <div className="sheet-match">
        <div className="sheet-match-logo">T</div>
        <div><b>Python Developer</b><span>TechNova Solutions, Pune</span></div>
        <em>92% match</em>
      </div>
    </div>
  );
}

export default function Landing() {
  return (
    <div className="landing">
      <header className="land-nav">
        <Link to="/" className="brand"><span className="logo-mark"><Sparkles size={17} /></span>JobMatch AI</Link>
        <nav className="row">
          <ThemeToggle inline className="land-theme" />
          <Link className="btn btn-ghost" to="/login">Login</Link>
          <Link className="btn btn-primary" to="/register">Register</Link>
        </nav>
      </header>

      <section className="hero">
        <div className="hero-copy">
          <h1>See your resume the way a recruiter's software does.</h1>
          <p>Upload your CV and get an ATS score, the skills recruiters are searching for, and live job openings that fit you.
            It takes less than a minute.</p>
          <div className="row hero-cta">
                       <Link className="btn btn-primary btn-lg" to="/register"><FileSearch />Register</Link>
            <Link className="btn btn-ghost btn-lg" to="/login">Login</Link>
          </div>
        </div>
        <ResumeSheet />
      </section>

      <section className="land-section">
        <h2>From CV to interview in four steps</h2>
        <ol className="steps">
          {STEPS.map(([t, d], i) => (
            <li key={t}><span className="step-n">{i + 1}</span><h3>{t}</h3><p>{d}</p></li>
          ))}
        </ol>
      </section>

      <section className="land-alt"><div className="land-section">
        <h2>Everything you need for your job search</h2>
        <div className="groups">
          {GROUPS.map(([title, items]) => (
            <div key={title} className="group">
              <h3>{title}</h3>
              {items.map(([Icon, t, d]) => (
                <div className="g-item" key={t}>
                  <Icon />
                  <div><b>{t}</b><p>{d}</p></div>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div></section>

      <section className="land-cta">
        <h2>Your next interview starts with a better resume.</h2>
        <div className="row"><Link className="btn btn-hl btn-lg" to="/register"><BriefcaseBusiness />Register</Link>
          <Link className="btn btn-ghost btn-lg land-cta-login" to="/login">Login</Link></div>
      </section>

      <footer className="land-foot">
        <span>Built by <b>Ganesh Sawant</b> as an MCA project</span>
        <span>Python, Django, React, PostgreSQL and machine learning</span>
      </footer>
    </div>
  );
}
