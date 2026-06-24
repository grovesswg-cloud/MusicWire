"""MusicWire — Album Finder"""
import json
import logging
import random
import re

log = logging.getLogger('musicwire.albums')

try:
    import google.generativeai as genai
    from config import GEMINI_API_KEY, GEMINI_MODEL
except ImportError as e:
    log.error("Import error: %s", e)
    raise

CLASSIC_ALBUMS = [
    {'artist': 'Kendrick Lamar',    'album': 'good kid, m.A.A.d city',                    'year': '2012', 'genre': 'Hip-Hop'},
    {'artist': 'Beyonce',           'album': 'Lemonade',                                   'year': '2016', 'genre': 'R&B'},
    {'artist': 'Frank Ocean',       'album': 'Blonde',                                     'year': '2016', 'genre': 'R&B/Pop'},
    {'artist': 'Radiohead',         'album': 'OK Computer',                                'year': '1997', 'genre': 'Alternative Rock'},
    {'artist': 'Amy Winehouse',     'album': 'Back to Black',                              'year': '2006', 'genre': 'Soul'},
    {'artist': 'Jay-Z',             'album': 'The Blueprint',                              'year': '2001', 'genre': 'Hip-Hop'},
    {'artist': 'Lauryn Hill',       'album': 'The Miseducation of Lauryn Hill',            'year': '1998', 'genre': 'R&B/Hip-Hop'},
    {'artist': 'Kanye West',        'album': 'My Beautiful Dark Twisted Fantasy',          'year': '2010', 'genre': 'Hip-Hop'},
    {'artist': 'Outkast',           'album': 'Stankonia',                                  'year': '2000', 'genre': 'Hip-Hop'},
    {'artist': 'Arcade Fire',       'album': 'Funeral',                                    'year': '2004', 'genre': 'Indie Rock'},
    {'artist': 'The Strokes',       'album': 'Is This It',                                 'year': '2001', 'genre': 'Indie Rock'},
    {'artist': 'Phoebe Bridgers',   'album': 'Punisher',                                   'year': '2020', 'genre': 'Indie Folk'},
    {'artist': 'SZA',               'album': 'Ctrl',                                       'year': '2017', 'genre': 'R&B'},
    {'artist': 'Tyler the Creator', 'album': 'Igor',                                       'year': '2019', 'genre': 'Hip-Hop'},
    {'artist': 'Fiona Apple',       'album': 'Fetch the Bolt Cutters',                     'year': '2020', 'genre': 'Art Rock'},
    {'artist': 'LCD Soundsystem',   'album': 'Sound of Silver',                            'year': '2007', 'genre': 'Electronic'},
    {'artist': 'Bon Iver',          'album': 'For Emma, Forever Ago',                      'year': '2008', 'genre': 'Folk'},
    {'artist': 'Solange',           'album': 'A Seat at the Table',                        'year': '2016', 'genre': 'R&B'},
    {'artist': 'Taylor Swift',      'album': 'folklore',                                   'year': '2020', 'genre': 'Indie Pop'},
    {'artist': 'Billie Eilish',     'album': 'When We All Fall Asleep, Where Do We Go?',  'year': '2019', 'genre': 'Pop'},
    {'artist': 'Sufjan Stevens',    'album': 'Illinois',                                   'year': '2005', 'genre': 'Indie Folk'},
    {'artist': 'D Angelo',          'album': 'Voodoo',                                     'year': '2000', 'genre': 'R&B'},
    {'artist': 'Vampire Weekend',   'album': 'Father of the Bride',                        'year': '2019', 'genre': 'Indie Pop'},
    {'artist': 'Blood Orange',      'album': 'Freetown Sound',                             'year': '2016', 'genre': 'R&B'},
]


def extract_album_from_news(news_items: list[dict]) -> dict | None:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)
    headlines = '\n'.join(f"- {item['title']}" for item in news_items[:20])
    prompt = f"""Identify one specific music album release from these headlines.
Only return a result if there is a clear, specific album title by a named artist.
If no album is clearly mentioned, return the JSON value null.

Headlines:
{headlines}

Return valid JSON only:
{{"artist": "Name", "album": "Title", "year": "2026", "genre": "Genre", "context": "Brief context"}}
Or if no album: null"""

    resp = model.generate_content(prompt)
    raw = re.sub(r'^```(?:json)?\s*|\s*```$', '', resp.text.strip())
    if raw.lower() == 'null':
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def _get_reviewed_albums(index: list[dict]) -> set[str]:
    reviewed = set()
    for entry in index:
        artist = entry.get('artistName', '')
        album  = entry.get('albumName', '')
        if artist and album and entry.get('type') in ('review', 'classic-review'):
            reviewed.add(f"{artist.lower()} — {album.lower()}")
    return reviewed


def pick_classic_album(reviewed: set[str]) -> dict:
    available = [
        a for a in CLASSIC_ALBUMS
        if f"{a['artist'].lower()} — {a['album'].lower()}" not in reviewed
    ]
    return random.choice(available if available else CLASSIC_ALBUMS)
