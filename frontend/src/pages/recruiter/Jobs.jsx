import { Briefcase, Edit3, PlusCircle, Power, Trash2, Users } from "lucide-react";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { Link } from "react-router-dom";
import api, { fmtSalary } from "../../api";
import { Chips, Empty, Loader } from "../../components/ui";

export default function RecruiterJobs() {
  const [jobs, setJobs] = useState(null);
  const load = () => api.get("/jobs/mine/").then((r) => setJobs(r.data));
  useEffect(() => { load(); }, []);

  const toggle = async (j) => { await api.patch(`/jobs/${j.id}/`, { is_active: !j.is_active }); toast.success(j.is_active ? "Job closed" : "Job re-opened"); load(); };
  const del = async (j) => { if (!window.confirm(`Delete "${j.title}"?`)) return; await api.delete(`/jobs/${j.id}/`); toast.success("Deleted"); load(); };

  if (!jobs) return <Loader />;
  return (
    <>
      <div className="page-head">
        <div><h1>My Job Posts</h1><p>Manage your openings and review AI-ranked applicants</p></div>
        <Link to="/recruiter/jobs/new" className="btn btn-primary"><PlusCircle />Post a job</Link>
      </div>
      {jobs.length === 0 ? (
        <div className="card"><Empty icon={Briefcase} title="No jobs posted yet" action={<Link to="/recruiter/jobs/new" className="btn btn-primary">Post your first job</Link>} /></div>
      ) : (
        <div className="grid" style={{ gap: 12 }}>
          {jobs.map((j) => (
            <div key={j.id} className="card">
              <div className="row between" style={{ alignItems: "flex-start" }}>
                <div style={{ flex: 1, minWidth: 260 }}>
                  <div className="row"><h3 style={{ margin: 0 }}>{j.title}</h3>
                    <span className={`badge ${j.is_active ? "b-green" : "b-gray"}`}>{j.is_active ? "Active" : "Closed"}</span></div>
                  <p className="muted" style={{ margin: "6px 0 10px" }}>
                    {j.location} • {j.job_type_label} • {j.work_mode_label} • {j.min_experience}+ yrs {fmtSalary(j.salary_min, j.salary_max) && `• ${fmtSalary(j.salary_min, j.salary_max)}`}
                  </p>
                  <Chips items={j.skills} max={8} />
                </div>
                <div className="row" style={{ gap: 6 }}>
                  <Link to={`/recruiter/jobs/${j.id}/applicants`} className="btn btn-primary btn-sm"><Users />{j.applications_count} applicants</Link>
                  <Link to={`/recruiter/jobs/${j.id}/edit`} className="btn btn-ghost btn-sm"><Edit3 /></Link>
                  <button className="btn btn-ghost btn-sm" title={j.is_active ? "Close job" : "Re-open"} onClick={() => toggle(j)}><Power /></button>
                  <button className="btn btn-danger btn-sm" onClick={() => del(j)}><Trash2 /></button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
