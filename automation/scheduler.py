#!/usr/bin/env python3
"""MusicWire Automation — Scheduler & Entry Point

Run modes:
  python scheduler.py --run-now                        Publish one news story (default)
  python scheduler.py --run-now --type feature         Publish a feature
  python scheduler.py --run-now --type review          Publish a current album review
  python scheduler.py --run-now --type classic-review  Publish a classic album reassessment
  python scheduler.py                                  Persistent daemon (local use)
"""
import argparse
import logging
import sys

from config import PUBLISH_TIMES_UTC, MAX_NEWS_PER_DAY, MAX_REVIEWS_PER_DAY, MAX_FEATURES_PER_DAY
from news_fetcher import get_trending_music_news
from article_writer import write_news
from feature_writer import write_feature
from review_writer import write_review, write_classic_review
from album_finder import extract_album_from_news, pick_classic_album, _get_reviewed_albums
from image_sourcer import get_article_images
from publisher import publish_article, load_index, is_duplicate, count_today, count_today_by_type

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  [MUSICWIRE]  %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
log = logging.getLogger('musicwire')


def _check_key() -> bool:
    from config import ANTHROPIC_API_KEY
    if not ANTHROPIC_API_KEY:
        log.error("ANTHROPIC_API_KEY not set. Add it as a GitHub Actions secret.")
        return False
    return True


def news_cycle() -> bool:
    log.info("─── News cycle ─────────────────────────────────────────────")
    try:
        if not _check_key(): return False
        index = load_index()
        n = count_today(index)
        log.info("News today: %d / %d", n, MAX_NEWS_PER_DAY)
        if n >= MAX_NEWS_PER_DAY: log.info("Daily limit reached."); return False
        items = get_trending_music_news()
        if not items: log.warning("No news fetched."); return False
        selected = next((i for i in items if not is_duplicate(i['title'], index)), None)
        if not selected: log.warning("All stories already published."); return False
        log.info("Selected: %s", selected['title'][:80])
        data = write_news(selected)
        images = get_article_images(data)
        log.info("Images sourced: %d", len(images))
        entry = publish_article(data, images)
        log.info("Published: %s", entry['url'])
        return True
    except Exception as exc:
        log.error("News cycle failed: %s", exc, exc_info=True)
        return False


def feature_cycle() -> bool:
    log.info("─── Feature cycle ──────────────────────────────────────────")
    try:
        if not _check_key(): return False
        index = load_index()
        n = count_today_by_type(index, 'feature')
        log.info("Features today: %d / %d", n, MAX_FEATURES_PER_DAY)
        if n >= MAX_FEATURES_PER_DAY: log.info("Daily limit reached."); return False
        items = get_trending_music_news()
        if not items: log.warning("No news for feature inspiration."); return False
        selected = next((i for i in items if not is_duplicate(i['title'], index)), None)
        if not selected: log.warning("No fresh news for feature."); return False
        log.info("Writing feature from: %s", selected['title'][:80])
        data = write_feature(selected)
        images = get_article_images(data)
        entry = publish_article(data, images)
        log.info("Published feature: %s", entry['url'])
        return True
    except Exception as exc:
        log.error("Feature cycle failed: %s", exc, exc_info=True)
        return False


def review_cycle() -> bool:
    log.info("─── Review cycle ───────────────────────────────────────────")
    try:
        if not _check_key(): return False
        index = load_index()
        n = count_today_by_type(index, 'review')
        log.info("Reviews today: %d / %d", n, MAX_REVIEWS_PER_DAY)
        if n >= MAX_REVIEWS_PER_DAY: log.info("Daily limit reached."); return False
        items = get_trending_music_news()
        if not items: log.warning("No news to source albums from."); return False
        reviewed = _get_reviewed_albums(index)
        album_info = extract_album_from_news(items)
        if not album_info: log.warning("No album identified from news."); return False
        log.info("Reviewing: %s — %s", album_info['artist'], album_info['album'])
        data = write_review(album_info)
        log.info("Rating: %s", data.get('rating',''))
        images = get_article_images(data)
        entry = publish_article(data, images)
        log.info("Published review: %s", entry['url'])
        return True
    except Exception as exc:
        log.error("Review cycle failed: %s", exc, exc_info=True)
        return False


def classic_review_cycle() -> bool:
    log.info("─── Classic review cycle ────────────────────────────────────")
    try:
        if not _check_key(): return False
        index = load_index()
        reviewed = _get_reviewed_albums(index)
        album_info = pick_classic_album(reviewed)
        log.info("Selected: %s — %s (%s)", album_info['artist'], album_info['album'], album_info.get('year',''))
        data = write_classic_review(album_info)
        log.info("Rating: %s", data.get('rating',''))
        images = get_article_images(data)
        entry = publish_article(data, images)
        log.info("Published classic review: %s", entry['url'])
        return True
    except Exception as exc:
        log.error("Classic review cycle failed: %s", exc, exc_info=True)
        return False


def run_daemon() -> None:
    try:
        import schedule
    except ImportError:
        log.error("'schedule' not installed. Run: pip install schedule")
        sys.exit(1)
    log.info("MusicWire Scheduler — UTC times: %s", ', '.join(PUBLISH_TIMES_UTC))
    for t in PUBLISH_TIMES_UTC:
        schedule.every().day.at(t).do(news_cycle)
    import time
    while True:
        schedule.run_pending()
        time.sleep(30)


def main() -> None:
    parser = argparse.ArgumentParser(description='MusicWire Automated Publisher')
    parser.add_argument('--run-now', action='store_true')
    parser.add_argument('--type', default='news',
                        choices=['news', 'feature', 'review', 'classic-review'])
    args = parser.parse_args()
    if args.run_now:
        {'news': news_cycle, 'feature': feature_cycle,
         'review': review_cycle, 'classic-review': classic_review_cycle}[args.type]()
        sys.exit(0)
    else:
        run_daemon()


if __name__ == '__main__':
    main()
