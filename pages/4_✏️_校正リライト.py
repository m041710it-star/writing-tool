import streamlit as st

from utils.common import render_api_error, render_output, render_sidebar, render_token_count
from utils.gemini_client import generate_stream, get_api_key
from utils.usage_tracker import record_usage

render_sidebar()

st.title("✏️ 校正・リライト")
st.caption("誤字脱字のチェックや、分かりやすく／簡潔に／丁寧に、といった書き換えを行います。")

with st.form("proofread_form"):
    text_input = st.text_area("校正・リライトしたい文章", height=300)

    render_token_count(st.session_state.get("proofread_usage"), "input")

    mode = st.selectbox(
        "モード",
        [
            "誤字脱字・文法チェックのみ（大きく書き換えない）",
            "分かりやすく言い換える",
            "簡潔にする",
            "丁寧・フォーマルにする",
            "説得力を強める",
        ],
    )

    show_explanation = st.checkbox("修正点の説明も出力する", value=True)

    check_items_input = st.text_area(
        "チェック項目（1行に1項目、任意）",
        height=120,
        placeholder="例：\n・敬語の誤りがないか\n・数字の表記ゆれがないか\n・専門用語に説明を添えているか",
        help="Googleスプレッドシートなどで管理しているチェックリストをそのまま貼り付けられます。"
        "入力すると、この項目に沿って文章をチェックします。空欄の場合は誤字脱字などの標準的なチェックのみ行います。",
        key="proofread_check_items",
    )

    submitted = st.form_submit_button(
        "🚀 実行する", type="primary", disabled=not get_api_key()
    )

if not get_api_key():
    st.info("「⚙️ 設定」ページでGemini APIキーを設定すると生成できます。")

if submitted:
    if not text_input.strip():
        st.warning("文章を入力してください。")
    else:
        check_items = [
            line.strip() for line in check_items_input.splitlines() if line.strip()
        ]

        prompt_parts = [
            f"# 対象の文章\n{text_input}",
            f"# モード\n{mode}",
        ]

        if check_items:
            items_text = "\n".join(f"{i + 1}. {item}" for i, item in enumerate(check_items))
            prompt_parts.append(f"# チェック項目\n{items_text}")
            prompt_parts.append(
                "出力は「## 修正後の文章」と「## チェック項目ごとの指摘」の2セクションに分けてください。"
                "「## チェック項目ごとの指摘」では、上記のチェック項目それぞれについて番号を対応させ、"
                "該当箇所があれば具体的な指摘を、問題がなければ「問題なし」と明記してください。"
                "チェック項目に含まれない一般的な誤字脱字も見つかった場合は、末尾に「## その他の気づき」として追記してください。"
            )
        elif show_explanation:
            prompt_parts.append(
                "出力は「## 修正後の文章」と「## 主な修正点」の2セクションに分けてください。"
                "修正点は箇条書きで、何をどう変えたか簡潔に説明してください。"
            )
        else:
            prompt_parts.append("修正後の文章のみを出力してください。説明は不要です。")
        prompt = "\n\n".join(prompt_parts)

        system_instruction = (
            "あなたは日本語の校正・編集のプロです。原文の意図を尊重しながら、"
            "指定されたモードに沿って適切に修正します。"
        )
        if check_items:
            system_instruction += (
                "チェック項目が指定された場合は、それぞれの観点を漏れなく確認し、"
                "指摘の有無を項目ごとに明確に示してください。"
            )

        st.divider()
        try:
            usage_holder = {}
            with st.spinner("校正しています..."):
                result = st.write_stream(
                    generate_stream(
                        prompt,
                        system_instruction=system_instruction,
                        temperature=0.4,
                        usage_holder=usage_holder,
                    )
                )
            st.session_state["proofread_output"] = result
            st.session_state["proofread_usage"] = usage_holder
            record_usage(
                "校正・リライト",
                usage_holder.get("prompt_tokens", 0),
                usage_holder.get("output_tokens", 0),
            )
        except RuntimeError as e:
            render_api_error(e)
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

if st.session_state.get("proofread_output"):
    st.divider()
    render_output(
        st.session_state["proofread_output"], "proofread.txt", "proofread_output_area"
    )
    render_token_count(st.session_state.get("proofread_usage"), "output")
