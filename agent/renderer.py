"""
Renderer — builds a clean, responsive HTML email from the 5-section digest.
"""

import html as html_lib
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Section metadata
# ---------------------------------------------------------------------------
SECTION_META = {
    "news_highlights": {"icon": "📰", "label": "News Highlights",   "accent": "#ff4d4d"},
    "top_labs":        {"icon": "🏢", "label": "Top Labs Updates",  "accent": "#00e5a0"},
    "dev_updates":     {"icon": "🌍", "label": "Developer Updates", "accent": "#4d9fff"},
    "open_source":     {"icon": "🔓", "label": "Open Source",       "accent": "#ff9f4d"},
    "papers":          {"icon": "📄", "label": "Notable Papers",    "accent": "#d04dff"},
}

# ---------------------------------------------------------------------------
# CSS (shared across all sections)
# ---------------------------------------------------------------------------
_CSS = """
  /* Reset & base */
  body {
    margin: 0; padding: 0;
    background-color: #f0f2f5;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
                 Helvetica, Arial, sans-serif;
    color: #1a1a2e;
  }
  a { color: inherit; text-decoration: none; }
  a:hover { text-decoration: underline; }

  /* Wrapper */
  .wrapper {
    max-width: 620px;
    margin: 32px auto;
    background: #ffffff;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 24px rgba(0,0,0,0.10);
  }

  /* Header */
  .header {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    padding: 36px 32px 28px;
    text-align: center;
  }
  .header h1 { margin: 0 0 6px; font-size: 28px; font-weight: 800; color: #fff; letter-spacing: -0.5px; }
  .header .subtitle { font-size: 14px; color: #a0a8c8; margin: 0; }
  .header .date-badge {
    display: inline-block; margin-top: 12px;
    padding: 4px 14px; background: rgba(255,255,255,0.15);
    border-radius: 20px; font-size: 13px; color: #dde3ff;
  }

  /* Stats bar */
  .stats-bar {
    display: flex; flex-wrap: wrap; gap: 6px;
    justify-content: center;
    padding: 14px 24px; background: #f8f9fc;
    border-bottom: 1px solid #e8eaed;
    font-size: 12px; color: #555;
  }
  .stat-chip {
    padding: 3px 10px; border-radius: 12px;
    background: #eef0f5; font-weight: 600;
  }

  /* Section */
  .section { padding: 0 24px 8px; }
  .section-title {
    display: flex; align-items: center; gap: 8px;
    font-size: 18px; font-weight: 700;
    padding: 22px 0 10px;
    border-bottom: 2px solid;
    margin-bottom: 4px;
  }

  /* News list */
  .news-list { list-style: none; margin: 10px 0 4px; padding: 0; }
  .news-item {
    padding: 12px 0;
    border-bottom: 1px solid #f0f0f5;
    font-size: 14px; line-height: 1.6;
  }
  .news-item:last-child { border-bottom: none; }
  .news-item strong { font-size: 15px; }
  .news-source {
    display: inline-block; margin-left: 6px;
    font-size: 11px; font-weight: 600; color: #888;
    background: #f0f2f5; border-radius: 8px;
    padding: 1px 7px;
  }

  /* Item card */
  .item { padding: 16px 0 12px; border-bottom: 1px solid #f0f0f5; }
  .item:last-child { border-bottom: none; }
  .item-header { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 8px; }
  .item-title { font-size: 15px; font-weight: 700; line-height: 1.4; flex: 1; }
  .item-meta { display: flex; align-items: center; gap: 5px; flex-shrink: 0; }
  .badge {
    font-size: 10px; font-weight: 700; padding: 2px 7px;
    border-radius: 8px; text-transform: uppercase; letter-spacing: 0.4px;
    background: #1a1a2e; color: #fff;
  }
  .source-badge {
    font-size: 11px; font-weight: 600; padding: 3px 8px;
    border-radius: 10px; background: #eef0f5; color: #444; white-space: nowrap;
  }
  .item-summary { font-size: 14px; line-height: 1.6; color: #444; margin: 0 0 10px; }

  /* Why it matters callout */
  .why-box {
    padding: 10px 14px; border-radius: 6px;
    font-size: 13px; line-height: 1.55;
    border-left: 3px solid;
  }
  .why-box strong {
    display: block; margin-bottom: 3px;
    font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;
  }

  /* Empty notice */
  .empty-notice { font-size: 13px; color: #aaa; padding: 14px 0; font-style: italic; }

  /* Footer */
  .footer {
    background: #f8f9fc; padding: 22px 32px;
    text-align: center; border-top: 1px solid #e8eaed;
  }
  .footer p { margin: 0; font-size: 12px; color: #888; line-height: 1.6; }
  .footer a { color: #555; text-decoration: underline; }
"""


