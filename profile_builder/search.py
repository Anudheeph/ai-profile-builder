import requests
from ddgs import DDGS

WIKI_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
WIKI_SEARCH_URL = "https://en.wikipedia.org/w/api.php"


def find_wikipedia_title(name: str) -> str | None:
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
    queries = [
        f"{name} {context} biography",
        f"{name} net worth",
        f"{name} university degree college",
        f"{name} lives in current residence city",
        f"{name} education career timeline",
        f"{name} news 2026",
    ]
    for q in queries:
        for hit in web_search(q, max_results=4):
            add(hit.get("title", ""), hit.get("href", ""), hit.get("body", ""))

    return sources
