"""ページ共通のUIパーツ(サイドバー設定・出力表示)。"""
import os
from typing import Optional

import streamlit as st

from utils import usage_tracker
from utils.gemini_client import get_api_key

MODEL_OPTIONS = {
    "Gemini Flash-Lite（軽量・低コスト／無料枠向け）": "gemini-flash-lite-latest",
    "Gemini Flash（高速・バランス型／無料枠向け）": "gemini-flash-latest",
    "Gemini Pro（高精度・じっくり／無料枠の上限が低め）": "gemini-pro-latest",
}


def render_sidebar() -> None:
    st.sidebar.header("⚙️ 設定")

    model_label = st.sidebar.selectbox(
        "使用するモデル", list(MODEL_OPTIONS.keys()), index=0
    )
    st.session_state.gemini_model = MODEL_OPTIONS[model_label]

    render_usage_progress()

    st.session_state.gemini_temperature = st.sidebar.slider(
        "創造性（表現の幅）",
        min_value=0.0,
        max_value=2.0,
        value=st.session_state.get("gemini_temperature", 1.0),
        step=0.1,
        help="値が高いほど自由で多様な文章に、低いほど堅実で一貫した文章になります。",
    )
    st.sidebar.caption("数値が高いほど、独創的で意外性のある文章になります。")

    st.sidebar.divider()
    if get_api_key():
        st.sidebar.success("✅ APIキー設定済み")
    else:
        st.sidebar.warning("⚠️ APIキーが未設定です")
        st.sidebar.caption(
            "「⚙️ 設定」ページでGemini APIキーを入力してください。"
            "[Google AI Studio](https://aistudio.google.com/apikey) で"
            "無料のAPIキーを取得できます。"
        )


def render_usage_progress(target=None) -> None:
    """課金残高に対するAPI使用量の目安を、色分けした進捗バーで表示する。

    `target` を省略するとサイドバーに表示する。`st`（本文エリア）を渡すと
    ページ本文にも同じ内容を表示できる。
    """
    if target is None:
        target = st.sidebar

    summary = usage_tracker.compute_summary()

    if summary["total_billing_yen"] <= 0:
        target.caption(
            "現在は無料枠でご利用中です。正確な利用状況は"
            "[Google AI Studio](https://aistudio.google.com/) でご確認ください。"
        )
        return

    ratio = summary["usage_ratio"]
    percent = min(ratio, 1.0) * 100

    if ratio >= 1.0:
        color = "#e53935"
    elif ratio >= 0.8:
        color = "#fb8c00"
    else:
        color = "#43a047"

    used_display = f"{summary['total_tokens']:,}"
    target_display = f"{summary['target_tokens']:,.0f}"

    target.markdown(
        f"""
<div style="margin: 4px 0 2px 0;">
  <div style="background: var(--secondary-background-color, #e0e0e0); border-radius: 6px; height: 10px; overflow: hidden;">
    <div style="width: {percent:.1f}%; background: {color}; height: 100%;"></div>
  </div>
  <div style="font-size: 0.75rem; margin-top: 4px; opacity: 0.85;">
    {used_display} トークン / {target_display} トークン（目安）
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    target.caption(
        "※この数値はアプリ内で計算した目安です。実際の請求額・残高は"
        "[Google AI Studio](https://aistudio.google.com/) や"
        "Google Cloudの公式画面でご確認ください。"
    )


def get_settings_password() -> Optional[str]:
    """設定ページの認証パスワードを取得する。優先順位: secrets.toml > 環境変数(.env)"""
    try:
        secret_value = st.secrets["SETTINGS_PASSWORD"]
        if secret_value:
            return secret_value
    except Exception:
        pass

    return os.environ.get("SETTINGS_PASSWORD")


def render_token_count(usage: Optional[dict], kind: str) -> None:
    """Geminiのレスポンスに含まれる使用トークン数を表示する。

    `kind` は "input"（入力＝プロンプト側のトークン数）または
    "output"（出力＝生成結果側のトークン数）を指定する。
    """
    if not usage:
        return
    if kind == "input":
        st.caption(f"🔢 入力トークン数: {usage.get('prompt_tokens', '―')}")
    else:
        st.caption(f"🔢 出力トークン数: {usage.get('output_tokens', '―')}")


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
