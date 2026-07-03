# Terminal version of the same thing app.py does.
# Usage: python cli.py "Satya Nadella" "CEO of Microsoft"

import sys
import os
from dotenv import load_dotenv

from profile_builder.search import gather_sources
from profile_builder.llm import generate_profile

load_dotenv()


def slugify(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def main():
    if len(sys.argv) < 3:
        print('Usage: python cli.py "<Name>" "<Context>"')
        sys.exit(1)

    name = sys.argv[1]
    context = sys.argv[2]

    print(f"Gathering public sources for '{name}' ({context})...")
    sources = gather_sources(name, context)
    print(f"Found {len(sources)} sources. Generating profile with Groq/Llama 3.3...")

    profile_md = generate_profile(name, context, sources)

    os.makedirs("sample_output", exist_ok=True)
    out_path = os.path.join("sample_output", f"{slugify(name)}_profile.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(profile_md)

    print(f"\nSaved to {out_path}\n")
    print(profile_md)


if __name__ == "__main__":
    main()
