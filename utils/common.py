"""ページ共通のUIパーツ(サイドバー設定・出力表示)。"""
import os
from typing import Optional

import streamlit as st

from utils import usage_tracker
from utils.gemini_client import FREE_TIER_DISCLAIMER, QuotaExceededError, get_api_key
from utils.models import (
    MODEL_DESCRIPTIONS,
    MODEL_LABELS,
    MODEL_OPTIONS,
    get_lighter_model,
    get_model_weight_tier,
)


def render_sidebar() -> None:
    model_label = st.sidebar.selectbox(
        "使用するモデル", list(MODEL_OPTIONS.keys()), index=0, key="gemini_model_label"
    )
    model_id = MODEL_OPTIONS[model_label]
    st.session_state.gemini_model = model_id
    st.sidebar.caption(MODEL_DESCRIPTIONS.get(model_id, ""))

    st.sidebar.divider()
    render_usage_status()
    st.sidebar.divider()

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


def _text_progress_bar(ratio: float, width: int = 8) -> str:
    ratio = max(0.0, min(ratio, 1.0))
    filled = round(ratio * width)
    return "[" + "■" * filled + "□" * (width - filled) + "]"


def render_usage_status(target=None) -> None:
    """無料枠・有料枠それぞれの利用状況を、まとめて表示する（あくまで簡易的な目安）。

    Gemini APIには残量を取得する仕組みがないため、無料枠の状態は
    「直近のAPI呼び出しで429（クォータ超過）が発生したかどうか」をもとにした
    簡易表示にとどめる。有料枠は「⚙️ 設定」ページで「有料利用に切り替えました」が
    ONの場合のみ、課金履歴に基づく進捗バー・残高目安を表示する（OFFの間は「未設定」）。
    このトグルは無料枠の状態に関わらず、いつでもユーザーの意思でON/OFFできる。
    `target` を省略するとサイドバーに表示する。`st`（本文エリア）を渡すと
    ページ本文にも同じ内容を表示できる。
    """
    if target is None:
        target = st.sidebar

    target.caption("📊 API利用状況（※簡易的な目安です）")

    last_call = usage_tracker.get_last_call_status()
    if last_call.get("status") == "quota_exceeded":
        target.caption("無料枠: ⚠️ 利用制限に達した可能性があります（目安）")
    else:
        target.caption("無料枠: ✅ 利用可能（直近でエラーなし）")

    if not usage_tracker.get_paid_mode():
        target.caption("有料枠: 未設定")
        target.page_link("pages/8_⚙️_設定.py", label="設定はこちら", icon="⚙️")
    else:
        summary = usage_tracker.compute_summary()
        if summary["total_billing_yen"] <= 0:
            target.caption("有料枠: 切り替え済み（課金履歴は未入力です）")
            target.caption(
                "「📊 API利用状況」ページの課金履歴に金額を入力すると、"
                "残高の目安が表示されます。"
            )
        else:
            ratio = summary["usage_ratio"]
            percent = min(ratio, 1.0) * 100
            bar = _text_progress_bar(ratio)
            balance_display = f"約{max(summary['balance_yen'], 0):,.0f}円分"
            target.caption(
                f"有料枠: `{bar}` {percent:.0f}%（残高目安: {balance_display}）"
            )
            if ratio >= 1.0:
                target.caption("⚠️ 残高目安を超えている可能性があります。")
            elif ratio >= 0.8:
                target.caption("残高目安が少なくなってきています。")

    target.caption(FREE_TIER_DISCLAIMER)


def render_api_error(error: Exception) -> None:
    """ページ共通のAPIエラー表示。

    `QuotaExceededError`（429）の場合は、メッセージ本文（モデル別の段階的な案内）に
    加えて、より軽量なモデルへ切り替えるボタンと「⚙️ 設定」ページへのリンクを表示する。
    それ以外のエラー（APIキー未設定など）は、従来どおりメッセージのみを表示する。
    """
    st.error(str(error))

    model = getattr(error, "model", None)
    if not isinstance(error, QuotaExceededError) or model is None:
        return
    if usage_tracker.get_paid_mode():
        return

    tier = get_model_weight_tier(model)
    lighter = get_lighter_model(model)

    if tier != "lightest" and lighter:
        lighter_label = MODEL_LABELS.get(lighter, lighter)
        if st.button(f"🍃 {lighter_label} に切り替える", key="quota_switch_lighter_model"):
            st.session_state["gemini_model_label"] = lighter_label
            st.rerun()

    st.page_link(
        "pages/8_⚙️_設定.py",
        label="⚙️ 設定ページへ（有料切り替え・課金額の入力）",
        icon="⚙️",
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
