from pathlib import Path

import streamlit as st

from utils.common import render_sidebar

render_sidebar()

st.title("📜 変更履歴")

changelog_path = Path(__file__).resolve().parent.parent / "CHANGELOG.md"
st.markdown(changelog_path.read_text(encoding="utf-8"))
