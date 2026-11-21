// Captures the browser "install app" prompt so a button can show it later.
let deferred = null;
const listeners = new Set();

export const isStandalone = () =>
  window.matchMedia?.("(display-mode: standalone)").matches || window.navigator.standalone === true;
export const isIOS = () => /iphone|ipad|ipod/i.test(window.navigator.userAgent);

window.addEventListener("beforeinstallprompt", (e) => {
  e.preventDefault();
  deferred = e;
  listeners.forEach((fn) => fn(true));
});
window.addEventListener("appinstalled", () => {
  deferred = null;
  listeners.forEach((fn) => fn(false));
});

export const canInstall = () => !!deferred;
export function onInstallAvailable(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}
export async function promptInstall() {
  if (!deferred) return false;
  deferred.prompt();
  const { outcome } = await deferred.userChoice;
  deferred = null;
  listeners.forEach((fn) => fn(false));
  return outcome === "accepted";
}

export function registerServiceWorker() {
  if (import.meta.env.PROD && "serviceWorker" in navigator) {
    window.addEventListener("load", () => navigator.serviceWorker.register("/sw.js").catch(() => {}));
  }
}
