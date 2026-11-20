import { Inbox } from "lucide-react";

export function ScoreRing({ value = 0, size = 120, stroke = 10, label = "Score" }) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const v = Math.max(0, Math.min(100, value));
  const color = v >= 75 ? "#12b76a" : v >= 50 ? "#5b5bf7" : v >= 35 ? "#f5a524" : "#f04438";
  return (
    <div className="ring" style={{ width: size, height: size }}>
      <svg width={size} height={size}>
        <circle cx={size / 2} cy={size / 2} r={r} stroke="#eef0f6" strokeWidth={stroke} fill="none" />
        <circle cx={size / 2} cy={size / 2} r={r} stroke={color} strokeWidth={stroke} fill="none"
          strokeLinecap="round" strokeDasharray={c} strokeDashoffset={c - (v / 100) * c}
          style={{ transition: "stroke-dashoffset .8s ease" }} />
      </svg>
      <div className="ring-text">
        <b style={{ fontSize: size * 0.26 }}>{Math.round(v)}</b>
        <span>{label}</span>
      </div>
    </div>
  );
}

export function MatchBadge({ score }) {
  const cls = score >= 75 ? "b-green" : score >= 55 ? "b-brand" : score >= 35 ? "b-amber" : "b-red";
  return <span className={`badge ${cls}`}>{Math.round(score)}% match</span>;
}

export function Chips({ items = [], kind = "", max = 99 }) {
  if (!items.length) return <span className="muted small">—</span>;
  const extra = items.length - max;
  return (
    <div className="chips">
      {items.slice(0, max).map((s) => <span key={s} className={`chip ${kind}`}>{s}</span>)}
      {extra > 0 && <span className="chip">+{extra}</span>}
    </div>
  );
}

export function Stat({ icon: Icon, value, label, color = "#5b5bf7", bg = "#eef0ff" }) {
  return (
    <div className="card stat">
      <div className="stat-icon" style={{ background: bg, color }}><Icon /></div>
      <div><b>{value}</b><span>{label}</span></div>
    </div>
  );
}

export function Empty({ icon: Icon = Inbox, title, text, action }) {
  return (
    <div className="empty">
      <Icon />
      <h4>{title}</h4>
      {text && <p>{text}</p>}
      {action && <div style={{ marginTop: 16 }}>{action}</div>}
    </div>
  );
}

export const Loader = () => <div className="center"><div className="spinner" /></div>;

export function Bar({ label, value, max = 100, right }) {
  return (
    <div className="bar-row">
      <div className="row between"><span>{label}</span><b>{right ?? `${value}/${max}`}</b></div>
      <div className="bar"><div style={{ width: `${(value / max) * 100}%` }} /></div>
    </div>
  );
}

const COLORS = ["#5b5bf7", "#ff7a59", "#12b76a", "#8b5cf6", "#f5a524", "#0ea5e9", "#ec4899", "#14b8a6"];
export function CompanyLogo({ name = "?" }) {
  const i = [...name].reduce((a, c) => a + c.charCodeAt(0), 0) % COLORS.length;
  return <div className="company-logo" style={{ background: COLORS[i] }}>{name.trim()[0]?.toUpperCase() || "?"}</div>;
}

export function Modal({ onClose, children }) {
  return (
    <div className="modal-back" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">{children}</div>
    </div>
  );
}

export const STATUS_BADGE = {
  saved: "b-gray", applied: "b-brand", interview: "b-amber", offer: "b-green", rejected: "b-red",
  shortlisted: "b-green", hired: "b-green", pending: "b-gray", processing: "b-amber", done: "b-green", failed: "b-red",
};
export const StatusBadge = ({ s }) => <span className={`badge ${STATUS_BADGE[s] || "b-gray"}`} style={{ textTransform: "capitalize" }}>{s}</span>;
