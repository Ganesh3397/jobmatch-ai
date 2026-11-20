import { Navigate, Route, Routes } from "react-router-dom";
import { homeFor, useAuth } from "./auth";
import Layout from "./components/Layout";
import { Loader } from "./components/ui";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Profile from "./pages/Profile";
import SeekerDashboard from "./pages/seeker/Dashboard";
import ResumePage from "./pages/seeker/Resume";
import LiveJobs from "./pages/seeker/LiveJobs";
import JDMatch from "./pages/seeker/JDMatch";
import Tracker from "./pages/seeker/Tracker";
import Applications from "./pages/seeker/Applications";
import RecruiterDashboard from "./pages/recruiter/Dashboard";
import RecruiterJobs from "./pages/recruiter/Jobs";
import JobForm from "./pages/recruiter/JobForm";
import Applicants from "./pages/recruiter/Applicants";
import AdminDashboard from "./pages/admin/Dashboard";
import AdminUsers from "./pages/admin/Users";

function Guard({ roles, children }) {
  const { user, ready } = useAuth();
  if (!ready) return <Loader />;
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to={homeFor(user.role)} replace />;
  return children;
}

export default function App() {
  const { user, ready } = useAuth();
  if (!ready) return <Loader />;

  return (
    <Routes>
      <Route path="/" element={user ? <Navigate to={homeFor(user.role)} /> : <Landing />} />
      <Route path="/login" element={user ? <Navigate to={homeFor(user.role)} /> : <Login />} />
      <Route path="/register" element={user ? <Navigate to={homeFor(user.role)} /> : <Register />} />

      <Route element={<Guard><Layout /></Guard>}>
        <Route path="/profile" element={<Profile />} />

        <Route path="/dashboard" element={<Guard roles={["seeker"]}><SeekerDashboard /></Guard>} />
        <Route path="/resume" element={<Guard roles={["seeker"]}><ResumePage /></Guard>} />
        <Route path="/jobs" element={<Guard roles={["seeker"]}><LiveJobs /></Guard>} />
        <Route path="/jd-match" element={<Guard roles={["seeker"]}><JDMatch /></Guard>} />
        <Route path="/tracker" element={<Guard roles={["seeker"]}><Tracker /></Guard>} />
        <Route path="/applications" element={<Guard roles={["seeker"]}><Applications /></Guard>} />

        <Route path="/recruiter" element={<Guard roles={["recruiter", "admin"]}><RecruiterDashboard /></Guard>} />
        <Route path="/recruiter/jobs" element={<Guard roles={["recruiter", "admin"]}><RecruiterJobs /></Guard>} />
        <Route path="/recruiter/jobs/new" element={<Guard roles={["recruiter", "admin"]}><JobForm /></Guard>} />
        <Route path="/recruiter/jobs/:id/edit" element={<Guard roles={["recruiter", "admin"]}><JobForm /></Guard>} />
        <Route path="/recruiter/jobs/:id/applicants" element={<Guard roles={["recruiter", "admin"]}><Applicants /></Guard>} />

        <Route path="/admin" element={<Guard roles={["admin"]}><AdminDashboard /></Guard>} />
        <Route path="/admin/users" element={<Guard roles={["admin"]}><AdminUsers /></Guard>} />
      </Route>
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
}
