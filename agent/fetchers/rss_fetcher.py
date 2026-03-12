"""
RSS Fetcher — pulls articles from major AI blog and paper feeds.
Uses per-category lookback windows for optimal freshness.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

import feedparser

logger = logging.getLogger(__name__)

TOP_LABS_SOURCES = [
    {"url": "https://blog.google/technology/ai/rss/",         "category": "toplabs", "source": "Google AI"},
    {"url": "https://openai.com/news/rss.xml",                "category": "toplabs", "source": "OpenAI"},
    {"url": "https://www.anthropic.com/news/rss",             "category": "toplabs", "source": "Anthropic"},
    {"url": "https://engineering.fb.com/feed/",               "category": "toplabs", "source": "Meta AI"},
    {"url": "https://mistral.ai/feed/",                       "category": "toplabs", "source": "Mistral"},
    {"url": "https://deepmind.google/blog/rss/",              "category": "toplabs", "source": "DeepMind"},
]

DEV_TOOLS_SOURCES = [
    {"url": "https://huggingface.co/blog/feed.xml",                           "category": "devtools", "source": "HuggingFace"},
    {"url": "https://github.com/langchain-ai/langchain/releases.atom",        "category": "devtools", "source": "LangChain"},
    {"url": "https://github.com/vllm-project/vllm/releases.atom",            "category": "devtools", "source": "vLLM"},
    {"url": "https://github.com/ollama/ollama/releases.atom",                 "category": "devtools", "source": "Ollama"},
    {"url": "https://github.com/stanfordnlp/dspy/releases.atom",              "category": "devtools", "source": "DSPy"},
    {"url": "https://github.com/BerriAI/litellm/releases.atom",              "category": "devtools", "source": "LiteLLM"},
    {"url": "https://github.com/pydantic/pydantic-ai/releases.atom",         "category": "devtools", "source": "PydanticAI"},
]

OPENSOURCE_SOURCES = [
    {"url": "https://huggingface.co/papers/rss",            "category": "opensource", "source": "HuggingFace Papers"},
    {"url": "https://www.reddit.com/r/LocalLLaMA/hot/.rss", "category": "opensource", "source": "r/LocalLLaMA"},
]

PAPERS_SOURCES = [
    {"url": "https://rss.arxiv.org/rss/cs.AI", "category": "papers", "source": "arXiv cs.AI"},
    {"url": "https://rss.arxiv.org/rss/cs.LG", "category": "papers", "source": "arXiv cs.LG"},
    {"url": "https://rss.arxiv.org/rss/cs.CL", "category": "papers", "source": "arXiv cs.CL"},
]

NEWS_SOURCES = [
    {"url": "https://techcrunch.com/category/artificial-intelligence/feed/",  "category": "news", "source": "TechCrunch"},
    {"url": "https://venturebeat.com/feed/",                                   "category": "news", "source": "VentureBeat"},
    {"url": "https://www.theverge.com/rss/index.xml",                         "category": "news", "source": "The Verge"},
    {"url": "https://www.wired.com/feed/rss",                                 "category": "news", "source": "Wired"},
    {"url": "https://hnrss.org/newest?q=AI+LLM",                             "category": "news", "source": "Hacker News"},
    {"url": "https://hnrss.org/show?q=AI",                                   "category": "news", "source": "HN Show AI"},
]

RSS_SOURCES = TOP_LABS_SOURCES + DEV_TOOLS_SOURCES + OPENSOURCE_SOURCES + PAPERS_SOURCES + NEWS_SOURCES

# Lookback window in hours per category
CATEGORY_HOURS: dict[str, int] = {
    "toplabs":    2160,  # 90 days — ensures at least one post per company
    "devtools":     72,  # 3 days
    "opensource":   48,  # 2 days
    "papers":       48,  # 2 days
    "news":         24,  # 1 day
}


def _parse_published(entry) -> Optional[datetime]:
    """Parse the published_parsed or updated_parsed struct_time from a feed entry."""
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t is not None:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def fetch_rss_items() -> list[dict]:
    """
    Fetch recent items from all configured RSS feeds.
    Each category uses its own lookback window (see CATEGORY_HOURS).

    Returns:
        List of dicts with keys: title, url, summary, source, category, published.
    """
    now = datetime.now(timezone.utc)
    results: list[dict] = []

    for feed_cfg in RSS_SOURCES:
        feed_url = feed_cfg["url"]
        source = feed_cfg["source"]
        category = feed_cfg["category"]
        hours = CATEGORY_HOURS.get(category, 24)
        cutoff = now - timedelta(hours=hours)

        try:
            logger.info(
                "Fetching RSS feed: %s (%s) [%dh window]", source, feed_url, hours
            )
            parsed = feedparser.parse(
                feed_url,
                response_headers={"content-type": "text/xml; charset=utf-8"}
            )

            if parsed.bozo and not parsed.entries:
                print(f"   ⚠️  Malformed feed skipped: {source} — {parsed.bozo_exception}")
                continue

            if parsed.bozo and parsed.bozo_exception:
                logger.warning(
                    "Feed %s parsed with error: %s", source, parsed.bozo_exception
                )

            entries = parsed.get("entries", [])
            logger.info("  -> %d total entries in %s", len(entries), source)

            fresh_count = 0
            for entry in entries:
                pub_dt = _parse_published(entry)

                # If we can't determine a date, include the item anyway
                if pub_dt is not None and pub_dt < cutoff:
                    continue

                title = entry.get("title", "").strip()
                url = entry.get("link", "").strip()
                # Use the first available text summary field
                summary = (
                    entry.get("summary", "")
                    or entry.get("description", "")
                    or entry.get("content", [{}])[0].get("value", "")
                ).strip()

                if not title or not url:
                    continue

                item: dict = {
                    "title": title,
                    "url": url,
                    "summary": summary[:600] if summary else "",
                    "source": source,
                    "category": category,
                    "published": pub_dt.isoformat() if pub_dt else "unknown",
                }

                if category == "toplabs" and pub_dt is not None:
                    days_ago = (now - pub_dt).days
                    item["days_ago"] = days_ago
                    item["recency"] = "recent" if days_ago <= 7 else "older"

                results.append(item)
                fresh_count += 1

            logger.info("  -> %d fresh entries kept from %s", fresh_count, source)

        except Exception as exc:
            logger.error("Failed to fetch RSS feed %s (%s): %s", source, feed_url, exc)

    logger.info("RSS fetcher total: %d items", len(results))
    return results
