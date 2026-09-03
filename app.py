import streamlit as st

st.set_page_config(
    page_title="AI ライティングツール",
    page_icon="🖋️",
    layout="wide",
)

home_page = st.Page(
    "pages/0_🏠_トップページ.py", title="トップページ", icon="🏠", default=True
)
tool_pages = [
    st.Page("pages/1_📝_ブログ記事作成.py", title="ブログ記事作成", icon="📝"),
    st.Page("pages/2_✉️_メール返信作成.py", title="メール返信作成", icon="✉️"),
    st.Page("pages/3_📄_文章要約.py", title="文章要約", icon="📄"),
    st.Page("pages/4_✏️_校正リライト.py", title="校正・リライト", icon="✏️"),
    st.Page("pages/5_🎨_文体変換.py", title="文体変換", icon="🎨"),
    st.Page("pages/6_💡_タイトル生成.py", title="タイトル生成", icon="💡"),
]
translate_page = st.Page("pages/7_🌐_翻訳.py", title="翻訳", icon="🌐")
settings_page = st.Page("pages/8_⚙️_設定.py", title="設定", icon="⚙️")
usage_page = st.Page("pages/10_📊_API利用状況.py", title="API利用状況", icon="📊")
spec_page = st.Page("pages/11_📘_仕様書.py", title="仕様書", icon="📘")
changelog_page = st.Page("pages/9_📜_変更履歴.py", title="変更履歴", icon="📜")

# サイドバーメニューに余白を入れたい箇所（トップページ/ブログ記事作成の間、
# タイトル生成/翻訳の間、翻訳/設定の間）でグループを分けている。
# st.navigation はグループの切れ目に見出し行分の余白を入れるため、
# 見出しテキスト自体は見えないよう空白文字だけのキー（重複不可なので
# 半角スペースの数を変えて区別）を使い、視覚的には余白のみを残す。
pg = st.navigation(
    {
        "": [home_page],
        " ": tool_pages,
        "  ": [translate_page],
        "   ": [settings_page, usage_page, spec_page, changelog_page],
    }
)
pg.run()
