```javascript
const CACHE_NAME = "skillbridge-v3";

const FILES_TO_CACHE = [
    "/",
    "/manifest.json",
    "/assets/style.css",
    "/assets/script.js",
    "/register.html",
    "/forgot-password.html"
];

// Install: cache only files that successfully load.
self.addEventListener("install", event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(async cache => {
                for (const url of FILES_TO_CACHE) {
                    try {
                        const response = await fetch(url, {
                            cache: "reload"
                        });

                        if (response.ok) {
                            await cache.put(url, response);
                        } else {
                            console.warn(
                                "Could not cache:",
                                url,
                                response.status
                            );
                        }
                    } catch (error) {
                        console.warn("Cache skipped:", url, error);
                    }
                }
            })
    );

    self.skipWaiting();
});

// Activate: remove old caches.
self.addEventListener("activate", event => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(
                keys
                    .filter(key => key !== CACHE_NAME)
                    .map(key => caches.delete(key))
            )
        ).then(() => self.clients.claim())
    );
});

// Fetch: network first, then cached fallback.
self.addEventListener("fetch", event => {
    const request = event.request;
    const url = new URL(request.url);

    // Handle only this website's GET requests.
    if (
        request.method !== "GET" ||
        url.origin !== self.location.origin
    ) {
        return;
    }

    // Do not intercept API requests or login requests.
    if (url.pathname.startsWith("/api/")) {
        return;
    }

    event.respondWith(
        fetch(request)
            .then(response => {
                if (response.ok) {
                    const copy = response.clone();

                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(request, copy).catch(() => {});
                    });
                }

                return response;
            })
            .catch(async () => {
                const cached = await caches.match(request);

                if (cached) {
                    return cached;
                }

                if (request.mode === "navigate") {
                    const home = await caches.match("/");

                    if (home) {
                        return home;
                    }
                }

                return new Response(
                    "You are offline. Please check your internet connection.",
                    {
                        status: 503,
                        headers: {
                            "Content-Type": "text/plain; charset=utf-8"
                        }
                    }
                );
            })
    );
});
```
