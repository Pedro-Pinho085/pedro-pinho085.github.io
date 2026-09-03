/* Sinal da Cruz - service worker
   Cache do "app shell" para abrir offline dentro do onibus. */
const CACHE = "sinaldacruz-v2";
const ASSETS = [
  "./",
  "./index.html",
  "./manifest.json",
  "./trajeto.json",
  "./icon-192.png",
  "./icon-512.png",
  "./apple-touch-icon.png",
  "./favicon.png"
];

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);

  if (url.origin === location.origin) {
    // app proprio: cache primeiro, atualiza em segundo plano
    e.respondWith(
      caches.match(req).then(hit => {
        const rede = fetch(req).then(res => {
          if (res && res.ok) {
            const copia = res.clone();
            caches.open(CACHE).then(c => c.put(req, copia));
          }
          return res;
        }).catch(() => hit);
        return hit || rede;
      })
    );
  } else {
    // fontes do Google etc: usa cache se tiver, senao busca e guarda
    e.respondWith(
      caches.match(req).then(hit => hit || fetch(req).then(res => {
        if (res && (res.ok || res.type === "opaque")) {
          const copia = res.clone();
          caches.open(CACHE).then(c => c.put(req, copia));
        }
        return res;
      }).catch(() => hit))
    );
  }
});

// permite ao app forcar ativacao de uma versao nova
self.addEventListener("message", e => {
  if (e.data === "skip-waiting") self.skipWaiting();
});
