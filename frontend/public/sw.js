/* JobMatch AI service worker: makes the site installable and loads fast.
   - API, admin and media requests always go to the network (never cached).
   - Pages: network first, cached copy when offline.
   - Built assets (/assets/*, /icons/*): cache first (file names change on every build). */
const CACHE = "jobmatch-v2";
const SHELL = ["/", "/manifest.json", "/icons/icon-192.png", "/icons/icon-512.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

const OFFLINE_HTML = `<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Offline - JobMatch AI</title>
<body style="font-family:system-ui;background:#0f1222;color:#fff;display:grid;place-items:center;height:100vh;margin:0;text-align:center">
<div><h2>You are offline</h2><p style="color:#c4c6e6">Connect to the internet and try again.</p>
<button onclick="location.reload()" style="padding:10px 18px;border:0;border-radius:10px;background:#5b5bf7;color:#fff;font-weight:600">Retry</button></div></body>`;

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;
  if (/^\/(api|django-admin|media|static\/admin)\//.test(url.pathname)) return; // always live

  if (req.mode === "navigate") {
    e.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put("/", copy));
          return res;
        })
        .catch(() => caches.match("/").then((r) => r || new Response(OFFLINE_HTML, { headers: { "Content-Type": "text/html" } })))
    );
    return;
  }

  if (url.pathname.startsWith("/assets/") || url.pathname.startsWith("/icons/")) {
    e.respondWith(
      caches.match(req).then((hit) => hit || fetch(req).then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(req, copy));
        return res;
      }))
    );
  }
});
