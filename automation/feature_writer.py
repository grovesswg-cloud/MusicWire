"""MusicWire — Feature Writer"""
import json
import logging
import re

log = logging.getLogger('musicwire.features')

try:
    import anthropic
    from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, MUSICWIRE_VOICE
except ImportError as e:
    log.error("Import error: %s", e)
    raise


def write_feature(news_item: dict) -> dict:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""You are the features editor at MusicWire. Write a long-form reported feature.

{MUSICWIRE_VOICE}

INSPIRATION:
Title: {news_item['title']}
Summary: {news_item.get('summary', '')}

Use the inspiration as a jumping-off point. Write about the broader story, trend, artist, or industry shift it represents. State a clear thesis. Support it with reporting.

Return valid JSON only:
{{
  "title": "Feature headline, max 100 chars. Literary but clear.",
  "deck": "The argument and why it matters. Two or three sentences. Max 220 chars.",
  "body": "Full feature. 600-1000 words. Has a thesis. Develops an argument. Uses <p> for paragraphs, <h2> for section headers, <em> for album/song titles. Names all subjects.",
  "type": "feature",
  "breaking": false,
  "artistName": "Primary artist if feature is artist-focused, else empty string",
  "albumName": "Album name if relevant, else empty string",
  "secondaryArtist": "Second artist name for comparison pieces, else empty string",
  "tags": ["tag1", "tag2", "tag3"]
}}"""

    resp = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=3000,
        messages=[{'role': 'user', 'content': prompt}],
    )
    raw = re.sub(r'^```(?:json)?\s*|\s*```$', '', resp.content[0].text.strip())
    return json.loads(raw)
