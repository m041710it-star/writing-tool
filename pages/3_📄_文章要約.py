import streamlit as st

from utils.common import render_output, render_sidebar, render_token_count
from utils.gemini_client import generate_stream, get_api_key
from utils.usage_tracker import record_usage

render_sidebar()

st.title("📄 文章要約")
st.caption("長い文章を要約したり、箇条書きに整理したりします。")

source_text = ""
uploaded_file = st.file_uploader("テキストファイルをアップロード（任意）", type=["txt", "md"])
if uploaded_file is not None:
    source_text = uploaded_file.read().decode("utf-8", errors="ignore")

with st.form("summary_form"):
    text_input = st.text_area(
        "要約したい文章", value=source_text, height=300, placeholder="ここに文章を貼り付けてください"
    )

    render_token_count(st.session_state.get("summary_usage"), "input")

    col1, col2 = st.columns(2)
    with col1:
        length = st.selectbox(
            "要約の長さ",
            ["一言で（1文）", "短め（3文程度）", "標準（5〜7文程度）", "詳しめ（複数段落）"],
            index=2,
        )
    with col2:
        output_format = st.selectbox("出力形式", ["文章（段落）", "箇条書き"])

    focus = st.text_input("特に重視したい観点（任意）", placeholder="例：結論と数値データを中心に")

    submitted = st.form_submit_button(
        "🚀 要約する", type="primary", disabled=not get_api_key()
    )

if not get_api_key():
    st.info("「⚙️ 設定」ページでGemini APIキーを設定すると生成できます。")

if submitted:
    if not text_input.strip():
        st.warning("要約したい文章を入力してください。")
    else:
        prompt_parts = [
            f"# 要約対象の文章\n{text_input}",
            f"# 要約の長さ\n{length}",
            f"# 出力形式\n{output_format}",
        ]
        if focus:
            prompt_parts.append(f"# 重視する観点\n{focus}")
        prompt_parts.append(
            "原文の意味を正確に保ちながら要約してください。誇張や事実の追加はしないでください。"
        )
        prompt = "\n\n".join(prompt_parts)

        system_instruction = (
            "あなたは要点整理が得意な日本語の編集者です。"
            "原文にない情報を付け加えず、簡潔で分かりやすい要約を作成します。"
        )

        st.divider()
        try:
            usage_holder = {}
            with st.spinner("要約しています..."):
                result = st.write_stream(
                    generate_stream(
                        prompt,
                        system_instruction=system_instruction,
                        temperature=0.5,
                        usage_holder=usage_holder,
                    )
                )
            st.session_state["summary_output"] = result
            st.session_state["summary_usage"] = usage_holder
            record_usage(
                "文章要約",
                usage_holder.get("prompt_tokens", 0),
                usage_holder.get("output_tokens", 0),
            )
        except RuntimeError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

if st.session_state.get("summary_output"):
    st.divider()
    render_output(st.session_state["summary_output"], "summary.txt", "summary_output_area")
    render_token_count(st.session_state.get("summary_usage"), "output")
