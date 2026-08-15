"""Security response headers.

Pure ASGI rather than BaseHTTPMiddleware: the latter buffers the response body,
which breaks streaming and interacts badly with session middleware ordering.
"""

from __future__ import annotations

HEADERS = {
    b"x-content-type-options": b"nosniff",
    b"x-frame-options": b"DENY",
    b"referrer-policy": b"strict-origin-when-cross-origin",
    b"permissions-policy": b"geolocation=(), microphone=(), camera=()",
    # No CDN assets: everything is served from this origin, so the policy can stay
    # tight. 'unsafe-inline' covers FastHTML's inline Style() blocks.
    b"content-security-policy": (
        b"default-src 'self'; style-src 'self' 'unsafe-inline'; "
        b"script-src 'self' 'unsafe-inline'; img-src 'self' data:; "
        b"connect-src 'self'; frame-ancestors 'none'; base-uri 'self'"
    ),
}


class SecurityHeadersMiddleware:
    def __init__(self, app, https_only: bool = False):
        self.app = app
        self.https_only = https_only

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = message.setdefault("headers", [])
                existing = {name.lower() for name, _ in headers}
                for name, value in HEADERS.items():
                    if name not in existing:
                        headers.append((name, value))
                if self.https_only and b"strict-transport-security" not in existing:
                    headers.append(
                        (b"strict-transport-security", b"max-age=31536000; includeSubDomains")
                    )
            await send(message)

        await self.app(scope, receive, send_wrapper)