def _esc(s: str) -> str:
    return html_lib.escape(str(s))


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------

def _render_news_highlights(items: list) -> str:
    """Render news_highlights as 3 clean bullet points."""
    meta = SECTION_META["news_highlights"]
    accent = meta["accent"]

    lines = [
        f'<div class="section">',
        f'<div class="section-title" style="color:{accent};border-color:{accent}">'
        f'{meta["icon"]} {meta["label"]}</div>',
    ]

    if not items:
        lines.append('<p class="empty-notice">No major news today.</p>')
    else:
        lines.append('<ul class="news-list">')
        for item in items:
            headline = _esc(item.get("headline", ""))
            summary = _esc(item.get("summary", ""))
            source = _esc(item.get("source", ""))
            url = _esc(item.get("url", "#"))
            lines.append(
                f'<li class="news-item">'
                f'<strong><a href="{url}">{headline}</a></strong> &mdash; {summary}'
                f'<span class="news-source">{source}</span>'
                f'</li>'
            )
        lines.append('</ul>')

    lines.append('</div>')
    return "\n".join(lines)


def _render_section(key: str, items: list) -> str:
    """Render a standard digest section (top_labs / dev_updates / open_source / papers)."""
    meta = SECTION_META[key]
    accent = meta["accent"]
    # Derive a subtle background tint from the accent for why-box
    why_bg = accent + "18"  # 18 = ~10% opacity in hex

    lines = [
        f'<div class="section">',
        f'<div class="section-title" style="color:{accent};border-color:{accent}">'
        f'{meta["icon"]} {meta["label"]}</div>',
    ]

    if not items:
        lines.append('<p class="empty-notice">Nothing to report.</p>')
    else:
        for item in items:
            title = _esc(item.get("title", ""))
            url = _esc(item.get("url", "#"))
            summary = _esc(item.get("summary", ""))
            why = _esc(item.get("why_it_matters", ""))
            source = _esc(item.get("source", ""))
            badge = _esc(item.get("badge", ""))

            badge_html = (
                f'<span class="badge">{badge}</span>' if badge else ""
            )
            lines.append(
                f'<div class="item">'
                f'<div class="item-header">'
                f'<div class="item-title"><a href="{url}">{title}</a></div>'
                f'<div class="item-meta">{badge_html}<span class="source-badge">{source}</span></div>'
                f'</div>'
                f'<p class="item-summary">{summary}</p>'
                f'<div class="why-box" style="border-left-color:{accent};background:{why_bg}">'
                f'<strong>&#x1F4A1; Why it matters</strong>{why}'
                f'</div>'
                f'</div>'
            )

    lines.append('</div>')
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main renderer
# ---------------------------------------------------------------------------

