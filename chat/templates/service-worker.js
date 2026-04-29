const CACHE_NAME = 'wiberchat-v1';
const URLS_TO_CACHE = [
  '/',
  '/new-chat/',
  '/actus/',
  '/profile/',
  '/static/css/style.css',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
];

// Installation: cache les pages de base
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(URLS_TO_CACHE))
  );
});

// Interception des requêtes
self.addEventListener('fetch', event => {
  // Stratégie: Network First, puis Cache
  event.respondWith(
    fetch(event.request)
      .then(response => {
        // Si OK, on met en cache et on retourne
        let clone = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        return response;
      })
      .catch(() => caches.match(event.request)) // Sinon on sert le cache
  );
});

// Background Sync pour les messages
self.addEventListener('sync', event => {
  if (event.tag === 'sync-messages') {
    event.waitUntil(syncMessages());
  }
});

async function syncMessages() {
  const db = await openDB();
  const messages = await db.getAll('outbox');

  for (let msg of messages) {
    try {
      await fetch('/api/send-message/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': msg.csrf },
        body: JSON.stringify(msg.data)
      });
      await db.delete('outbox', msg.id);
      // Notifie la page pour changer l'icône horloge → double coche
      self.clients.matchAll().then(clients => {
        clients.forEach(client => client.postMessage({ type: 'SYNCED', id: msg.id }));
      });
    } catch (err) {
      console.log('Sync failed, will retry');
    }
  }
}

// IndexedDB simple
function openDB() {
  return new Promise((resolve, reject) => {
    let request = indexedDB.open('WiberchatDB', 1);
    request.onupgradeneeded = e => {
      let db = e.target.result;
      if (!db.objectStoreNames.contains('outbox')) {
        db.createObjectStore('outbox', { keyPath: 'id', autoIncrement: true });
      }
    };
    request.onsuccess = e => resolve(e.target.result);
    request.onerror = e => reject(e.target.error);
  });
}