import { ExternalLink, KanbanSquare, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { Link } from "react-router-dom";
import api from "../../api";
import { Empty, Loader, MatchBadge } from "../../components/ui";

const COLS = [
  ["saved", "🔖 Saved", "#6b7190"], ["applied", "📨 Applied", "#5b5bf7"], ["interview", "🗓️ Interview", "#f5a524"],
  ["offer", "🎉 Offer", "#12b76a"], ["rejected", "❌ Rejected", "#f04438"],
];

export default function Tracker() {
  const [items, setItems] = useState(null);
  const [dragId, setDragId] = useState(null);
  const load = () => api.get("/jobs/saved/").then((r) => setItems(r.data));
  useEffect(() => { load(); }, []);

  const move = async (id, status) => {
    setItems(items.map((i) => (i.id === id ? { ...i, status } : i)));
    await api.patch(`/jobs/saved/${id}/`, { status });
  };
  const remove = async (id) => { await api.delete(`/jobs/saved/${id}/`); setItems(items.filter((i) => i.id !== id)); toast.success("Removed"); };

  if (!items) return <Loader />;
  return (
    <>
      <div className="page-head"><div><h1>Job Tracker</h1><p>Drag cards between columns to track your application progress</p></div></div>
      {items.length === 0 ? (
        <div className="card"><Empty icon={KanbanSquare} title="No saved jobs yet" text="Save jobs from the Live Jobs page to track them here."
          action={<Link to="/jobs" className="btn btn-primary">Browse live jobs</Link>} /></div>
      ) : (
        <div className="kanban">
          {COLS.map(([key, label, color]) => {
            const col = items.filter((i) => i.status === key);
            return (
              <div key={key} className="kcol" onDragOver={(e) => e.preventDefault()} onDrop={() => dragId && move(dragId, key)}>
                <div className="kcol-head"><span>{label}</span><span className="badge" style={{ background: "#fff", color }}>{col.length}</span></div>
                {col.map((i) => (
                  <div key={i.id} className="kcard" draggable onDragStart={() => setDragId(i.id)} onDragEnd={() => setDragId(null)} style={{ cursor: "grab" }}>
                    <h5>{i.job.title}</h5>
                    <p className="small muted">{i.job.company} • {i.job.location}</p>
                    <div className="row between" style={{ marginTop: 10 }}>
                      {i.match_score ? <MatchBadge score={i.match_score} /> : <span />}
                      <div className="row" style={{ gap: 4 }}>
                        {i.job.apply_url && <a className="icon-btn" style={{ color: "#5b5bf7" }} href={i.job.apply_url} target="_blank" rel="noreferrer"><ExternalLink size={15} /></a>}
                        <button className="icon-btn" style={{ color: "#f04438" }} onClick={() => remove(i.id)}><Trash2 size={15} /></button>
                      </div>
                    </div>
                    <select className="select" style={{ marginTop: 8, padding: "6px 8px", fontSize: 12.5 }} value={i.status} onChange={(e) => move(i.id, e.target.value)}>
                      {COLS.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
                    </select>
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      )}
    </>
  );
}
