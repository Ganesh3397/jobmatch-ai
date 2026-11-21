import { ArrowLeft, ArrowRight, Bot, CheckCircle2, History, Lightbulb, Mic, Play, RotateCcw, Send, Trophy } from "lucide-react";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { Link, useSearchParams } from "react-router-dom";
import api, { errMsg } from "../../api";
import { Empty, Loader, ScoreRing } from "../../components/ui";

const scoreClass = (s) => (s >= 7.5 ? "b-green" : s >= 5 ? "b-brand" : s >= 3 ? "b-amber" : "b-red");

function Feedback({ result }) {
  return (
    <div className="card mt" style={{ background: "var(--surface-2)", boxShadow: "none" }}>
      <div className="row between">
        <h3 style={{ margin: 0 }}><Bot /> AI feedback</h3>
        <span className={`badge ${scoreClass(result.score)}`} style={{ fontSize: 14 }}>{result.score}/10</span>
      </div>
      <div className="grid g-2 mt" style={{ gap: 14 }}>
        <div>
          <div className="small muted" style={{ fontWeight: 700, marginBottom: 6 }}>✅ What was good</div>
          {result.strengths.map((s) => <p key={s} className="small" style={{ marginBottom: 4 }}>• {s}</p>)}
        </div>
        <div>
          <div className="small muted" style={{ fontWeight: 700, marginBottom: 6 }}>💡 How to improve</div>
          {result.improvements.length ? result.improvements.map((s) => <p key={s} className="small" style={{ marginBottom: 4 }}>• {s}</p>)
            : <p className="small">Great answer! 🎉</p>}
        </div>
      </div>
      {result.ideal_points?.length > 0 && (
        <div className="mt"><div className="small muted" style={{ fontWeight: 700, marginBottom: 6 }}>Key points interviewers expect</div>
          <div className="chips">{result.ideal_points.map((p) => <span key={p} className="chip brand">{p}</span>)}</div></div>
      )}
      {result.model_answer && <div className="tip mt"><Lightbulb size={18} color="var(--amber)" /><div><b>Sample answer</b><p>{result.model_answer}</p></div></div>}
    </div>
  );
}

