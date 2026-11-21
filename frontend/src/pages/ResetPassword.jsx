import { Navigate } from "react-router-dom";

// Old email links pointed here. Password reset now uses a 6-digit code on the Forgot password page.
export default function ResetPassword() {
  return <Navigate to="/forgot-password" replace />;
}
