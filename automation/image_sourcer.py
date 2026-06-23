"""MusicWire — Image Sourcer
Fetches real artist and album images from music APIs.
No generic stock photos. Real images of the artist or project only.

Priority chain:
  Albums:  iTunes Search API -> Last.fm -> MusicBrainz/Cover Art Archive
  Artists: Last.fm -> iTunes -> Wikipedia
"""
import json
import logging
import time
import urllib.parse
import urllib.request

log = logging.getLogger('musicwire.images')

try:
    from config import LASTFM_API_KEY
except ImportError:
    LASTFM_API_KEY = ''

UA             = 'MusicWire/1.0 (musicwire.com)'
ITUNES_SEARCH  = 'https://itunes.apple.com/search'
LASTFM_API     = 'https://ws.audioscrobbler.com/2.0/'
MBRAINZ_API    = 'https://musicbrainz.org/ws/2/'
COVER_ART_BASE = 'https://coverartarchive.org/release/'
WIKIPEDIA_API  = 'https://en.wikipedia.org/w/api.php'


def _get(url: str, timeout: int = 12) -> dict | None:
    try:
        req = urllib.request.Request(
            url, headers={'User-Agent': UA, 'Accept': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8', errors='replace'))
    except Exception as exc:
        log.debug("Request failed %s: %s", url[:80], exc)
        return None


def _itunes_album(artist: str, album: str) -> str | None:
    q = urllib.parse.urlencode({'term': f'{artist} {album}', 'entity': 'album', 'limit': 5})
    data = _get(f'{ITUNES_SEARCH}?{q}')
    if not data:
        return None
    for r in data.get('results', []):
        art = r.get('artworkUrl100', '')
        if art:
            return art.replace('100x100bb', '600x600bb')
    return None


def _itunes_artist(artist: str) -> str | None:
    q = urllib.parse.urlencode({'term': artist, 'entity': 'musicArtist', 'limit': 5})
    data = _get(f'{ITUNES_SEARCH}?{q}')
    if not data:
        return None
    for r in data.get('results', []):
        art = r.get('artworkUrl100', '')
        if art:
            return art.replace('100x100bb', '600x600bb')
    return None


def _lastfm_artist(artist: str) -> str | None:
    if not LASTFM_API_KEY:
        return None
    params = urllib.parse.urlencode({
        'method': 'artist.getInfo', 'artist': artist,
        'api_key': LASTFM_API_KEY, 'format': 'json',
    })
    data = _get(f'{LASTFM_API}?{params}')
    if not data:
        return None
    for img in reversed(data.get('artist', {}).get('image', [])):
        url = img.get('#text', '')
        if url and 'noimage' not in url and url.strip():
            return url
    return None


def _lastfm_album(artist: str, album: str) -> str | None:
    if not LASTFM_API_KEY:
        return None
    params = urllib.parse.urlencode({
        'method': 'album.getInfo', 'artist': artist, 'album': album,
        'api_key': LASTFM_API_KEY, 'format': 'json',
    })
    data = _get(f'{LASTFM_API}?{params}')
    if not data:
        return None
    for img in reversed(data.get('album', {}).get('image', [])):
        url = img.get('#text', '')
        if url and 'noimage' not in url and url.strip():
            return url
    return None


def _musicbrainz_cover(artist: str, album: str) -> str | None:
    q = urllib.parse.urlencode({
        'query': f'artist:"{artist}" AND release:"{album}"',
        'fmt': 'json', 'limit': 3,
    })
    data = _get(f'{MBRAZ_API}release?{q}') if False else _get(f'{MBRAZ_API}release?{q}') if False else None
    data = _get(f'{MBRAZ_API}release?{q}'.replace(MBRAZ_API, MBRAZ_API)) if False else _get(f'https://musicbrainz.org/ws/2/release?{q}')
    if not data:
        return None
    for release in data.get('releases', []):
        mbid = release.get('id')
        if not mbid:
            continue
        time.sleep(1.2)
        art_data = _get(f'{COVER_ART_BASE}{mbid}/')
        if not art_data:
            continue
        for img in art_data.get('images', []):
            if img.get('front'):
                thumbnails = img.get('thumbnails', {})
                url = thumbnails.get('large') or thumbnails.get('500') or img.get('image')
                if url:
                    return url
    return None


def _wikipedia_image(subject: str) -> str | None:
    params = urllib.parse.urlencode({
        'action': 'query', 'titles': subject, 'prop': 'pageimages',
        'piprop': 'original', 'format': 'json', 'redirects': 1,
    })
    data = _get(f'{WIKIPEDIA_API}?{params}')
    if not data:
        return None
    for page in data.get('query', {}).get('pages', {}).values():
        url = page.get('original', {}).get('source', '')
        if url:
            return url
    return None


def get_album_image(artist: str, album: str) -> dict | None:
    log.info("Album image: %s — %s", artist, album)
    url = _itunes_album(artist, album)
    if url:
        log.info("  [iTunes] %s", url[:70])
        return {'url': url, 'credit': artist, 'provider': 'iTunes', 'alt': f'{artist} — {album}'}
    url = _lastfm_album(artist, album)
    if url:
        log.info("  [Last.fm] %s", url[:70])
        return {'url': url, 'credit': artist, 'provider': 'Last.fm', 'alt': f'{artist} — {album}'}
    url = _musicbrainz_cover(artist, album)
    if url:
        log.info("  [CoverArtArchive] %s", url[:70])
        return {'url': url, 'credit': artist, 'provider': 'Cover Art Archive', 'alt': f'{artist} — {album}'}
    log.info("  No album art found")
    return None


def get_artist_image(artist: str) -> dict | None:
    log.info("Artist image: %s", artist)
    url = _lastfm_artist(artist)
    if url:
        log.info("  [Last.fm] %s", url[:70])
        return {'url': url, 'credit': artist, 'provider': 'Last.fm', 'alt': artist}
    url = _itunes_artist(artist)
    if url:
        log.info("  [iTunes] %s", url[:70])
        return {'url': url, 'credit': artist, 'provider': 'iTunes', 'alt': artist}
    url = _wikipedia_image(artist)
    if url:
        log.info("  [Wikipedia] %s", url[:70])
        return {'url': url, 'credit': f'{artist} / Wikimedia Commons', 'provider': 'Wikipedia', 'alt': artist}
    log.info("  No artist image found")
    return None


def get_article_images(article_data: dict) -> list[dict]:
    """Source real images for an article based on artistName/albumName fields."""
    artist       = article_data.get('artistName', '').strip()
    album        = article_data.get('albumName', '').strip()
    article_type = article_data.get('type', 'news')
    images: list[dict] = []

    if article_type in ('review', 'classic-review') and artist and album:
        album_img = get_album_image(artist, album)
        if album_img:
            images.append(album_img)
        artist_img = get_artist_image(artist)
        if artist_img:
            images.append(artist_img)
    elif artist:
        artist_img = get_artist_image(artist)
        if artist_img:
            images.append(artist_img)
        secondary = article_data.get('secondaryArtist', '').strip()
        if secondary:
            sec_img = get_artist_image(secondary)
            if sec_img:
                images.append(sec_img)
        elif album:
            album_img = get_album_image(artist, album)
            if album_img:
                images.append(album_img)

    return images