export default function Interview() {
  const [params] = useSearchParams();
  const [session, setSession] = useState(null);
  const [idx, setIdx] = useState(0);
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [history, setHistory] = useState([]);
  const [role, setRole] = useState("");
  const [roles, setRoles] = useState([]);
  const [count, setCount] = useState(6);
  const [status, setStatus] = useState(null);

  const loadHistory = () => api.get("/ai/interviews/").then((r) => setHistory(r.data));
  useEffect(() => {
    loadHistory();
    api.get("/ai/status/").then((r) => setStatus(r.data));
    api.get("/resumes/roadmap/").then((r) => { setRoles(r.data.roles); setRole(r.data.suggested_roles?.[0] || r.data.role); }).catch(() => {});
  }, []);

  const start = async (jobId) => {
    setBusy(true);
    try {
      const { data } = await api.post("/ai/interviews/", jobId ? { job_id: jobId } : { role, count });
      setSession(data); setIdx(0); setAnswer("");
    } catch (e) { toast.error(errMsg(e)); } finally { setBusy(false); }
  };
  useEffect(() => { if (params.get("job")) start(params.get("job")); }, []);

  const open = async (id) => { const { data } = await api.get(`/ai/interviews/${id}/`); setSession(data); setIdx(0); setAnswer(data.questions[0]?.answer || ""); };

  const submit = async () => {
    setBusy(true);
    try {
      const { data } = await api.post(`/ai/interviews/${session.id}/answer/`, { index: idx, answer });
      setSession(data.session);
      if (data.session.completed) loadHistory();
    } catch (e) { toast.error(errMsg(e)); } finally { setBusy(false); }
  };

  const go = (i) => { setIdx(i); setAnswer(session.questions[i]?.answer || ""); };

  // ---------------- start screen
  if (!session) {
    return (
      <>
        <div className="page-head"><div><h1>AI Mock Interview</h1><p>Practise real interview questions and get instant AI feedback on every answer</p></div></div>
        <div className="grid g-side">
          <div className="card">
            <h3><Mic /> Start a new interview</h3>
            <div className="grid g-2" style={{ gap: 12 }}>
              <div className="field"><label>Role</label>
                <select className="select" value={role} onChange={(e) => setRole(e.target.value)}>
                  {roles.map((r) => <option key={r}>{r}</option>)}
                </select></div>
              <div className="field"><label>Number of questions</label>
                <select className="select" value={count} onChange={(e) => setCount(e.target.value)}>
                  {[4, 6, 8, 10].map((n) => <option key={n} value={n}>{n} questions</option>)}
                </select></div>
            </div>
            <p className="small muted" style={{ marginBottom: 14 }}>Questions are based on your resume skills: an HR opener, technical questions and a behavioural question.
              Tip: you can also start an interview for a specific job from the job's details window.</p>
            <button className="btn btn-primary" disabled={busy || !role} onClick={() => start()}><Play />{busy ? "Preparing questions…" : "Start interview"}</button>
            {status && <p className="small muted mt">AI engine: {status.engine}</p>}
          </div>
          <div className="card" style={{ alignSelf: "start" }}>
            <h3><History /> Past interviews</h3>
            {history.length === 0 && <Empty title="No interviews yet" text="Your attempts will appear here." />}
            {history.map((h) => (
              <div key={h.id} className="row between" style={{ padding: "10px 0", borderBottom: "1px solid var(--line)", cursor: "pointer" }} onClick={() => open(h.id)}>
                <div><b style={{ fontSize: 14 }}>{h.role}</b><div className="small muted">{new Date(h.created_at).toLocaleDateString()} • {h.questions} questions</div></div>
                {h.overall_score != null ? <span className={`badge ${scoreClass(h.overall_score)}`}>{h.overall_score}/10</span> : <span className="badge b-gray">Not started</span>}
              </div>
            ))}
          </div>
        </div>
      </>
    );
  }

  const q = session.questions[idx];
  const answered = session.questions.filter((x) => x.answered).length;

  // ---------------- result screen
  if (session.completed && idx >= session.questions.length) {
    return (
      <>
        <div className="page-head"><div><h1>Interview result</h1><p>{session.role}</p></div></div>
        <div className="card" style={{ textAlign: "center" }}>
          <Trophy size={36} color="var(--amber)" />
          <div className="center" style={{ padding: 10 }}><ScoreRing value={session.overall_score * 10} size={160} label="Score" /></div>
          <h2>{session.overall_score}/10 • {session.verdict}</h2>
          <div className="row" style={{ justifyContent: "center", marginTop: 16 }}>
            <button className="btn btn-ghost" onClick={() => go(0)}><ArrowLeft />Review answers</button>
            <button className="btn btn-primary" onClick={() => { setSession(null); loadHistory(); }}><RotateCcw />New interview</button>
          </div>
        </div>
        <div className="card mt">
          <h3>Question-wise score</h3>
          {session.questions.map((x, i) => (
            <div key={i} className="bar-row" style={{ cursor: "pointer" }} onClick={() => go(i)}>
              <div className="row between"><span className="small">{i + 1}. {x.question}</span><b>{x.result?.score ?? 0}/10</b></div>
              <div className="bar"><div style={{ width: `${(x.result?.score || 0) * 10}%` }} /></div>
            </div>
          ))}
        </div>
      </>
    );
  }

  // ---------------- question screen
  return (
    <>
      <div className="page-head">
        <div><h1>{session.role}</h1><p>Question {idx + 1} of {session.questions.length} • {answered} answered</p></div>
        <button className="btn btn-ghost" onClick={() => { setSession(null); loadHistory(); }}><ArrowLeft />Exit</button>
      </div>
      <div className="bar" style={{ marginBottom: 18 }}><div style={{ width: `${(answered / session.questions.length) * 100}%` }} /></div>
      <div className="card">
        <div className="row" style={{ gap: 8, marginBottom: 10 }}>
          <span className={`badge ${q.type === "hr" ? "b-amber" : "b-brand"}`}>{q.type === "hr" ? "HR / Behavioural" : "Technical"}</span>
          {q.skill && <span className="badge b-gray">{q.skill}</span>}
        </div>
        <h2 style={{ fontSize: 20, lineHeight: 1.4 }}>{q.question}</h2>
        <textarea className="textarea mt" style={{ minHeight: 170 }} placeholder="Type your answer as you would speak it in the interview…"
          value={answer} onChange={(e) => setAnswer(e.target.value)} disabled={busy} />
        <div className="row between mt">
          <span className="small muted">{answer.trim().split(/\s+/).filter(Boolean).length} words • aim for 60-150</span>
          <div className="row">
            <button className="btn btn-ghost" disabled={idx === 0} onClick={() => go(idx - 1)}><ArrowLeft /></button>
            <button className="btn btn-primary" disabled={busy || answer.trim().length < 3} onClick={submit}>
              <Send />{busy ? "Checking…" : q.answered ? "Re-submit" : "Submit answer"}</button>
            <button className="btn btn-ghost" onClick={() => go(idx + 1)} disabled={idx + 1 >= session.questions.length && !session.completed}>
              {idx + 1 >= session.questions.length ? <><CheckCircle2 />Result</> : <ArrowRight />}</button>
          </div>
        </div>
        {q.result && <Feedback result={q.result} />}
      </div>
      {!session.completed && idx + 1 >= session.questions.length && answered < session.questions.length && (
        <p className="small muted mt">Answer all questions to see your final score. <Link to="#" onClick={(e) => { e.preventDefault(); go(session.questions.findIndex((x) => !x.answered)); }}>Go to unanswered</Link></p>
      )}
    </>
  );
}
