"""
GitHub Fetcher — retrieves the latest release for a curated list of AI repos.
Uses the public GitHub REST API; no authentication required (60 req/h limit).
Returns releases published within the last 7 days.
"""

import logging
from datetime import datetime, timezone, timedelta

import requests

logger = logging.getLogger(__name__)

GITHUB_REPOS = [
    "langchain-ai/langchain",
    "vllm-project/vllm",
    "ollama/ollama",
    "run-llama/llama_index",
    "stanfordnlp/dspy",
    "crewAIInc/crewAI",
]

GITHUB_API_BASE = "https://api.github.com/repos"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
REQUEST_TIMEOUT = 15  # seconds


def fetch_github_releases(days: int = 7) -> list[dict]:
    """
    Fetch the latest GitHub release for every repo in GITHUB_REPOS.

    Args:
        days: Only include releases published within this many days.

    Returns:
        List of dicts with keys: title, url, body, repo, published.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    results: list[dict] = []

    for repo in GITHUB_REPOS:
        url = f"{GITHUB_API_BASE}/{repo}/releases/latest"
        try:
            logger.info("Fetching latest release for %s", repo)
            response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)

            if response.status_code == 404:
                logger.warning("No releases found for %s (404)", repo)
                continue

            if response.status_code == 403:
                logger.warning(
                    "GitHub rate-limit hit while fetching %s — skipping", repo
                )
                continue

            response.raise_for_status()
            data = response.json()

            raw_pub = data.get("published_at") or data.get("created_at", "")
            try:
                pub_dt = datetime.fromisoformat(raw_pub.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pub_dt = None

            if pub_dt is not None and pub_dt < cutoff:
                logger.info(
                    "  -> %s latest release %s is older than %d days — skipped",
                    repo,
                    data.get("tag_name", ""),
                    days,
                )
                continue

            tag = data.get("tag_name", "")
            name = data.get("name", "") or tag
            html_url = data.get("html_url", "")
            body = (data.get("body") or "").strip()

            # Truncate very long release notes
            if len(body) > 800:
                body = body[:797] + "..."

            results.append(
                {
                    "title": f"{repo.split('/')[1]} {tag}: {name}".strip(": "),
                    "url": html_url,
                    "body": body,
                    "repo": repo,
                    "published": pub_dt.isoformat() if pub_dt else "unknown",
                }
            )
            logger.info(
                "  -> Kept release %s for %s (published %s)",
                tag,
                repo,
                raw_pub,
            )

        except requests.exceptions.Timeout:
            logger.error("Timeout while fetching release for %s", repo)
        except requests.exceptions.ConnectionError as exc:
            logger.error("Connection error for %s: %s", repo, exc)
        except requests.exceptions.HTTPError as exc:
            logger.error(
                "HTTP error %s while fetching %s: %s",
                exc.response.status_code,
                repo,
                exc,
            )
        except Exception as exc:
            logger.error("Unexpected error fetching release for %s: %s", repo, exc)

    logger.info("GitHub fetcher total: %d recent releases", len(results))
    return results
