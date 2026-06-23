"""MusicWire — Publisher
Generates article HTML and maintains articles.json index.
"""
import json
import logging
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger('musicwire.publisher')

try:
    from config import ARTICLES_DIR, ARTICLES_JSON
except ImportError as e:
    log.error("Import error: %s", e)
    raise

FONTS = ("https://fonts.googleapis.com/css2?"
         "family=Barlow+Condensed:wght@700;900"
         "&family=Source+Serif+4:ital,wght@0,400;0,600;0,700;1,400;1,600"
         "&family=IBM+Plex+Mono:wght@400;500&display=swap")

WIRE_SCALE_CSS = {
    'STATIC': 'wire-rating static', 'SIGNAL': 'wire-rating signal',
    'BREAKING': 'wire-rating breaking', 'TRANSMISSION': 'wire-rating transmission',
    'FREQUENCY': 'wire-rating frequency',
}

TYPE_LABELS = {
    'news': 'NEWS', 'feature': 'FEATURE', 'review': 'REVIEW',
    'classic-review': 'REASSESSMENT', 'industry': 'INDUSTRY',
    'opinion': 'OPINION', 'live': 'LIVE',
}

NAV = '''  <div class="breaking-ticker">
    <span class="ticker-label">LIVE</span>
    <div class="ticker-track">MusicWire &mdash; Fast. Factual. On the wire. &mdash; Est. 2026 &mdash; musicwire.com</div>
  </div>
  <header class="site-header">
    <div class="header-top"><div class="container header-top-inner">
      <span class="mono" id="hdr-date"></span>
      <nav class="header-utility"><a href="../sections/about.html">About</a></nav>
    </div></div>
    <div class="header-main"><div class="container header-main-inner">
      <a href="../index.html" class="site-wordmark" aria-label="MusicWire">
        <span class="wm-music">MUSIC</span><span class="wm-rule"></span><span class="wm-wire">WIRE</span>
      </a>
      <nav class="site-nav">
        <a href="../sections/news.html">News</a>
        <a href="../sections/reviews.html">Reviews</a>
        <a href="../sections/features.html">Features</a>
        <a href="../sections/charts.html">Charts</a>
        <a href="../sections/industry.html">Industry</a>
      </nav>
    </div></div>
  </header>'''

FOOTER = '''  <footer class="site-footer">
    <div class="container footer-inner">
      <div class="footer-brand">
        <div class="footer-wm"><span class="wm-music">MUSIC</span><span class="wm-rule"></span><span class="wm-wire">WIRE</span></div>
        <p class="footer-tag">Fast. Factual. On the wire.</p>
        <p class="mono ftr-domain">musicwire.com &mdash; Est. 2026</p>
      </div>
      <nav class="footer-nav">
        <a href="../sections/news.html">News</a><a href="../sections/reviews.html">Reviews</a>
        <a href="../sections/features.html">Features</a><a href="../sections/charts.html">Charts</a>
        <a href="../sections/industry.html">Industry</a><a href="../sections/opinion.html">Opinion</a>
        <a href="../sections/live.html">Live</a><a href="../sections/about.html">About</a>
      </nav>
      <p class="footer-stmt">MusicWire is an independent online music publication. All editorial content &copy; MusicWire 2026. Reproduction without written permission is prohibited. MusicWire accepts no editorial direction from record labels, management companies, or advertisers.</p>
    </div>
    <div class="footer-bottom"><div class="container ftr-btm">
      <span class="mono">&copy; MusicWire 2026</span><span class="mono">musicwire.com</span>
    </div></div>
  </footer>
  <script>
    const d=new Date(),M=['January','February','March','April','May','June','July','August','September','October','November','December'];
    const el=document.getElementById('hdr-date'); if(el) el.textContent=d.getDate()+' '+M[d.getMonth()]+' '+d.getFullYear();
  </script>'''


def _slugify(text: str) -> str:
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode()
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    text = re.sub(r'[\s_-]+', '-', text)
    return text[:80]


def _fmt_date(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso.replace('Z', '+00:00'))
        M = ['January','February','March','April','May','June',
             'July','August','September','October','November','December']
        return f"{dt.day} {M[dt.month-1]} {dt.year}"
    except Exception:
        return iso


def _hero_html(images: list[dict]) -> tuple[str, str]:
    if not images:
        return '<div class="article-hero article-hero--empty"></div>', ''
    img = images[0]
    url, alt, credit = img.get('url',''), img.get('alt',''), img.get('credit','')
    cap = f'<p class="hero-caption mono">Photo: {credit}</p>' if credit else ''
    return f'<div class="article-hero"><img src="{url}" alt="{alt}" loading="eager"></div>{cap}', url


