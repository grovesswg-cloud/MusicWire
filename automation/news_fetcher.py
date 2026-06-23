"""MusicWire — News Fetcher"""
import json
import logging
import re
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape

log = logging.getLogger('musicwire.news')

try:
    from config import RSS_FEEDS
except ImportError:
    RSS_FEEDS = []

_MUSIC_KEYWORDS = [
    'album', 'single', 'tour', 'concert', 'artist', 'band', 'release',
    'music', 'record', 'label', 'streaming', 'chart', 'grammy', 'award',
    'festival', 'rapper', 'singer', 'producer', 'track', 'ep', 'mixtape',
    'billboard', 'spotify', 'apple music', 'vinyl', 'hip-hop', 'pop',
    'rock', 'r&b', 'country', 'electronic', 'jazz', 'tour dates', 'setlist',
    'sold out', 'debut', 'comeback', 'collaboration', 'biopic', 'documentary',
]

_STRIP_TAGS = re.compile(r'<[^>]+')
_WHITESPACE = re.compile(r'\s+')
UA = 'MusicWire/1.0 (musicwire.com)'


def _clean(text: str) -> str:
    if not text:
        return ''
    text = unescape(_STRIP_TAGS.sub(' ', text))
    return _WHITESPACE.sub(' ', text).strip()


def _is_music(title: str, summary: str) -> bool:
    combined = (title + ' ' + summary).lower()
    return any(kw in combined for kw in _MUSIC_KEYWORDS)


def _fetch_feed(url: str) -> list[dict]:
    items = []
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read()

        if b'"version"' in content[:100] and b'"items"' in content[:200]:
            try:
                data = json.loads(content)
                for item in data.get('items', [])[:20]:
                    items.append({
                        'title':   _clean(item.get('title', '')),
                        'summary': _clean(item.get('summary', item.get('content_text', '')))[:400],
                        'url':     item.get('url', ''),
                        'source':  url,
                    })
                return items
            except Exception:
                pass

        root = ET.fromstring(content)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}

        for item in root.findall('.//item')[:20]:
            title   = _clean(item.findtext('title', ''))
            summary = _clean(item.findtext('description', ''))[:400]
            link    = item.findtext('link', '')
            if title:
                items.append({'title': title, 'summary': summary, 'url': link, 'source': url})

        if not items:
            for entry in root.findall('.//atom:entry', ns)[:20]:
                title   = _clean(entry.findtext('atom:title', '', ns))
                summary = _clean(entry.findtext('atom:summary', '', ns))[:400]
                link_el = entry.find('atom:link', ns)
                link    = link_el.get('href', '') if link_el is not None else ''
                if title:
                    items.append({'title': title, 'summary': summary, 'url': link, 'source': url})

    except Exception as exc:
        log.warning("Feed failed %s: %s", url[:60], exc)
    return items


def get_trending_music_news() -> list[dict]:
    all_items = []
    seen: set[str] = set()
    for feed_url in RSS_FEEDS:
        for item in _fetch_feed(feed_url):
            key = item['title'].lower()[:80]
            if key and key not in seen and _is_music(item['title'], item['summary']):
                seen.add(key)
                all_items.append(item)
    log.info("Fetched %d unique music stories", len(all_items))
    return all_items