def render_digest(digest: dict) -> str:
    """
    Render a complete HTML email from the 5-section digest dict.

    Args:
        digest: Dict produced by ``agent.summarizer.summarize_items``.
                Keys: news_highlights, top_labs, dev_updates, open_source, papers.

    Returns:
        Complete HTML string ready to be sent as an email body.
    """
    news   = digest.get("news_highlights", [])
    labs   = digest.get("top_labs", [])
    dev    = digest.get("dev_updates", [])
    oss    = digest.get("open_source", [])
    papers = digest.get("papers", [])

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%A, %B {day}, %Y").format(day=now.day)
    generated_at = now.strftime("%Y-%m-%d %H:%M UTC")

    logger.info(
        "Rendering digest: news=%d  labs=%d  dev=%d  oss=%d  papers=%d",
        len(news), len(labs), len(dev), len(oss), len(papers),
    )

    try:
        # Stats chips
        stats_html = "".join(
            f'<span class="stat-chip">{meta["icon"]} {meta["label"]}: {count}</span>'
            for (key, meta), count in zip(
                SECTION_META.items(),
                [len(news), len(labs), len(dev), len(oss), len(papers)],
            )
        )

        body = "\n".join([
            _render_news_highlights(news),
            _render_section("top_labs",   labs),
            _render_section("dev_updates", dev),
            _render_section("open_source", oss),
            _render_section("papers",      papers),
        ])

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>AI Radar — Daily Digest</title>
  <style>{_CSS}</style>
</head>
<body>
  <div class="wrapper">

    <!-- HEADER -->
    <div class="header">
      <h1>&#x1F4E1; AI Radar</h1>
      <p class="subtitle">Your curated daily digest of what matters in AI</p>
      <span class="date-badge">{_esc(date_str)}</span>
    </div>

    <!-- STATS BAR -->
    <div class="stats-bar">{stats_html}</div>

    <!-- SECTIONS -->
    {body}

    <!-- FOOTER -->
    <div class="footer">
      <p>
        Generated by <strong>AI Radar</strong> on {_esc(generated_at)}<br />
        You received this because you subscribed to the AI Radar daily digest.
      </p>
    </div>

  </div>
</body>
</html>"""

    except Exception as exc:
        logger.error("Rendering failed: %s", exc)
        html = _fallback_render(digest, date_str, generated_at)

    return html


def render_email(digest: dict) -> str:
    """Alias for render_digest — kept for backward compatibility."""
    return render_digest(digest)


# ---------------------------------------------------------------------------
# Fallback renderer (no external dependencies)
# ---------------------------------------------------------------------------

def _fallback_render(digest: dict, date_str: str, generated_at: str) -> str:
    """Plain HTML fallback used if the main renderer fails."""
    rows = ""
    for section_key, items in digest.items():
        meta = SECTION_META.get(section_key, {})
        label = meta.get("label", section_key)
        rows += f"<tr><td style='padding:8px 0'><h3>{label}</h3></td></tr>"
        for item in items:
            if section_key == "news_highlights":
                title = item.get("headline", "")
                url = item.get("url", "#")
                body_text = item.get("summary", "")
                rows += (
                    f"<tr><td style='padding:10px 0;border-bottom:1px solid #eee'>"
                    f"<strong><a href='{_esc(url)}'>{_esc(title)}</a></strong><br/>"
                    f"<small>{_esc(item.get('source', ''))}</small><br/>{_esc(body_text)}"
                    f"</td></tr>"
                )
            else:
                title = item.get("title", "")
                url = item.get("url", "#")
                rows += (
                    f"<tr><td style='padding:10px 0;border-bottom:1px solid #eee'>"
                    f"<strong><a href='{_esc(url)}'>{_esc(title)}</a></strong><br/>"
                    f"<small>{_esc(item.get('source', ''))} | {_esc(item.get('badge', ''))}</small>"
                    f"<br/><br/>{_esc(item.get('summary', ''))}<br/><br/>"
                    f"<em>Why it matters: {_esc(item.get('why_it_matters', ''))}</em>"
                    f"</td></tr>"
                )

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"/><title>AI Radar — Daily Digest</title></head>
<body style="font-family:sans-serif;max-width:620px;margin:auto;padding:20px">
  <h1 style="background:#302b63;color:#fff;padding:20px;border-radius:8px">
    AI Radar — Daily Digest<br/>
    <small style="font-size:14px;font-weight:normal">{_esc(date_str)}</small>
  </h1>
  <table width="100%" cellpadding="0" cellspacing="0">{rows}</table>
  <p style="color:#888;font-size:12px">Generated at {_esc(generated_at)}</p>
</body></html>"""