def _inline_imgs(images: list[dict]) -> list[str]:
    result = []
    for img in images[1:]:
        url, alt, credit = img.get('url',''), img.get('alt',''), img.get('credit','')
        cap = f'<p class="inline-caption mono">Photo: {credit}</p>' if credit else ''
        result.append(f'<figure class="article-inline"><img src="{url}" alt="{alt}" loading="lazy">{cap}</figure>')
    return result


def _inject_images(body: str, inlines: list[str]) -> str:
    if not inlines:
        return body
    parts = re.split(r'(?=<p[\s>])', body)
    out, idx, n = [], 0, 0
    for part in parts:
        out.append(part)
        if '<p' in part:
            n += 1
            if n % 3 == 0 and idx < len(inlines):
                out.append(inlines[idx])
                idx += 1
    return ''.join(out)


def _render_html(article_data: dict, images: list[dict]) -> str:
    title        = article_data.get('title', '')
    deck         = article_data.get('deck', '')
    body         = article_data.get('body', '')
    atype        = article_data.get('type', 'news')
    rating       = article_data.get('rating', '')
    published    = article_data.get('publishedAt', datetime.now(timezone.utc).isoformat())
    artist       = article_data.get('artistName', '')
    album        = article_data.get('albumName', '')

    label      = TYPE_LABELS.get(atype, atype.upper())
    date_str   = _fmt_date(published)
    hero, hero_url = _hero_html(images)
    body_final = _inject_images(body, _inline_imgs(images))

    rating_html = ''
    if rating and rating in WIRE_SCALE_CSS:
        rating_html = f'<div class="{WIRE_SCALE_CSS[rating]}">{rating}</div>\n      '

    meta_parts = [p for p in [artist, album, date_str, 'MusicWire'] if p]
    meta_str   = ' &mdash; '.join(meta_parts)
    og_img     = f'<meta property="og:image" content="{hero_url}">' if hero_url else ''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} &mdash; MusicWire</title>
  <meta name="description" content="{deck}">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{deck}">
  {og_img}
  <meta name="theme-color" content="#1A5CFF">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="{FONTS}" rel="stylesheet">
  <link rel="stylesheet" href="../assets/css/style.css">
</head>
<body>
{NAV}
  <article>
    {hero}
    <div class="article-container">
      <span class="article-eyebrow">{label}</span>
      {rating_html}<h1 class="article-title">{title}</h1>
      <p class="article-deck">{deck}</p>
      <div class="article-meta mono">{meta_str}</div>
      <div class="article-body">{body_final}</div>
    </div>
  </article>
{FOOTER}
</body>
</html>'''


def load_index() -> list[dict]:
    if not ARTICLES_JSON.exists():
        return []
    try:
        return json.loads(ARTICLES_JSON.read_text()).get('articles', [])
    except Exception:
        return []


def save_index(articles: list[dict]) -> None:
    ARTICLES_JSON.parent.mkdir(parents=True, exist_ok=True)
    ARTICLES_JSON.write_text(json.dumps({'articles': articles}, indent=2, ensure_ascii=False))


def is_duplicate(title: str, articles: list[dict], threshold: int = 10) -> bool:
    words = set(title.lower().split())
    for a in articles:
        if len(words & set(a.get('title','').lower().split())) >= threshold:
            return True
    return False


def count_today(articles: list[dict]) -> int:
    today = datetime.now(timezone.utc).date().isoformat()
    return sum(1 for a in articles if a.get('publishedAt','').startswith(today))


def count_today_by_type(articles: list[dict], atype: str) -> int:
    today = datetime.now(timezone.utc).date().isoformat()
    return sum(1 for a in articles
               if a.get('publishedAt','').startswith(today) and a.get('type') == atype)


def publish_article(article_data: dict, images: list[dict]) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    article_data.setdefault('publishedAt', now)
    title = article_data.get('title', 'Untitled')
    slug  = _slugify(title)

    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    base, counter = slug, 1
    while (ARTICLES_DIR / f'{slug}.html').exists():
        slug = f'{base}-{counter}'; counter += 1

    html = _render_html(article_data, images)
    (ARTICLES_DIR / f'{slug}.html').write_text(html, encoding='utf-8')
    log.info("Written: articles/%s.html", slug)

    hero_url = images[0].get('url','') if images else ''
    entry = {
        'slug':        slug,
        'title':       title,
        'deck':        article_data.get('deck',''),
        'type':        article_data.get('type','news'),
        'rating':      article_data.get('rating',''),
        'publishedAt': article_data.get('publishedAt', now),
        'artistName':  article_data.get('artistName',''),
        'albumName':   article_data.get('albumName',''),
        'breaking':    article_data.get('breaking', False),
        'tags':        article_data.get('tags', []),
        'heroImage':   hero_url,
        'url':         f'articles/{slug}.html',
    }

    articles = load_index()
    articles.insert(0, entry)
    save_index(articles[:500])
    return entry
