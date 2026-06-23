"""MusicWire — News Article Writer"""
import json
import logging
import re

log = logging.getLogger('musicwire.writer')

try:
    import anthropic
    from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, MUSICWIRE_VOICE
except ImportError as e:
    log.error("Import error: %s", e)
    raise


def write_news(news_item: dict) -> dict:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""You are the news desk at MusicWire. Write a breaking news story based on this source item.

{MUSICWIRE_VOICE}

SOURCE:
Title: {news_item['title']}
Summary: {news_item.get('summary', '')}
URL: {news_item.get('url', '')}

Return valid JSON only — no markdown, no commentary:
{{
  "title": "Concise factual headline, max 90 chars. No clickbait.",
  "deck": "Essential who/what/when in one or two sentences. Max 180 chars.",
  "body": "Full news story. 200-400 words. Inverted pyramid. No opinion. Source all claims. Use <p> tags for paragraphs. Use <em> for album/song titles.",
  "type": "news",
  "breaking": false,
  "artistName": "Primary artist name if story is artist-specific, else empty string",
  "albumName": "Album name if story is album-specific, else empty string",
  "tags": ["tag1", "tag2", "tag3"]
}}"""

    resp = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1500,
        messages=[{'role': 'user', 'content': prompt}],
    )
    raw = re.sub(r'^```(?:json)?\s*|\s*```$', '', resp.content[0].text.strip())
    return json.loads(raw)
