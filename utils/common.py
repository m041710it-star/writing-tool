"""ページ共通のUIパーツ(サイドバー設定・出力表示)。"""
import streamlit as st

from utils.gemini_client import get_api_key

MODEL_OPTIONS = {
    "Gemini Flash（高速・バランス型／無料枠向け）": "gemini-flash-latest",
    "Gemini Flash-Lite（軽量・低コスト／無料枠向け）": "gemini-flash-lite-latest",
    "Gemini Pro（高精度・じっくり／無料枠の上限が低め）": "gemini-pro-latest",
}


def render_sidebar() -> None:
    st.sidebar.page_link("app.py", label="🏠 トップページ")
    st.sidebar.divider()

    st.sidebar.header("⚙️ 設定")

    api_key_input = st.sidebar.text_input(
        "Gemini APIキー",
        type="password",
        value=st.session_state.get("gemini_api_key", ""),
        placeholder="AIza...",
        help=(
            "環境変数 GEMINI_API_KEY (.env) や .streamlit/secrets.toml が"
            "未設定の場合はここに入力してください。ブラウザには保存されず、"
            "このセッション中のみ保持されます。"
        ),
    )
    st.session_state.gemini_api_key = api_key_input

    model_label = st.sidebar.selectbox(
        "使用するモデル", list(MODEL_OPTIONS.keys()), index=0
    )
    st.session_state.gemini_model = MODEL_OPTIONS[model_label]

    st.session_state.gemini_temperature = st.sidebar.slider(
        "創造性（temperature）",
        min_value=0.0,
        max_value=2.0,
        value=st.session_state.get("gemini_temperature", 1.0),
        step=0.1,
        help="値が高いほど自由で多様な文章に、低いほど堅実で一貫した文章になります。",
    )

    st.sidebar.divider()
    if get_api_key():
        st.sidebar.success("✅ APIキー設定済み")
    else:
        st.sidebar.warning("⚠️ APIキーが未設定です")
        st.sidebar.caption(
            "[Google AI Studio](https://aistudio.google.com/apikey) で"
            "無料のAPIキーを取得できます。"
        )


def render_output(text: str, filename: str, area_key: str) -> None:
    """生成結果を編集可能なテキストエリアとダウンロードボタンで表示する。"""
    st.text_area("生成結果（編集・コピー可）", value=text, height=350, key=area_key)
    st.download_button(
        "📥 テキストファイルをダウンロード",
        data=text,
        file_name=filename,
        mime="text/plain",
        key=f"download_{area_key}",
    )
