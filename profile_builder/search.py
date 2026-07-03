# Wikipedia + DuckDuckGo, no API keys needed for either.
# Everything ends up as one flat list of numbered sources that gets
# passed to the LLM later, so it can cite what it's looking at instead
# of just making stuff up.

import requests
from ddgs import DDGS

WIKI_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
WIKI_SEARCH_URL = "https://en.wikipedia.org/w/api.php"


def find_wikipedia_title(name: str) -> str | None:
    # Wikipedia's summary endpoint needs an exact article title, and people
    # rarely type the exact title, so search first to resolve "satya nadella"
    # -> "Satya Nadella" (or handle typos/nicknames).
    params = {
        "action": "query",
        "list": "search",
        "srsearch": name,
        "format": "json",
        "srlimit": 1,
    }
    try:
        resp = requests.get(WIKI_SEARCH_URL, params=params, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("query", {}).get("search", [])
        if results:
            return results[0]["title"]
    except requests.RequestException:
        pass
    return None


def get_wikipedia_summary(name: str) -> dict | None:
    title = find_wikipedia_title(name)
    if not title:
        return None

    url = WIKI_SUMMARY_URL.format(title=title.replace(" ", "_"))
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
    except requests.RequestException:
        return None

    # disambiguation pages (e.g. searching a common name) aren't useful here
    if data.get("type") == "disambiguation":
        return None

    return {
        "title": data.get("title"),
        "description": data.get("description"),
        "extract": data.get("extract"),
        "url": data.get("content_urls", {}).get("desktop", {}).get("page"),
    }


def web_search(query: str, max_results: int = 5) -> list[dict]:
    try:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results))
    except Exception:
        # ddgs occasionally rate-limits or times out. Rather than let one
        # bad query kill the whole run, just skip it — the profile will
        # have fewer sources for that particular field, that's it.
        return []


def gather_sources(name: str, context: str) -> list[dict]:
    sources: list[dict] = []
    seen_urls: set[str] = set()

    def add(title: str, url: str, snippet: str):
        if not url or url in seen_urls:
            return
        seen_urls.add(url)
        sources.append(
            {"id": len(sources) + 1, "title": title, "url": url, "snippet": snippet}
        )

    wiki = get_wikipedia_summary(name)
    if wiki:
        add(wiki["title"], wiki["url"], wiki["extract"] or "")

    # these four cover most of what the assignment template asks for —
    # wikipedia alone almost never has net worth or anything recent
    queries = [
        f"{name} {context} biography",
        f"{name} net worth",
        f"{name} education career timeline",
        f"{name} news 2026",
    ]
    for q in queries:
        for hit in web_search(q, max_results=4):
            add(hit.get("title", ""), hit.get("href", ""), hit.get("body", ""))

    return sources
