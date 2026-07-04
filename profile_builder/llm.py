import os
import json
import requests

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are a research assistant that builds structured public \
profiles of well-known people using ONLY the numbered source excerpts you are \
given. You must never use prior/training knowledge to fill in facts.

Rules:
1. Every factual claim must be followed by the source number(s) it came from, \
in square brackets, e.g. "Born in 1967 [1][3]".
2. If a required field is not supported by any given source, write exactly: \
"Not publicly available" for that field. Do not guess or infer.
3. Be concise and factual. No flattery, no speculation, no filler.
4. Output must be valid Markdown using exactly the section headers given in \
the user prompt, in that order.
"""

REPORT_TEMPLATE = """# {name}
_{context}_

## Executive Summary
(3-4 sentence overview)

## Basic Details
- Full name:
- Nationality:
- Current role / occupation:
- Industry:
- Current City:
- Current Country:

## Biography / Summary

## Career Timeline
(chronological bullet list)

## Education

## Interests

## Net Worth

## Recent News or Public Activities

## References
(numbered list of source titles + URLs used above)
"""


def _build_user_prompt(name: str, context: str, sources: list[dict]) -> str:
    numbered_context = "\n\n".join(
        f"[{s['id']}] {s['title']}\nURL: {s['url']}\nExcerpt: {s['snippet']}"
        for s in sources
    )
    return f"""Person name: {name}
Context: {context}

Numbered sources (this is the ONLY information you may use):
{numbered_context}

Fill in this exact Markdown template, keeping every header as-is:
{REPORT_TEMPLATE}

Remember: use "Not publicly available" for anything the sources above don't \
support. Cite sources inline with [n] wherever you state a fact."""


def generate_profile(name: str, context: str, sources: list[dict]) -> str:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY not set. Get a free key at https://console.groq.com "
            "and put it in your .env file (see .env.example)."
        )

    if not sources:
        return (
            f"# {name}\n_{context}_\n\nNo public sources could be found for "
            "this person. Not publicly available for all fields."
        )

    payload = {
        "model": GROQ_MODEL,
        "temperature": 0.2,  # want this factual, not creative
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(name, context, sources)},
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    resp = requests.post(GROQ_API_URL, headers=headers, data=json.dumps(payload), timeout=60)
    resp.raise_for_status()
    data = resp.json()
    profile_md = data["choices"][0]["message"]["content"]
    
    refs = "\n".join(f"{s['id']}. [{s['title']}]({s['url']})" for s in sources)
    if "## References" not in profile_md:
        profile_md += f"\n\n## References\n{refs}\n"

    return profile_md
