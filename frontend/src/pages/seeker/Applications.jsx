import { ClipboardList } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../../api";
import { Chips, Empty, Loader, MatchBadge, StatusBadge } from "../../components/ui";

export default function Applications() {
  const [apps, setApps] = useState(null);
  useEffect(() => { api.get("/jobs/applications/mine/").then((r) => setApps(r.data)); }, []);
  if (!apps) return <Loader />;

  return (
    <>
      <div className="page-head"><div><h1>My Applications</h1><p>Jobs you applied to directly on JobMatch AI</p></div></div>
      <div className="card">
        {apps.length === 0 ? (
          <Empty icon={ClipboardList} title="No applications yet" text="Look for jobs with the 'Easy Apply' badge on the Live Jobs page."
            action={<Link to="/jobs" className="btn btn-primary">Find jobs</Link>} />
        ) : (
          <div className="table-wrap"><table>
            <thead><tr><th>Job</th><th>Company</th><th>Matched skills</th><th>AI match</th><th>Status</th><th>Applied on</th></tr></thead>
            <tbody>{apps.map((a) => (
              <tr key={a.id}>
                <td><b>{a.job.title}</b></td>
                <td className="muted">{a.job.company}</td>
                <td><Chips items={a.match_result.matched_skills || []} kind="ok" max={4} /></td>
                <td><MatchBadge score={a.match_score} /></td>
                <td><StatusBadge s={a.status} /></td>
                <td className="muted">{new Date(a.created_at).toLocaleDateString()}</td>
              </tr>
            ))}</tbody>
          </table></div>
        )}
      </div>
    </>
  );
}
