import streamlit as st

from utils import usage_tracker
from utils.common import get_settings_password, render_sidebar
from utils.gemini_client import get_api_key

render_sidebar()

st.title("⚙️ 設定")

correct_password = get_settings_password()

if not correct_password:
    st.error(
        "SETTINGS_PASSWORD が設定されていないため、このページは利用できません。"
        "`.env` や `.streamlit/secrets.toml` に SETTINGS_PASSWORD を設定してください。"
    )
    st.stop()

if not st.session_state.get("settings_authenticated"):
    st.caption("このページはパスワードで保護されています。")
    with st.form("settings_login_form"):
        password_input = st.text_input("パスワード", type="password")
        submitted = st.form_submit_button("ログイン")

    if submitted:
        if password_input == correct_password:
            st.session_state.settings_authenticated = True
            st.rerun()
        else:
            st.error("パスワードが正しくありません。")

    st.stop()

st.caption("アプリ全体で使うGemini APIキーを設定します。")

st.divider()

st.subheader("Gemini APIキー")

api_key_input = st.text_input(
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

if get_api_key():
    st.success("✅ APIキー設定済み")
else:
    st.warning("⚠️ APIキーが未設定です")
    st.caption(
        "[Google AI Studio](https://aistudio.google.com/apikey) で"
        "無料のAPIキーを取得できます。"
    )

st.divider()

st.subheader("課金モード")

current_paid_mode = usage_tracker.get_paid_mode()
paid_mode_input = st.toggle(
    "有料利用に切り替えました",
    value=current_paid_mode,
    help=(
        "Google Cloud側で実際に有料アカウントへ切り替えた後にONにしてください。"
        "ONにすると「📊 API利用状況」ページの課金履歴の入力欄・進捗バー・"
        "残高目安の表示が有効になります。"
    ),
)
if paid_mode_input != current_paid_mode:
    usage_tracker.set_paid_mode(paid_mode_input)
    st.rerun()

if paid_mode_input:
    st.caption("✅ 現在は「有料利用中」として扱われています。")
else:
    st.caption("🆓 現在は「無料枠を利用中」として扱われています（デフォルト）。")
