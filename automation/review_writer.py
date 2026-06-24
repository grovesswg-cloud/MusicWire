"""MusicWire — Review Writer
Wire Scale: STATIC / SIGNAL / BREAKING / TRANSMISSION / FREQUENCY
"""
import json
import logging
import re

log = logging.getLogger('musicwire.reviews')

try:
    import google.generativeai as genai
    from config import GEMINI_API_KEY, GEMINI_MODEL, MUSICWIRE_VOICE
except ImportError as e:
    log.error("Import error: %s", e)
    raise

WIRE_SCALE_GUIDE = """
WIRE SCALE — use exactly one of these values:
  STATIC       — Competent. Does what it says. Average.
  SIGNAL       — Strong. A clear transmission worth hearing.
  BREAKING     — Essential. Stop what you're doing.
  TRANSMISSION — Rare. Career-defining. Alters the conversation.
  FREQUENCY    — Once in a generation. Assign sparingly.
"""


def write_review(album_info: dict) -> dict:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)
    prompt = f"""You are the reviews desk at MusicWire. Write a critical album review.

{MUSICWIRE_VOICE}
{WIRE_SCALE_GUIDE}

ALBUM:
Artist: {album_info['artist']}
Album:  {album_info['album']}
Year:   {album_info.get('year', '2026')}
Genre:  {album_info.get('genre', 'unknown')}
Context: {album_info.get('context', '')}

State a thesis. Make an argument. Assign a Wire Scale rating the review earns.

Return valid JSON only:
{{
  "title": "Review headline that states the thesis — not just 'Artist Album Review'. Max 90 chars.",
  "deck": "The thesis in two sentences. Max 180 chars.",
  "body": "Full review. 500-800 words. Opens on the album. States thesis early. Has a strong closing line. Uses <p> for paragraphs, <em> for album/song titles. Names specific tracks.",
  "type": "review",
  "breaking": false,
  "rating": "STATIC or SIGNAL or BREAKING or TRANSMISSION or FREQUENCY",
  "artistName": "{album_info['artist']}",
  "albumName": "{album_info['album']}",
  "tags": ["tag1", "tag2", "tag3"]
}}"""

    resp = model.generate_content(prompt)
    raw = re.sub(r'^```(?:json)?\s*|\s*```$', '', resp.text.strip())
    return json.loads(raw)


def write_classic_review(album_info: dict) -> dict:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)
    prompt = f"""You are the reviews desk at MusicWire. Write a retrospective reassessment of a classic album.

{MUSICWIRE_VOICE}
{WIRE_SCALE_GUIDE}

ALBUM:
Artist: {album_info['artist']}
Album:  {album_info['album']}
Year:   {album_info.get('year', '')}
Genre:  {album_info.get('genre', '')}

Consider: how the album holds up now, what it meant then, what we understand about it today that wasn't clear on release.

Return valid JSON only:
{{
  "title": "Reassessment headline. States the argument — not just 'Album Revisited'. Max 90 chars.",
  "deck": "The reassessment thesis in two sentences. Max 180 chars.",
  "body": "Full reassessment. 600-900 words. Historical context, original reception, how it reads now. Has a thesis. Uses <p> for paragraphs, <em> for album/song titles, <h2> for sections.",
  "type": "classic-review",
  "breaking": false,
  "rating": "STATIC or SIGNAL or BREAKING or TRANSMISSION or FREQUENCY",
  "artistName": "{album_info['artist']}",
  "albumName": "{album_info['album']}",
  "tags": ["reassessment", "classic"]
}}"""

    resp = model.generate_content(prompt)
    raw = re.sub(r'^```(?:json)?\s*|\s*```$', '', resp.text.strip())
    return json.loads(raw)
