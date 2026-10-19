"""Serve the test page plus the files beside it in docs/ (the self-hosted fonts, icons), so the tools render what players see.

    from docsroute import route
    await pg.route('http://bsb.test/**', route(HTML))
"""
import os
from urllib.parse import urlparse
DOCS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs')

def route(html):
    async def handle(r):
        path = urlparse(r.request.url).path.lstrip('/')
        f = os.path.join(DOCS, path)
        if path and os.path.isfile(f): return await r.fulfill(path=f)
        await r.fulfill(body=html, content_type='text/html')
    return handle
