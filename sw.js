const CACHE_NAME = 'sudoku-solver-cache-v2';

self.addEventListener('install', (event) => {
  // Skip waiting to activate the service worker immediately
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  // Clear all caches to ensure no stale index.html or bundle files are served
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          return caches.delete(cache);
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  // Pass-through network requests.
  // Streamlit apps run completely dynamically using WebSockets and cannot run offline.
  // Caching index.html or chunk files causes Vite dynamic import failures upon redeployment.
  event.respondWith(fetch(event.request));
});
