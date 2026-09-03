import streamlit as st

from utils.common import render_output, render_sidebar, render_token_count
from utils.gemini_client import generate_stream, get_api_key
from utils.usage_tracker import record_usage

render_sidebar()

st.title("🎨 文体変換")
st.caption("文章の口調（ビジネス敬語・カジュアル・フレンドリーなど）を変換します。")

with st.form("tone_form"):
    text_input = st.text_area("変換したい文章", height=250)

    render_token_count(st.session_state.get("tone_usage"), "input")

    target_tone = st.selectbox(
        "変換後の文章の口調",
        [
            "ビジネス敬語（フォーマル）",
            "カジュアル・フランク",
            "フレンドリー・親しみやすい",
            "SNS向け（親しみやすく短め）",
            "丁寧語（です・ます調）",
            "学術的・硬め",
        ],
    )

    keep_length = st.checkbox("元の文章の長さをできるだけ変えずに変換する", value=True)

    submitted = st.form_submit_button(
        "🚀 変換する", type="primary", disabled=not get_api_key()
    )

if not get_api_key():
    st.info("「⚙️ 設定」ページでGemini APIキーを設定すると生成できます。")

if submitted:
    if not text_input.strip():
        st.warning("文章を入力してください。")
    else:
        prompt_parts = [
            f"# 対象の文章\n{text_input}",
            f"# 変換後の文章の口調\n{target_tone}",
        ]
        if keep_length:
            prompt_parts.append("元の文章と近い分量に収めてください。")
        prompt_parts.append(
            "文章の意味内容は変えず、トーン・語調のみを変換してください。"
            "変換後の文章のみを出力してください。"
        )
        prompt = "\n\n".join(prompt_parts)

        system_instruction = (
            "あなたは日本語の文体変換が得意なライターです。"
            "意味を保ったまま指定されたトーンに自然に書き換えます。"
        )

        st.divider()
        try:
            usage_holder = {}
            with st.spinner("変換しています..."):
                result = st.write_stream(
                    generate_stream(
                        prompt,
                        system_instruction=system_instruction,
                        temperature=0.7,
                        usage_holder=usage_holder,
                    )
                )
            st.session_state["tone_output"] = result
            st.session_state["tone_usage"] = usage_holder
            record_usage(
                "文体変換",
                usage_holder.get("prompt_tokens", 0),
                usage_holder.get("output_tokens", 0),
            )
        except RuntimeError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

if st.session_state.get("tone_output"):
    st.divider()
    render_output(st.session_state["tone_output"], "tone_converted.txt", "tone_output_area")
    render_token_count(st.session_state.get("tone_usage"), "output")
