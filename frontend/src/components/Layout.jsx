import {
  BarChart3, Briefcase, FileText, KanbanSquare, LayoutDashboard, LogOut, Radar,
  Sparkles, Target, User, Users, ClipboardList, PlusCircle,
} from "lucide-react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";

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

export default function Layout() {
  const { user, logout } = useAuth();
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
        <div className="sidebar-foot">
          <div className="avatar">{initials}</div>
          <div className="who"><b>{user.first_name ? `${user.first_name} ${user.last_name}` : user.username}</b><span>{user.role}</span></div>
          <button className="icon-btn" title="Logout" onClick={() => { logout(); nav("/login"); }}><LogOut size={18} /></button>
        </div>
      </aside>
      <main className="main"><Outlet /></main>
      <div className="mobile-nav">
        {menu.flatMap(([, l]) => l).slice(0, 5).map(([to, , Icon]) => (
          <NavLink key={to} to={to} end><Icon size={20} /></NavLink>
        ))}
      </div>
    </div>
  );
}
