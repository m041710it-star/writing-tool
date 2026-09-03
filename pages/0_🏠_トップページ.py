import streamlit as st

from utils.common import render_sidebar

render_sidebar()

CAT_ICON = """<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor"
     stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"
     style="flex: 0 0 auto; opacity: 0.75; margin-top: 2px;">
  <path d="M4 10 L6 4 L9 8" />
  <path d="M20 10 L18 4 L15 8" />
  <circle cx="12" cy="13" r="7" />
  <circle cx="9.3" cy="12" r="0.6" fill="currentColor" stroke="none" />
  <circle cx="14.7" cy="12" r="0.6" fill="currentColor" stroke="none" />
  <path d="M12 14.2 L11.3 15 L12.7 15 Z" fill="currentColor" stroke="none" />
  <path d="M9 15.6 Q12 17.4 15 15.6" />
  <path d="M2.5 12 L7 12.8" />
  <path d="M2.5 14.6 L7 13.7" />
  <path d="M21.5 12 L17 12.8" />
  <path d="M21.5 14.6 L17 13.7" />
</svg>"""

st.title("🖋️🐱 AI ライティングツール")
st.caption("Gemini APIを使った個人用の文章作成アシスタント集")

st.markdown(
    "にゃんとも心強い、日本語ライティングのお供です🐾 "
    "このツールは個人利用向けのため、ユーザー認証やデータベースへの保存は行っていません。"
    "生成結果は各ページでダウンロードして保存してください。"
)

st.divider()

st.subheader("😻 使える機能")

tools = [
    ("ブログ記事作成", "テーマとキーワードから、構成の整ったブログ記事のたたき台を生成します。"),
    ("メール返信作成", "受信メールと返信の要点を入力すると、トーンに合わせた返信文を作成します。"),
    ("文章要約", "長い文章を要約したり、箇条書きに変換したりします。"),
    ("校正・リライト", "誤字脱字のチェックや、分かりやすく／簡潔に／丁寧に、といった書き換えを行います。"),
    ("文体変換", "文章の口調（ビジネス敬語・カジュアル・フレンドリーなど）を変換します。"),
    ("タイトル生成", "記事の内容やキーワードから、複数のタイトル案・見出し案を生成します。"),
    ("翻訳", "文章を指定した言語に、トーンを保ったまま翻訳します。"),
]

tools_html = "\n".join(
    f'<div style="display:flex; align-items:flex-start; gap:10px; margin:12px 0;">'
    f'{CAT_ICON}'
    f'<div><strong>{name}</strong><br>'
    f'<span style="opacity:0.85;">{desc}</span></div>'
    f"</div>"
    for name, desc in tools
)
st.markdown(tools_html, unsafe_allow_html=True)

st.divider()

st.markdown("左のサイドバーからページを選んで、使いたい機能を開いてください🐾")
