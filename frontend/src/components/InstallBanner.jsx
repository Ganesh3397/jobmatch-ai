import { Download, Share, X } from "lucide-react";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { canInstall, isIOS, isStandalone, onInstallAvailable, promptInstall } from "../pwa";

const DISMISS_KEY = "jm-install-dismissed";

export default function InstallBanner({ compact = false }) {
  const [available, setAvailable] = useState(canInstall());
  const [dismissed, setDismissed] = useState(() => {
    try { return localStorage.getItem(DISMISS_KEY) === "1"; } catch { return false; }
  });
  useEffect(() => onInstallAvailable(setAvailable), []);

  if (isStandalone() || dismissed) return null;
  const ios = isIOS();
  if (!available && !ios) return null;

  const dismiss = () => { setDismissed(true); try { localStorage.setItem(DISMISS_KEY, "1"); } catch { /* ignore */ } };
  const install = async () => {
    if (ios) { toast("On iPhone: tap the Share button, then 'Add to Home Screen'", { icon: "📲", duration: 6000 }); return; }
    if (await promptInstall()) toast.success("App installed! Open it from your home screen 🎉");
  };

  if (compact) {
    return <button className="btn btn-soft btn-sm" onClick={install}>{ios ? <Share /> : <Download />}Install app</button>;
  }
  return (
    <div className="install-banner">
      <Download size={16} />
      <span>Install JobMatch AI as an app</span>
      <button className="btn btn-primary btn-sm" onClick={install}>Install</button>
      <button className="icon-btn" onClick={dismiss} title="Hide"><X size={14} /></button>
    </div>
  );
}
