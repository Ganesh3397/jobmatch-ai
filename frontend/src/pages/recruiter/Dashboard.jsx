import { Award, Briefcase, PlusCircle, UserCheck, Users } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis, Legend } from "recharts";
import api from "../../api";
import { useAuth } from "../../auth";
import { Loader, MatchBadge, Stat, StatusBadge } from "../../components/ui";

const PIE = ["#5b5bf7", "#12b76a", "#f5a524", "#f04438", "#8b5cf6"];

export default function RecruiterDashboard() {
  const { user } = useAuth();
  const [d, setD] = useState(null);
  useEffect(() => { api.get("/analytics/recruiter/").then((r) => setD(r.data)); }, []);
  if (!d) return <Loader />;
  const pie = Object.entries(d.status_breakdown).map(([name, value]) => ({ name, value })).filter((x) => x.value);

  return (
    <>
      <div className="banner">
        <h2>Welcome, {user.first_name || user.username} 👋</h2>
        <p>{user.company_name} • Candidates are automatically ranked by AI match score.</p>
        <div className="row" style={{ marginTop: 16 }}><Link to="/recruiter/jobs/new" className="btn btn-primary"><PlusCircle />Post a new job</Link></div>
      </div>
      <div className="grid g-4 mt">
        <Stat icon={Briefcase} value={d.total_jobs} label={`Jobs posted • ${d.active_jobs} active`} />
        <Stat icon={Users} value={d.total_applicants} label="Total applicants" color="#ff7a59" bg="#fff1ec" />
        <Stat icon={Award} value={`${d.avg_match_score}%`} label="Avg. AI match" color="#12b76a" bg="#e8f8f0" />
        <Stat icon={UserCheck} value={(d.status_breakdown.shortlisted || 0) + (d.status_breakdown.interview || 0)} label="Shortlisted / Interview" color="#8b5cf6" bg="#f3edff" />
      </div>
      <div className="grid g-2 mt">
        <div className="card">
          <h3>Applicants per job</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={d.per_job}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="title" tick={{ fontSize: 11 }} interval={0} tickFormatter={(t) => (t.length > 16 ? t.slice(0, 16) + "…" : t)} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar isAnimationActive={false} dataKey="applicants" fill="#5b5bf7" radius={[6, 6, 0, 0]} />
              <Bar isAnimationActive={false} dataKey="avg_match" name="Avg match %" fill="#ff7a59" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <h3>Hiring pipeline</h3>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={pie} dataKey="value" nameKey="name" innerRadius={60} outerRadius={95} paddingAngle={3}>
                {pie.map((_, i) => <Cell key={i} fill={PIE[i % PIE.length]} />)}
              </Pie>
              <Tooltip /><Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="card mt">
        <h3>🏆 Top candidates</h3>
        <div className="table-wrap"><table>
          <thead><tr><th>Candidate</th><th>Job</th><th>AI match</th><th>Status</th></tr></thead>
          <tbody>{d.top_candidates.map((c, i) => (
            <tr key={i}><td><b>{c.name}</b></td><td className="muted">{c.job}</td><td><MatchBadge score={c.score} /></td><td><StatusBadge s={c.status} /></td></tr>
          ))}</tbody>
        </table></div>
      </div>
    </>
  );
}
