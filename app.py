"""Airline fuel shock monitor - entry point.

Run locally:  streamlit run app.py
Three pages: the story (story.py), Method & sources (method.py) and the News room (news.py). The first dashboard that lived here is
retired; it stays available in git under the tag v1-dashboard.
"""
import streamlit as st

st.set_page_config(page_title="Airline fuel shock monitor", layout="wide")

pages = st.navigation(
    [st.Page("story.py", title="Story", default=True),
     st.Page("method.py", title="Method & sources", url_path="method"),
     st.Page("news.py", title="News room", url_path="news")],
    position="hidden")        # the story links to the method page itself (markers, footer); no sidebar menu
pages.run()
