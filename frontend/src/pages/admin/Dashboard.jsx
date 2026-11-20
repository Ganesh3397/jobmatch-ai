import { Briefcase, FileCheck2, Gauge, Users } from "lucide-react";
import { useEffect, useState } from "react";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import api from "../../api";
import { Loader, Stat } from "../../components/ui";

const C = ["#5b5bf7", "#ff7a59", "#12b76a", "#8b5cf6", "#f5a524"];

export default function AdminDashboard() {
  const [d, setD] = useState(null);
  useEffect(() => { api.get("/analytics/admin/").then((r) => setD(r.data)); }, []);
  if (!d) return <Loader />;

  const roles = Object.entries(d.users).map(([name, value]) => ({ name, value }));
  const sources = Object.entries(d.jobs_by_source).map(([name, value]) => ({ name, value })).filter((x) => x.value);
  const skills = d.skill_demand.map((s) => ({ skill: s.skill, demand: s.count, supply: d.skill_supply.find((x) => x.skill === s.skill)?.count || 0 }));

  return (
    <>
      <div className="page-head"><div><h1>Platform Analytics</h1><p>Overview of users, resumes, jobs and skill trends</p></div></div>
      <div className="grid g-4">
        <Stat icon={Users} value={d.total_users} label={`Users • ${d.users.seeker} seekers`} />
        <Stat icon={FileCheck2} value={d.resumes_processed} label={`Resumes analysed • ${d.resumes_failed} failed`} color="#12b76a" bg="#e8f8f0" />
        <Stat icon={Gauge} value={d.avg_ats_score} label="Average ATS score" color="#ff7a59" bg="#fff1ec" />
        <Stat icon={Briefcase} value={d.total_jobs} label="Jobs in database" color="#8b5cf6" bg="#f3edff" />
      </div>

      <div className="grid g-2 mt">
        <div className="card">
          <h3>New signups (14 days)</h3>
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={d.signups_14_days}>
              <defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#5b5bf7" stopOpacity={.35} /><stop offset="100%" stopColor="#5b5bf7" stopOpacity={0} /></linearGradient></defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={(t) => t.slice(5)} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Area isAnimationActive={false} type="monotone" dataKey="count" stroke="#5b5bf7" strokeWidth={2.5} fill="url(#g)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        <div className="grid g-2" style={{ gap: 18 }}>
          <div className="card">
            <h3>Users by role</h3>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart><Pie data={roles} dataKey="value" nameKey="name" innerRadius={45} outerRadius={75}>
                {roles.map((_, i) => <Cell key={i} fill={C[i]} />)}</Pie><Tooltip /><Legend /></PieChart>
            </ResponsiveContainer>
          </div>
          <div className="card">
            <h3>Jobs by source</h3>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart><Pie data={sources} dataKey="value" nameKey="name" innerRadius={45} outerRadius={75}>
                {sources.map((_, i) => <Cell key={i} fill={C[(i + 1) % C.length]} />)}</Pie><Tooltip /><Legend /></PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid g-side mt">
        <div className="card">
          <h3>Skill demand (jobs) vs supply (candidates)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={skills}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="skill" tick={{ fontSize: 11 }} interval={0} angle={-25} textAnchor="end" height={60} />
              <YAxis allowDecimals={false} />
              <Tooltip /><Legend />
              <Bar isAnimationActive={false} dataKey="demand" name="Jobs requiring" fill="#5b5bf7" radius={[5, 5, 0, 0]} />
              <Bar isAnimationActive={false} dataKey="supply" name="Candidates having" fill="#ff7a59" radius={[5, 5, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <h3>ATS score distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={d.ats_distribution} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" allowDecimals={false} /><YAxis type="category" dataKey="range" width={60} />
              <Tooltip />
              <Bar isAnimationActive={false} dataKey="count" fill="#12b76a" radius={[0, 6, 6, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </>
  );
}
