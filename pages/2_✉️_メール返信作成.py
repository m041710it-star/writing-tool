import streamlit as st

from utils.common import render_output, render_sidebar
from utils.gemini_client import generate_stream, get_api_key

st.set_page_config(page_title="メール返信作成", page_icon="✉️", layout="wide")
render_sidebar()

st.title("✉️ メール返信作成")
st.caption("受信したメールと返信の要点を入力すると、状況に合った返信文を作成します。")

with st.form("email_form"):
    original_email = st.text_area(
        "受信したメール本文", height=200, placeholder="返信元のメールをそのまま貼り付けてください"
    )
    intent = st.text_area(
        "返信で伝えたい要点",
        height=100,
        placeholder="例：来週の打ち合わせは火曜14時なら参加可能。資料は前日までに送ると伝えたい。",
    )

    col1, col2 = st.columns(2)
    with col1:
        tone = st.selectbox(
            "トーン",
            ["ビジネス・フォーマル", "丁寧だが柔らかい", "カジュアル（社内向け）", "謝罪・お詫び", "お礼"],
        )
    with col2:
        length = st.selectbox("長さ", ["簡潔に", "標準", "やや丁寧に長め"], index=1)

    signature = st.text_input("署名（任意）", placeholder="例：株式会社〇〇 山田")

    submitted = st.form_submit_button(
        "🚀 返信文を生成する", type="primary", disabled=not get_api_key()
    )

if not get_api_key():
    st.info("サイドバーでGemini APIキーを設定すると生成できます。")

if submitted:
    if not intent:
        st.warning("返信で伝えたい要点を入力してください。")
    else:
        prompt_parts = []
        if original_email:
            prompt_parts.append(f"# 受信したメール本文\n{original_email}")
        prompt_parts.append(f"# 返信で伝えたい要点\n{intent}")
        prompt_parts.append(f"# トーン\n{tone}")
        prompt_parts.append(f"# 長さ\n{length}")
        if signature:
            prompt_parts.append(f"# 署名\n{signature}")
        prompt_parts.append(
            "上記をもとに、日本語ビジネスメールとして自然な返信文を、"
            "宛名・書き出しの挨拶・本文・結びの挨拶・署名まで含めて作成してください。"
        )
        prompt = "\n\n".join(prompt_parts)

        system_instruction = (
            "あなたは日本のビジネスメール作成に精通したアシスタントです。"
            "相手に失礼のない自然な敬語と、簡潔で分かりやすい文章を書きます。"
        )

        st.divider()
        try:
            with st.spinner("返信文を生成しています..."):
                result = st.write_stream(
                    generate_stream(
                        prompt,
                        system_instruction=system_instruction,
                        temperature=st.session_state.get("gemini_temperature", 1.0),
                    )
                )
            st.session_state["email_output"] = result
        except RuntimeError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

if st.session_state.get("email_output"):
    st.divider()
    render_output(st.session_state["email_output"], "email_reply.txt", "email_output_area")
