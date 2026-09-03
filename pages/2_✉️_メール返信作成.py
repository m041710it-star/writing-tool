import streamlit as st

from utils.common import render_api_error, render_output, render_sidebar, render_token_count
from utils.gemini_client import generate_stream, get_api_key
from utils.usage_tracker import record_usage

render_sidebar()

st.title("✉️ メール返信作成")
st.caption("受信したメールと返信の要点を入力すると、状況に合った返信文を作成します。")

tone_options = [
    "ビジネス・フォーマル",
    "丁寧だが柔らかい",
    "カジュアル（社内向け）",
    "謝罪・お詫び",
    "お礼",
    "カスタム",
]
col_tone1, col_tone2 = st.columns(2)
with col_tone1:
    tone_choice = st.selectbox("トーン", tone_options, key="email_tone_choice")
custom_tone_text = ""
if tone_choice == "カスタム":
    with col_tone2:
        custom_tone_text = st.text_input(
            "カスタムトーン（自由入力）",
            placeholder="例：関西弁で親しみやすく",
            key="email_custom_tone",
        )

with st.form("email_form"):
    original_email = st.text_area(
        "受信したメール本文", height=200, placeholder="返信元のメールをそのまま貼り付けてください"
    )
    intent = st.text_area(
        "返信で伝えたい要点",
        height=100,
        placeholder="例：来週の打ち合わせは火曜14時なら参加可能。資料は前日までに送ると伝えたい。",
    )

    render_token_count(st.session_state.get("email_usage"), "input")

    col1, col2 = st.columns(2)
    with col1:
        length = st.selectbox(
            "長さ",
            [
                "簡潔に（100字程度）",
                "標準（200〜300字程度）",
                "丁寧に・やや長め（400字程度以上）",
            ],
            index=1,
        )
    with col2:
        relationship = st.selectbox(
            "相手との関係性",
            [
                "上司・目上の方",
                "同僚・同じチームのメンバー",
                "部下・後輩",
                "社外の取引先・顧客",
                "友人・知人",
            ],
        )

    signature = st.text_input("署名（任意）", placeholder="例：株式会社〇〇 山田")

    submitted = st.form_submit_button(
        "🚀 返信文を生成する", type="primary", disabled=not get_api_key()
    )

if not get_api_key():
    st.info("「⚙️ 設定」ページでGemini APIキーを設定すると生成できます。")

if submitted:
    tone = (custom_tone_text or "カスタム") if tone_choice == "カスタム" else tone_choice

    if not intent:
        st.warning("返信で伝えたい要点を入力してください。")
    else:
        prompt_parts = []
        if original_email:
            prompt_parts.append(f"# 受信したメール本文\n{original_email}")
        prompt_parts.append(f"# 返信で伝えたい要点\n{intent}")
        prompt_parts.append(f"# トーン\n{tone}")
        prompt_parts.append(f"# 長さ\n{length}")
        prompt_parts.append(f"# 相手との関係性\n{relationship}")
        if signature:
            prompt_parts.append(f"# 署名\n{signature}")
        prompt_parts.append(
            "上記をもとに、日本語ビジネスメールとして自然な返信文を、"
            "宛名・書き出しの挨拶・本文・結びの挨拶・署名まで含めて作成してください。"
            "相手との関係性に応じて、敬語のレベルや言葉選びを適切に調整してください。"
        )
        prompt = "\n\n".join(prompt_parts)

        system_instruction = (
            "あなたは日本のビジネスメール作成に精通したアシスタントです。"
            "相手に失礼のない自然な敬語と、簡潔で分かりやすい文章を書きます。"
        )

        st.divider()
        try:
            usage_holder = {}
            with st.spinner("返信文を生成しています..."):
                result = st.write_stream(
                    generate_stream(
                        prompt,
                        system_instruction=system_instruction,
                        temperature=st.session_state.get("gemini_temperature", 1.0),
                        usage_holder=usage_holder,
                    )
                )
            st.session_state["email_output"] = result
            st.session_state["email_usage"] = usage_holder
            record_usage(
                "メール返信作成",
                usage_holder.get("prompt_tokens", 0),
                usage_holder.get("output_tokens", 0),
            )
        except RuntimeError as e:
            render_api_error(e)
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

if st.session_state.get("email_output"):
    st.divider()
    render_output(st.session_state["email_output"], "email_reply.txt", "email_output_area")
    render_token_count(st.session_state.get("email_usage"), "output")
