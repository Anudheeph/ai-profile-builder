import streamlit as st
from dotenv import load_dotenv

from profile_builder.search import gather_sources
from profile_builder.llm import generate_profile

load_dotenv()

st.set_page_config(page_title="AI Profile Builder", layout="centered")

st.title("AI-Powered Profile Builder")
st.caption("Name + context in, structured profile with sources out. Won't invent facts it can't find.")

with st.form("profile_form"):
    name = st.text_input("Name", placeholder="Enter the name")
    context = st.text_input("Context", placeholder="Enter the context")
    submitted = st.form_submit_button("Generate Profile")

if submitted:
    if not name.strip():
        st.error("Please enter a name.")
        st.stop()

    with st.spinner("Searching Wikipedia and the web..."):
        sources = gather_sources(name, context)

    if not sources:
        st.warning("Couldn't find any public sources for this person.")
    else:
        st.success(f"Found {len(sources)} sources.")

    with st.spinner("Writing up the profile..."):
        try:
            profile_md = generate_profile(name, context, sources)
        except RuntimeError as e:
            st.error(str(e))
            st.stop()

    st.markdown("---")
    st.markdown(profile_md)

    st.download_button(
        "Download profile as Markdown",
        data=profile_md,
        file_name=f"{name.strip().lower().replace(' ', '_')}_profile.md",
        mime="text/markdown",
    )

    with st.expander("Raw sources used"):
        for s in sources:
            st.markdown(f"**[{s['id']}]** [{s['title']}]({s['url']})\n\n> {s['snippet']}")
