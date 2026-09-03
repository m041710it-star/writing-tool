import streamlit as st

from utils.common import render_output, render_sidebar, render_token_count
from utils.gemini_client import generate_stream, get_api_key
from utils.usage_tracker import record_usage

render_sidebar()

st.title("🌐 翻訳")
st.caption("文章を指定した言語に、トーンやニュアンスを保ったまま翻訳します。")

LANGUAGES = [
    "英語", "日本語", "中国語（簡体字）", "中国語（繁体字）", "韓国語",
    "フランス語", "ドイツ語", "スペイン語", "ポルトガル語", "その他（自由入力）",
]

with st.form("translate_form"):
    text_input = st.text_area("翻訳したい文章", height=250)

    render_token_count(st.session_state.get("translate_usage"), "input")

    col1, col2 = st.columns(2)
    with col1:
        target_lang = st.selectbox("翻訳先の言語", LANGUAGES)
        if target_lang == "その他（自由入力）":
            target_lang = st.text_input("言語名を入力", placeholder="例：タイ語")
    with col2:
        tone = st.selectbox(
            "トーン",
            ["自然な標準表現", "ビジネス・フォーマル", "カジュアル・会話調"],
        )

    submitted = st.form_submit_button(
        "🚀 翻訳する", type="primary", disabled=not get_api_key()
    )

if not get_api_key():
    st.info("「⚙️ 設定」ページでGemini APIキーを設定すると生成できます。")

if submitted:
    if not text_input.strip():
        st.warning("翻訳したい文章を入力してください。")
    elif not target_lang:
        st.warning("翻訳先の言語を入力してください。")
    else:
        prompt = (
            f"以下の文章を{target_lang}に翻訳してください。トーンは「{tone}」でお願いします。\n\n"
            f"# 原文\n{text_input}\n\n"
            "翻訳結果のみを出力してください。原文や説明は不要です。"
        )

        system_instruction = (
            "あなたはプロの翻訳者です。直訳ではなく、対象言語として自然で、"
            "原文のニュアンスとトーンを保った翻訳を行います。"
        )

        st.divider()
        try:
            usage_holder = {}
            with st.spinner("翻訳しています..."):
                result = st.write_stream(
                    generate_stream(
                        prompt,
                        system_instruction=system_instruction,
                        temperature=0.5,
                        usage_holder=usage_holder,
                    )
                )
            st.session_state["translate_output"] = result
            st.session_state["translate_usage"] = usage_holder
            record_usage(
                "翻訳",
                usage_holder.get("prompt_tokens", 0),
                usage_holder.get("output_tokens", 0),
            )
        except RuntimeError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

if st.session_state.get("translate_output"):
    st.divider()
    render_output(
        st.session_state["translate_output"], "translation.txt", "translate_output_area"
    )
    render_token_count(st.session_state.get("translate_usage"), "output")
