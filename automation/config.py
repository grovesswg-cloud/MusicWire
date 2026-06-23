"""MusicWire Automation — Configuration"""
import os
from pathlib import Path

ROOT_DIR      = Path(__file__).parent.parent
SITE_DIR      = ROOT_DIR / 'site'
ARTICLES_DIR  = SITE_DIR / 'articles'
SECTIONS_DIR  = SITE_DIR / 'sections'
API_DIR       = SITE_DIR / 'api'
ARTICLES_JSON = API_DIR / 'articles.json'

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
LASTFM_API_KEY    = os.getenv('LASTFM_API_KEY', '')
NEWS_API_KEY      = os.getenv('NEWS_API_KEY', '')

PUBLISH_TIMES_UTC    = ['06:00', '09:00', '12:00', '15:00', '18:00', '21:00']
MAX_NEWS_PER_DAY     = 6
MAX_REVIEWS_PER_DAY  = 3
MAX_FEATURES_PER_DAY = 2

ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-6')

RSS_FEEDS = [
    'https://www.rollingstone.com/music/music-news/feed/',
    'https://www.nme.com/news/music/feed',
    'https://consequence.net/feed/',
    'https://www.theguardian.com/music/rss',
    'https://www.billboard.com/feed/',
    'https://hypebeast.com/music/feed',
    'https://stereogum.com/feed/',
    'https://uproxx.com/music/feed/',
    'https://www.complex.com/music/rss',
]

WIRE_SCALE = ['STATIC', 'SIGNAL', 'BREAKING', 'TRANSMISSION', 'FREQUENCY']

MUSICWIRE_VOICE = """
MusicWire is an independent online music publication. Voice: Direct. Credible. Never cute. Always on record.

THE FIVE PRINCIPLES:
1. NAME NAMES. No anonymous sources. If you can't name them, don't quote them.
2. STATE THE THESIS. Every piece needs a central argument. 'This album is good' is not a thesis.
3. NUMBERS NEED CONTEXT. Chart positions and streaming figures require explanation of what they mean.
4. DISTINGUISH FACT FROM OPINION. News is news. Criticism is criticism. Label both clearly.
5. CORRECT VISIBLY. If wrong, say so at the top of the piece with the date.

MUSICWIRE WRITES LIKE THIS:
- News lede: "Universal Music Group confirmed Thursday it will acquire Concord Music in a deal valued at $1.8 billion, the largest label consolidation in a decade."
- Review opener: "The first thing you notice is the silence. Then the kick drum arrives and doesn't leave."
- Feature lede: "Three months after the tour ended, the venues are still arguing about who gets the deposit back."

MUSICWIRE NEVER WRITES LIKE THIS:
- Fan copy: "This banger goes absolutely HARD and the stans are eating it up!!"
- Vague: "The production is quite interesting in many ways."
- PR speak: "The artist has crafted a sonically immersive journey that resonates deeply."
- Hedging: "Some might argue, at least in certain circles, that..."

STYLE RULES:
- Dates: 28 June 2026 (day month year, no ordinals)
- Album titles: italicised with <em> tags
- Numbers: spell out one through ten, numerals for 11 and above
- Always numerals for chart positions
- No courtesy titles (Mr, Ms, Dr) unless germane to the story
- First name on second reference
"""
