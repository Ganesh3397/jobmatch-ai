import { Moon, Sun } from "lucide-react";
import { useTheme } from "../theme";

/** Floating button (login / register / landing) or inline icon (sidebar). */
export default function ThemeToggle({ inline = false, className = "" }) {
  const [theme, toggle] = useTheme();
  const Icon = theme === "dark" ? Sun : Moon;
  const label = theme === "dark" ? "Switch to light mode" : "Switch to dark mode";
  return (
    <button type="button" className={inline ? `icon-btn ${className}` : `theme-toggle ${className}`} onClick={toggle} title={label} aria-label={label}>
      <Icon size={18} />
    </button>
  );
}
