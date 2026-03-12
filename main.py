"""
main.py — Orchestrator for the AI Radar Daily Digest Agent.

Usage:
    python main.py            # Fetch, summarise, and send the email
    python main.py --test     # Fetch, summarise, and save output/preview.html
                              # (no email is sent)
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Force UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load .env as early as possible so all submodules see the vars
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("ai_radar")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _print_section(title: str) -> None:
    width = 60
    print(f"\n{'─' * width}")
    print(f"  {title}")
    print(f"{'─' * width}")


def _print_fetch_summary(
    rss_items: list,
    github_items: list,
    summarised: dict,
) -> None:
    _print_section("Fetch summary")
    print(f"  RSS articles   : {len(rss_items)}")
    print(f"  GitHub releases: {len(github_items)}")
    print(f"  Total raw items: {len(rss_items) + len(github_items)}")
    total = sum(len(v) for v in summarised.values()) if summarised else 0
    print(f"  After filtering: {total}")
    if summarised:
        print(f"  📰 News:        {len(summarised.get('news_highlights', []))}")
        print(f"  🏢 Top Labs:    {len(summarised.get('top_labs', []))}")
        print(f"  🌍 Dev Updates: {len(summarised.get('dev_updates', []))}")
        print(f"  🔓 Open Source: {len(summarised.get('open_source', []))}")
        print(f"  📄 Papers:      {len(summarised.get('papers', []))}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="AI Radar — daily AI ecosystem digest agent."
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Save rendered HTML to output/preview.html instead of sending email.",
    )
    args = parser.parse_args()

    start_time = datetime.now(timezone.utc)
    _print_section(f"AI Radar — {'TEST MODE' if args.test else 'LIVE MODE'}")
    print(f"  Started at {start_time.strftime('%Y-%m-%d %H:%M UTC')}")

    # ------------------------------------------------------------------ #
    # Step 1 — Fetch                                                       #
    # ------------------------------------------------------------------ #
    _print_section("Step 1 / 4 — Fetching data sources")

    print("  [1a] Fetching RSS feeds …")
    from agent.fetchers.rss_fetcher import fetch_rss_items
    rss_items = fetch_rss_items()
    print(f"       Done — {len(rss_items)} items")

    print("  [1b] Fetching GitHub releases …")
    from agent.fetchers.github_fetcher import fetch_github_releases
    github_items = fetch_github_releases()
    print(f"       Done — {len(github_items)} releases")

    all_items = rss_items + github_items
    print(f"\n  Total raw items: {len(all_items)}")

    if not all_items:
        logger.warning("No items fetched from any source. Exiting.")
        sys.exit(0)

    # ------------------------------------------------------------------ #
    # Step 2 — Summarise                                                   #
    # ------------------------------------------------------------------ #
    _print_section("Step 2 / 4 — Summarising with Gemini 1.5 Flash")
    print("  Calling Gemini API (single batched request) …")

    from agent.summarizer import summarize_items
    summarised = summarize_items(all_items)

    if not summarised:
        logger.error("Summarizer returned no items. Cannot render or send digest.")
        sys.exit(1)

    total_items = sum(len(v) for v in summarised.values())
    print(f"  Done — {total_items} items after AI filtering.")
    print(f"  📰 News:        {len(summarised.get('news_highlights', []))}")
    print(f"  🏢 Top Labs:    {len(summarised.get('top_labs', []))}")
    print(f"  🌍 Dev Updates: {len(summarised.get('dev_updates', []))}")
    print(f"  🔓 Open Source: {len(summarised.get('open_source', []))}")
    print(f"  📄 Papers:      {len(summarised.get('papers', []))}")

    # ------------------------------------------------------------------ #
    # Step 3 — Render                                                      #
    # ------------------------------------------------------------------ #
    _print_section("Step 3 / 4 — Rendering HTML email")

    from agent.renderer import render_email
    html = render_email(summarised)
    print(f"  Done — {len(html):,} characters of HTML generated.")

    # ------------------------------------------------------------------ #
    # Step 4a — TEST: save to file                                         #
    # ------------------------------------------------------------------ #
    if args.test:
        _print_section("Step 4 / 4 — Saving preview (test mode)")
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        preview_path = output_dir / "preview.html"

        try:
            preview_path.write_text(html, encoding="utf-8")
            print(f"  Saved: {preview_path.resolve()}")
        except OSError as exc:
            logger.error("Could not save preview file: %s", exc)
            sys.exit(1)

        # Print full fetch summary in test mode
        _print_fetch_summary(rss_items, github_items, summarised)

        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        print(f"\n  All done in {duration:.1f}s  (test mode — no email sent)")
        return

    # ------------------------------------------------------------------ #
    # Step 4b — LIVE: send email                                           #
    # ------------------------------------------------------------------ #
    _print_section("Step 4 / 4 — Sending email via Gmail")

    from agent.notifier import send_email
    success = send_email(html)

    if success:
        print("  Email sent successfully.")
    else:
        logger.error("Failed to send email.")
        sys.exit(1)

    duration = (datetime.now(timezone.utc) - start_time).total_seconds()
    print(f"\n  All done in {duration:.1f}s")


if __name__ == "__main__":
    main()
