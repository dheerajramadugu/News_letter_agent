"""
Summarizer — uses Google Gemini to filter and summarise all
fetched items in a single batched API call, returning a structured
5-section digest.
"""

import json
import logging
import os
import re

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are an AI news curator for a senior AI engineer.
Your job is to filter and summarize raw items into a tight, high-signal daily digest with exactly 5 sections.

Return ONLY valid JSON, no markdown, no explanation:
{
  "news_highlights": [...],
  "top_labs": [...],
  "dev_updates": [...],
  "open_source": [...],
  "papers": [...]
}

SECTION RULES:

news_highlights (exactly 3 items):
- Pick the 3 biggest AI stories of the day from news sources (TechCrunch, VentureBeat, Verge, HN)
- Think: funding rounds, acquisitions, major launches, policy changes, anything that made headlines
- Each item has: headline (1 line), summary (1 sentence), source, url
- No "why it matters" needed here — just the news

top_labs (max 6 items, max 1 per company):
- Sources: Google, OpenAI, Anthropic, Meta, Mistral ONLY
- Always include the most recent post from each company even if older than 7 days
- If the item has recency="older" or days_ago > 7, append a note like "(posted 12 days ago)" to the title
- Keep: new model releases, major updates, new capabilities, API changes
- Discard: blog posts, opinion pieces, research previews without an actual release
- Max 1 item per company, max 6 total

dev_updates (max 4 items):
- Keep: framework releases, tool updates, API changes you can use today
- Must have a direct "you can use this today" angle
- Discard: roadmaps, partnerships, announcements without actual code or release

open_source (max 6 items):
- Keep: new open weight model releases, local inference improvements, quantization news, community benchmarks
- Must be something you can actually download and run
- Discard: closed models, pure benchmarks with no release

papers (max 3 items):
- Keep ONLY papers about: LLMs, RAG, agents, inference optimization, fine-tuning, prompting
- Discard: medical, biology, robotics, hardware-specific, purely theoretical papers with no engineering angle
- Each paper needs a clear 1-sentence "what you can do with this" takeaway

All items except news_highlights should have:
title, summary (2 sentences max), why_it_matters (1 sentence), source, url, badge (New/Update/Notable/Hot)

Be ruthless with filtering. Less is more. If an item is borderline, cut it.
"""

DIGEST_SECTIONS = ["news_highlights", "top_labs", "dev_updates", "open_source", "papers"]

NEWS_REQUIRED = {"headline", "summary", "source", "url"}
ITEM_REQUIRED = {"title", "summary", "why_it_matters", "source", "url"}
VALID_BADGES = {"New", "Update", "Notable", "Hot"}


def _build_user_message(items: list[dict]) -> str:
    """Serialise all raw items as compact JSON for the model."""
    return (
        "Here are the raw items to process:\n\n"
        + json.dumps(items, ensure_ascii=False, indent=2)
    )


def _extract_json_obj(text: str) -> dict:
    """
    Robustly extract a JSON object from the model response.
    Handles leading/trailing whitespace and optional markdown code fences.
    """
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    # Find the outermost JSON object
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in model response")

    json_str = text[start : end + 1]
    result = json.loads(json_str)
    if not isinstance(result, dict):
        raise ValueError("Parsed JSON is not an object")
    return result


def _validate_news_highlights(items: list) -> list[dict]:
    """Validate and clean news_highlights items."""
    cleaned = []
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            logger.warning("news_highlights item %d is not a dict — skipping", idx)
            continue
        missing = NEWS_REQUIRED - item.keys()
        if missing:
            logger.warning("news_highlights item %d missing %s — skipping", idx, missing)
            continue
        cleaned.append(
            {
                "headline": str(item["headline"]).strip(),
                "summary": str(item["summary"]).strip(),
                "source": str(item["source"]).strip(),
                "url": str(item["url"]).strip(),
            }
        )
    return cleaned


def _validate_section_items(section: str, items: list) -> list[dict]:
    """Validate and clean items for top_labs / dev_updates / open_source / papers."""
    cleaned = []
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            logger.warning("%s item %d is not a dict — skipping", section, idx)
            continue
        missing = ITEM_REQUIRED - item.keys()
        if missing:
            logger.warning("%s item %d missing %s — skipping", section, idx, missing)
            continue
        badge = str(item.get("badge", "Notable")).strip()
        if badge not in VALID_BADGES:
            badge = "Notable"
        cleaned.append(
            {
                "title": str(item["title"]).strip(),
                "url": str(item["url"]).strip(),
                "summary": str(item["summary"]).strip(),
                "why_it_matters": str(item["why_it_matters"]).strip(),
                "source": str(item["source"]).strip(),
                "badge": badge,
            }
        )
    return cleaned


def summarize_items(all_items: list[dict]) -> dict:
    """
    Filter and summarise a flat list of raw items using Gemini.

    Args:
        all_items: Combined list from RSS and GitHub fetchers.

    Returns:
        Dict with keys: news_highlights, top_labs, dev_updates, open_source, papers.
        On failure returns an empty dict (errors are logged).
    """
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        logger.error("GEMINI_API_KEY is not set — cannot summarise.")
        return {}

    if not all_items:
        logger.warning("No items passed to summarizer — skipping API call.")
        return {}

    logger.info("Summarizing %d raw items via Gemini …", len(all_items))

    try:
        client = genai.Client(api_key=api_key)
        user_message = _build_user_message(all_items)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
            ),
        )
        raw_text = response.text or ""

        logger.debug("Raw Gemini response (first 500 chars): %s", raw_text[:500])

    except Exception as exc:
        logger.error("Gemini API call failed: %s", exc)
        return {}

    # Parse the JSON response
    try:
        digest_raw = _extract_json_obj(raw_text)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.error("Failed to parse Gemini JSON response: %s", exc)
        logger.debug("Full raw response:\n%s", raw_text)
        return {}

    # Validate each section
    digest: dict[str, list] = {}

    for section in DIGEST_SECTIONS:
        raw_section = digest_raw.get(section, [])
        if not isinstance(raw_section, list):
            logger.warning("Section '%s' is not a list — using empty list", section)
            raw_section = []

        if section == "news_highlights":
            digest[section] = _validate_news_highlights(raw_section)
        else:
            digest[section] = _validate_section_items(section, raw_section)

        logger.info(
            "Section '%s': %d valid items (from %d raw)",
            section,
            len(digest[section]),
            len(raw_section),
        )

    total = sum(len(v) for v in digest.values())
    logger.info("Summarizer produced %d valid items total across all sections.", total)
    return digest
