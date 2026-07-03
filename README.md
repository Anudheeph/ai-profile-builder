# AI-Powered Profile Builder

Give it a name and a bit of context (e.g. "Satya Nadella" / "CEO of Microsoft") and it pulls together a structured public profile — bio, career timeline, education, net worth, recent news — with sources for every claim.

## How it works

There are two stages, and I kept them as separate files on purpose so I could test/debug them independently.

**1. Search (`profile_builder/search.py`)**
First it hits Wikipedia's REST API for a reliable base summary. Then it runs a few DuckDuckGo searches to fill in what Wikipedia usually doesn't have — net worth figures, recent news, education details. Everything gets collected into one numbered list of sources (title, url, snippet), with duplicate URLs dropped.

**2. Generation (`profile_builder/llm.py`)**
That numbered source list gets handed to Llama 3.3 70B on Groq (free tier, no card needed) with a prompt that's fairly strict about two things:
- only use what's in the sources, nothing from the model's own training data
- cite every fact with the source number it came from, and if a field just isn't covered by anything I retrieved, say "Not publicly available" instead of making something up

That second point was the main thing I was worried about with this assignment — it's easy to build something that produces a confident-looking profile that's half invented. Forcing citations and giving the model an explicit "I don't know" option was the fix.

**On "agent" vs. pipeline:** this is a fixed pipeline, not an autonomous agent — it always runs the same steps in the same order (Wikipedia, then four fixed search queries, then one LLM call to write it up). The model never decides what to search for or whether it has enough information. I chose that on purpose given the timeline: it's predictable and easy to debug, versus a tool-calling loop where the LLM drives its own searches, which is more impressive when it works but has a lot more that can go wrong. A natural next step would be giving the model a search tool and letting it decide when it's done.

**A real thing I noticed while testing:** I ran the exact same input ("Satya Nadella" / "CEO of Microsoft") twice — once from the CLI, once from the Streamlit UI — and got different results for the Education field. One run confidently said "Mangalore University, 1988," which is wrong (his actual degrees are from Manipal Institute of Technology, University of Wisconsin-Milwaukee, and University of Chicago). The other run correctly said "Not publicly available." Same code, same prompt, different outcome, because `temperature=0.2` isn't `0` and DuckDuckGo doesn't return identical results every time. The bigger lesson: the citation system stops the model from inventing facts out of nowhere, but it can't protect against a source that's already wrong — in the bad run, "Mangalore University" was traced to a real search result, just an inaccurate one. The model was faithfully wrong, not hallucinating.

## Running it

```bash
python -m venv venv
source venv/bin/activate      # venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env          # then paste a free Groq key into it (console.groq.com)
```

Streamlit UI:
```bash
streamlit run app.py
```

Or from the terminal:
```bash
python cli.py "Satya Nadella" "CEO of Microsoft"
```
This writes the result to `sample_output/` and also prints it.

## Project layout

```
app.py                              streamlit UI
cli.py                              same thing, terminal version
profile_builder/search.py           wikipedia + duckduckgo, returns numbered sources
profile_builder/llm.py              prompt + groq call, returns markdown
sample_output/satya_nadella_profile.md
requirements.txt
.env.example
```

## Things that don't work perfectly

- DuckDuckGo's free search sometimes rate-limits after a bunch of queries back to back — the code just returns fewer sources when that happens instead of crashing, so worst case the profile has more "not publicly available" fields, not an error.
- Net worth and "recent" news are only as current as whatever's indexed on the day you run it. There's no live financial feed here.
- For people without much of a public footprint the profile will mostly say "not publicly available," which is correct behavior, just not exciting to look at.

## If I had more time

I'd add a second pass where the model checks its own draft for any claim missing a citation and flags it, and probably a local cache so re-running the same name twice doesn't re-search everything. Didn't get to either given the deadline.
