// CNC Tools - Service Worker for PWA
// CACHE_NAME jest automatycznie aktualizowany przez lap_prod.py
const CACHE_NAME = 'cnctools-1.00.0g';

// Zasoby do cache'owania przy instalacji
const STATIC_CACHE = [
    '/',
    '/static/images/icons/icon-192x192.png',
    '/static/images/icons/icon-512x512.png',
    '/static/images/cnc-logo.png',
    '/static/fonts/primeicons.woff2',
];

// Instalacja - cache'owanie statycznych zasobow
self.addEventListener('install', (event) => {
    console.log('PWA: Service Worker instalowany');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('PWA: Cache otwarty');
                return cache.addAll(STATIC_CACHE);
            })
            .catch((error) => {
                console.log('PWA: Blad cache:', error);
            })
    );
    // Natychmiast aktywuj nowy SW
    self.skipWaiting();
});

// Aktywacja - czyszczenie starych cache'ow
self.addEventListener('activate', (event) => {
    console.log('PWA: Service Worker aktywowany');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('PWA: Usuwam stary cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    // Przejmij kontrole nad wszystkimi klientami
    self.clients.claim();
});

// Strategia: Network First z fallback do cache
// - Dla API zawsze siec (dane musza byc aktualne)
// - Dla statycznych zasobow: siec first, cache jako fallback
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Pomijamy requesty nie-GET
    if (event.request.method !== 'GET') {
        return;
    }

    // API - zawsze siec, bez cache
    if (url.pathname.startsWith('/api/')) {
        return;
    }

    // Dla pozostalych - Network First
    event.respondWith(
        fetch(event.request)
            .then((response) => {
                // Jesli odpowiedz OK, zapisz do cache
                if (response.status === 200) {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(event.request, responseClone);
                    });
                }
                return response;
            })
            .catch(() => {
                // Brak sieci - probuj z cache
                return caches.match(event.request).then((cachedResponse) => {
                    if (cachedResponse) {
                        return cachedResponse;
                    }
                    // Dla nawigacji - zwroc strone glowna z cache
                    if (event.request.mode === 'navigate') {
                        return caches.match('/');
                    }
                });
            })
    );
});
