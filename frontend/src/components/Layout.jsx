import {
  BarChart3, Briefcase, FileText, KanbanSquare, LayoutDashboard, LogOut, Radar,
  Sparkles, Target, User, Users, ClipboardList, PlusCircle, Map, Mic, Wand2, Menu, X,
} from "lucide-react";
import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import InstallBanner from "./InstallBanner";
import ThemeToggle from "./ThemeToggle";

const MENUS = {
  seeker: [
    ["Overview", [
      ["/dashboard", "Dashboard", LayoutDashboard],
      ["/resume", "My Resume & ATS", FileText],
    ]],
    ["Jobs", [
      ["/jobs", "Live Jobs For You", Radar],
      ["/jd-match", "JD Matcher", Target],
      ["/tracker", "Job Tracker", KanbanSquare],
      ["/applications", "My Applications", ClipboardList],
    ]],
    ["AI Career Tools", [
      ["/interview", "AI Mock Interview", Mic],
      ["/ai-writer", "AI Resume Writer", Wand2],
      ["/roadmap", "Skill Roadmap", Map],
    ]],
  ],
  recruiter: [
    ["Recruiter", [
      ["/recruiter", "Dashboard", LayoutDashboard],
      ["/recruiter/jobs", "My Job Posts", Briefcase],
      ["/recruiter/jobs/new", "Post a Job", PlusCircle],
    ]],
  ],
  admin: [
    ["Admin", [
      ["/admin", "Analytics", BarChart3],
      ["/admin/users", "Users", Users],
    ]],
  ],
};

const SHORT = {
  "/dashboard": "Home", "/resume": "Resume", "/jobs": "Jobs", "/jd-match": "JD Match",
  "/recruiter": "Home", "/recruiter/jobs": "My Jobs", "/recruiter/jobs/new": "Post",
  "/admin": "Stats", "/admin/users": "Users",
};

export default function Layout() {
  const { user, logout } = useAuth();
  const [more, setMore] = useState(false);
  const loc = useLocation();
  useEffect(() => setMore(false), [loc.pathname]);
  const nav = useNavigate();
  const menu = MENUS[user.role] || [];
  const initials = (user.first_name?.[0] || user.username[0]).toUpperCase();

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="logo">
          <div className="logo-mark"><Sparkles size={18} /></div>
          <div>JobMatch AI<small>Resume • Match • Hire</small></div>
        </div>
        <nav className="nav">
          {menu.map(([label, links]) => (
            <div key={label}>
              <div className="nav-label">{label}</div>
              {links.map(([to, text, Icon]) => (
                <NavLink key={to} to={to} end><Icon />{text}</NavLink>
              ))}
            </div>
          ))}
          <div className="nav-label">Account</div>
          <NavLink to="/profile"><User />Profile</NavLink>
        </nav>
        <InstallBanner />
        <div className="sidebar-foot">
          <div className="avatar">{initials}</div>
          <div className="who"><b>{user.first_name ? `${user.first_name} ${user.last_name}` : user.username}</b><span>{user.role}</span></div>
          <ThemeToggle inline />
          <button className="icon-btn" title="Logout" onClick={() => { logout(); nav("/login"); }}><LogOut size={18} /></button>
        </div>
      </aside>
      <main className="main">
        <div className="mobile-top"><InstallBanner compact /><ThemeToggle inline className="mobile-theme" /></div>
        <Outlet />
      </main>
      <div className="mobile-nav">
        {menu.flatMap(([, l]) => l).slice(0, 4).map(([to, text, Icon]) => (
          <NavLink key={to} to={to} end><Icon size={20} /><span>{SHORT[to] || text}</span></NavLink>
        ))}
        <button className={more ? "active" : ""} onClick={() => setMore(!more)}>{more ? <X size={20} /> : <Menu size={20} />}<span>More</span></button>
      </div>
      {more && (
        <div className="mobile-sheet" onClick={() => setMore(false)}>
          <div className="mobile-sheet-inner" onClick={(e) => e.stopPropagation()}>
            {menu.map(([label, links]) => (
              <div key={label}>
                <div className="nav-label">{label}</div>
                <div className="sheet-grid">
                  {links.map(([to, text, Icon]) => <NavLink key={to} to={to} end className="sheet-item"><Icon size={20} /><span>{text}</span></NavLink>)}
                </div>
              </div>
            ))}
            <div className="nav-label">Account</div>
            <div className="sheet-grid">
              <NavLink to="/profile" className="sheet-item"><User size={20} /><span>Profile</span></NavLink>
              <button className="sheet-item" onClick={() => { logout(); nav("/login"); }}><LogOut size={20} /><span>Logout</span></button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
