const CACHE_NAME = 'wiberchat-v4';

// 1. Ressources critiques à mettre en cache
const ASSETS_TO_CACHE = [
    '/',
    '/chats/',
    '/actus/',
    '/profile/',
    '/static/manifest.json',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css'
];

// Installation : Cache initial
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('Wiberchat : Mise en cache v4...');
            return cache.addAll(ASSETS_TO_CACHE);
        })
    );
    self.skipWaiting();
});

// Activation : Supprime vieux caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cache) => {
                    if (cache !== CACHE_NAME) {
                        console.log('Suppression ancien cache:', cache);
                        return caches.delete(cache);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// Fetch : Stratégies de cache
self.addEventListener('fetch', (event) => {
    if (event.request.method !== 'GET' || event.request.url.includes('/admin/')) {
        return;
    }

    const url = event.request.url;

    // 1. Cache First : Images profil + icônes + avatars
    if (url.includes('/media/profile_pics/') ||
        url.includes('/static/icons/') ||
        url.includes('ui-avatars.com')) {
        event.respondWith(
            caches.match(event.request).then(cached => {
                if (cached) return cached;
                return fetch(event.request).then(response => {
                    return caches.open(CACHE_NAME).then(cache => {
                        cache.put(event.request, response.clone());
                        return response;
                    });
                });
            })
        );
        return;
    }

    // 2. Network First : Pages HTML pour avoir les nouveaux messages
    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request)
                .then(response => {
                    return caches.open(CACHE_NAME).then(cache => {
                        cache.put(event.request, response.clone());
                        return response;
                    });
                })
                .catch(() => {
                    return caches.match(event.request).then(cached => {
                        return cached || caches.match('/chats/');
                    });
                })
        );
        return;
    }

    // 3. Stale While Revalidate : CSS, JS
    event.respondWith(
        caches.match(event.request).then(cached => {
            const fetchPromise = fetch(event.request).then(networkResponse => {
                caches.open(CACHE_NAME).then(cache => {
                    cache.put(event.request, networkResponse.clone());
                });
                return networkResponse;
            });
            return cached || fetchPromise;
        })
    );
});

// Background Sync : Envoi messages offline
self.addEventListener('sync', event => {
  if (event.tag === 'sync-messages') {
    event.waitUntil(syncMessages());
  }
});

async function syncMessages() {
  const db = await openDB();
  const tx = db.transaction('outbox', 'readonly');
  const store = tx.objectStore('outbox');
  const messages = await store.getAll();

  for (const msg of messages) {
    try {
      const res = await fetch('/api/send-message/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': msg.csrf
        },
        body: JSON.stringify(msg.data)
      });

      if (res.ok) {
        const data = await res.json();
        // Supprime de outbox
        const delTx = db.transaction('outbox', 'readwrite');
        delTx.objectStore('outbox').delete(msg.id);

        // Notifie la page
        self.clients.matchAll().then(clients => {
          clients.forEach(client => {
            client.postMessage({
              type: 'SYNCED',
              id: msg.id,
              realId: data.id
            });
          });
        });
      }
    } catch (err) {
      console.log('Sync failed, will retry');
    }
  }
}

function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('WiberchatDB', 1);
    request.onupgradeneeded = e => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains('outbox')) {
        db.createObjectStore('outbox', { keyPath: 'id' });
      }
    };
    request.onsuccess = e => resolve(e.target.result);
    request.onerror = e => reject(e.target.error);
  });
}