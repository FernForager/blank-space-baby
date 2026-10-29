"""Read a fifa.com article as plain text, for research and fact checks (Oct 29, 2026).

    python3 tools/fifa.py https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/...

fifa.com draws its pages in the browser, so a plain fetch comes back empty. FIFA's own content feed (cxm-api.fifa.com)
serves the same text: the page's JSON names its article section, and the section holds the article's rich text."""
import json, re, sys, urllib.request
API = 'https://cxm-api.fifa.com/fifaplusweb/api'
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30) as r: return json.load(r)
def text(node):
    """Contentful rich text to plain lines."""
    out = []
    def walk(n, buf):
        if isinstance(n, dict):
            if n.get('nodeType') == 'text': buf.append(n.get('value', ''))
            for c in n.get('content', []) or []: walk(c, buf)
        elif isinstance(n, list):
            for c in n: walk(c, buf)
    for block in (node.get('content') or []):
        buf = []; walk(block, buf); line = ''.join(buf).strip()
        if line: out.append(('- ' if block.get('nodeType') in ('unordered-list', 'ordered-list') else '') + line)
    return out
path = re.sub(r'^https?://(www\.)?fifa\.com', '', sys.argv[1]).split('?')[0]
page = get(API + '/pages' + path)
print('#', page.get('meta', {}).get('title'), '| created', page.get('createdDate'))
for s in page.get('sections', []):
    if s.get('entryType') != 'article': continue
    a = get(API + '/' + s['entryEndpoint'].lstrip('/'))
    print('published', a.get('articlePublishedDate') or a.get('publishedDate'), '| updated', a.get('updatedDate') or a.get('lastUpdated'))
    body = a.get('richtext') or a.get('body') or a.get('content') or {}
    if isinstance(body, dict): print('\n'.join(text(body)))
    else: print(json.dumps(a)[:3000])
