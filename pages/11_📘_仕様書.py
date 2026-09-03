from pathlib import Path

import streamlit as st

from utils.common import render_sidebar

render_sidebar()

st.title("📘 仕様書")
st.caption("このアプリが現時点で持つ機能を、利用者向けにまとめたものです。")

spec_path = Path(__file__).resolve().parent.parent / "SPEC.md"
st.markdown(spec_path.read_text(encoding="utf-8"))
