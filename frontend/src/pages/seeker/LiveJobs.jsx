import { ExternalLink, Info, MapPin, Radar, RefreshCw, Search, Zap } from "lucide-react";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { Link } from "react-router-dom";
import api, { errMsg } from "../../api";
import JobCard from "../../components/JobCard";
import JobModal from "../../components/JobModal";
import { Empty } from "../../components/ui";

// Search the same role on the big job portals (opens their own search page in a new tab)
function portalLinks(query, location) {
  const q = (query || "").trim();
  const l = (location || "").trim();
  const slug = (t) => t.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
  const enc = encodeURIComponent;
  return [
    { name: "Naukri", url: `https://www.naukri.com/${slug(q)}-jobs${l ? `-in-${slug(l)}` : ""}?k=${enc(q)}${l ? `&l=${enc(l)}` : ""}` },
    { name: "LinkedIn", url: `https://www.linkedin.com/jobs/search/?keywords=${enc(q)}&location=${enc(l || "India")}` },
    { name: "Indeed", url: `https://in.indeed.com/jobs?q=${enc(q)}${l ? `&l=${enc(l)}` : ""}` },
    { name: "Google Jobs", url: `https://www.google.com/search?q=${enc(`${q} jobs ${l ? `in ${l}` : "in India"}`)}&ibp=htl;jobs` },
    { name: "Company career pages", url: `https://www.google.com/search?q=${enc(`${q} jobs ${l} careers apply`)}` },
  ];
}

export default function LiveJobs() {
  const [q, setQ] = useState("");
  const [location, setLocation] = useState("");
  const [jobType, setJobType] = useState("");
  const [mode, setMode] = useState("");
  const [minScore, setMinScore] = useState(0);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [open, setOpen] = useState(null);

  const load = async (refresh = false, query = q) => {
    setLoading(true); setError("");
    try {
      const params = { q: query, location, job_type: jobType, work_mode: mode, min_score: minScore };
      if (refresh) params.refresh = 1;
      const r = await api.get("/jobs/live/", { params });
      setData(r.data);
    } catch (e) { setError(errMsg(e)); } finally { setLoading(false); }
  };
  useEffect(() => { load(); }, [jobType, mode, minScore]);

  const save = async (item) => {
    try {
      await api.post("/jobs/saved/", { job_id: item.job.id, status: "saved", match_score: item.match.score });
      item.job.saved_status = "saved";
      setData({ ...data });
      toast.success("Saved to your Job Tracker");
    } catch (e) { toast.error(errMsg(e)); }
  };

  const meta = data?.meta;
  const liveCount = meta ? Object.values(meta.per_source || {}).reduce((a, b) => a + b, 0) : 0;
  const liveOk = meta?.live_enabled && liveCount > 0;

  return (
    <>
      <div className="page-head">
        <div><h1>Live Jobs For You</h1><p>Real-time openings matched to your resume by AI</p></div>
        <button className="btn btn-ghost" onClick={() => load(true)} disabled={loading}><RefreshCw /> Refresh live feed</button>
      </div>

      {error ? (
        <div className="card"><Empty icon={Radar} title="Upload your resume first" text={error}
          action={<Link className="btn btn-primary" to="/resume">Upload resume</Link>} /></div>
      ) : (
        <>
          <form className="card search-bar" onSubmit={(e) => { e.preventDefault(); load(); }}>
            <div className="search-input"><Search /><input className="input" placeholder={`Role or skill (default: ${meta?.query || "your best-fit role"})`} value={q} onChange={(e) => setQ(e.target.value)} /></div>
            <div className="search-input" style={{ maxWidth: 220 }}><MapPin /><input className="input" placeholder="City (e.g. Pune)" value={location} onChange={(e) => setLocation(e.target.value)} /></div>
            <select className="select" style={{ width: 150 }} value={jobType} onChange={(e) => setJobType(e.target.value)}>
              <option value="">All types</option><option value="full_time">Full Time</option><option value="internship">Internship</option>
              <option value="part_time">Part Time</option><option value="contract">Contract</option>
            </select>
            <select className="select" style={{ width: 140 }} value={mode} onChange={(e) => setMode(e.target.value)}>
              <option value="">Any mode</option><option value="remote">Remote</option><option value="hybrid">Hybrid</option><option value="onsite">On-site</option>
            </select>
            <select className="select" style={{ width: 150 }} value={minScore} onChange={(e) => setMinScore(e.target.value)}>
              <option value={0}>Any match</option><option value={40}>40%+ match</option><option value={60}>60%+ match</option><option value={75}>75%+ match</option>
            </select>
            <button className="btn btn-primary"><Search />Search</button>
          </form>

          {meta && (
            <div className="row mt" style={{ gap: 8 }}>
              <span className="small muted">Suggested for you:</span>
              {meta.suggested_queries.map((s) => (
                <button key={s} className="chip brand" style={{ cursor: "pointer", border: 0 }} onClick={() => { setQ(s); load(false, s); }}>{s}</button>
              ))}
            </div>
          )}

          {meta && (
            <div className={`info-strip mt ${liveOk ? "ok" : ""}`}>
              {liveOk ? <Zap /> : <Info />}
              <span>
              {liveOk
                ? <>Real-time jobs from <b>{Object.entries(meta.per_source || {}).map(([k, v]) => `${k} (${v})`).join(", ")}</b>{meta.cached ? " • served from cache" : " • just fetched"} • AI engine: {meta.engine}</>
                : meta.live_enabled
                  ? <>No live jobs found right now{meta.errors?.length ? " (job sites could not be reached)" : ""} — showing platform & demo jobs. Try another role or click <b>Refresh live feed</b>.</>
                  : <>Live job APIs are turned off — showing platform & demo jobs. Set <b>FREE_JOB_APIS=True</b> in backend <code>.env</code>.</>}
              {meta.errors?.length > 0 && <div className="small" style={{ marginTop: 4, opacity: .85 }}>Details: {meta.errors.join(" | ")}</div>}
              </span>
            </div>
          )}

          <div className="row between mt">
            <b>{loading ? "Finding the best jobs for you…" : `${meta?.total_found ?? 0} jobs found for "${meta?.query}"`}</b>
          </div>

          {meta?.query && (
            <div className="card portal-strip mt">
              <span className="small"><b>More "{meta.query}" jobs</b> on other job sites:</span>
              <div className="row" style={{ gap: 8 }}>
                {portalLinks(meta.query, meta.location || location).map((p) => (
                  <a key={p.name} className="btn btn-ghost btn-sm" href={p.url} target="_blank" rel="noopener noreferrer">
                    {p.name} <ExternalLink size={14} />
                  </a>
                ))}
              </div>
            </div>
          )}

          <div className="grid mt" style={{ gap: 12 }}>
            {loading && [1, 2, 3, 4].map((i) => <div key={i} className="skeleton" style={{ height: 130 }} />)}
            {!loading && data?.results.length === 0 && (
              <div className="card"><Empty icon={Search} title="No jobs found" text="Try another role, remove filters or clear the city." /></div>
            )}
            {!loading && data?.results.map((item) => (
              <JobCard key={item.job.id} job={item.job} match={item.match}
                onOpen={() => setOpen(item)} onSave={() => save(item)} />
            ))}
          </div>
        </>
      )}

      {open && <JobModal job={open.job} match={open.match} onClose={() => setOpen(null)} onApplied={() => load()} />}
    </>
  );
}
