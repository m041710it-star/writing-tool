import streamlit as st

from utils.common import render_sidebar

st.set_page_config(
    page_title="AI ライティングツール",
    page_icon="🖋️",
    layout="wide",
)

render_sidebar()

st.title("🖋️ AI ライティングツール")
st.caption("Gemini APIを使った個人用の文章作成アシスタント集")
st.info("💡 本アプリはGemini APIの無料枠での利用を前提としています。")

st.markdown(
    """
左のサイドバーからページを選んで使いたい機能を開いてください。
はじめに **サイドバーでGemini APIキー** を設定する必要があります
（`.env` や `.streamlit/secrets.toml` に `GEMINI_API_KEY` を設定していれば入力不要です）。
"""
)

st.divider()

tools = [
    ("📝", "ブログ記事作成", "テーマとキーワードから、構成の整ったブログ記事のたたき台を生成します。"),
    ("✉️", "メール返信作成", "受信メールと返信の要点を入力すると、トーンに合わせた返信文を作成します。"),
    ("📄", "文章要約", "長い文章を要約したり、箇条書きに変換したりします。"),
    ("✏️", "校正・リライト", "誤字脱字のチェックや、分かりやすく／簡潔に／丁寧に、といった書き換えを行います。"),
    ("🎨", "トーン変換", "文章の口調（ビジネス敬語・カジュアル・フレンドリーなど）を変換します。"),
    ("💡", "タイトル生成", "記事の内容やキーワードから、複数のタイトル案・見出し案を生成します。"),
    ("🌐", "翻訳", "文章を指定した言語に、トーンを保ったまま翻訳します。"),
]

cols = st.columns(2)
for i, (icon, name, desc) in enumerate(tools):
    with cols[i % 2]:
        with st.container(border=True):
            st.subheader(f"{icon} {name}")
            st.write(desc)

st.divider()
st.caption(
    "本ツールは個人利用向けのため、ユーザー認証やデータベースへの保存は行っていません。"
    "生成結果は各ページでダウンロードして保存してください。"
)
