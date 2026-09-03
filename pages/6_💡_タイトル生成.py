import streamlit as st

from utils.common import render_api_error, render_output, render_sidebar, render_token_count
from utils.gemini_client import generate_stream, get_api_key
from utils.usage_tracker import record_usage

render_sidebar()

st.title("💡 タイトル生成")
st.caption("記事の内容やキーワードから、複数のタイトル案・見出し案を生成します。")

with st.form("title_form"):
    content = st.text_area(
        "記事の内容・要約、またはキーワード",
        height=200,
        placeholder="例：初心者向けにNISAの始め方を解説する記事。つみたて投資の始め方、口座開設の手順を含む。",
    )

    render_token_count(st.session_state.get("title_usage"), "input")

    col1, col2 = st.columns(2)
    with col1:
        style = st.selectbox(
            "スタイル",
            ["SEOを意識した検索されやすいタイトル", "クリックしたくなる（煽り気味）タイトル", "シンプルで誠実なタイトル", "SNS向けの短いタイトル"],
        )
    with col2:
        count = st.slider("生成する案の数", min_value=3, max_value=15, value=8)

    include_subheadings = st.checkbox("記事内の見出し（h2）案も一緒に生成する", value=False)

    submitted = st.form_submit_button(
        "🚀 タイトルを生成する", type="primary", disabled=not get_api_key()
    )

if not get_api_key():
    st.info("「⚙️ 設定」ページでGemini APIキーを設定すると生成できます。")

if submitted:
    if not content.strip():
        st.warning("記事の内容やキーワードを入力してください。")
    else:
        prompt_parts = [
            f"# 記事の内容・キーワード\n{content}",
            f"# スタイル\n{style}",
            f"# 生成する案の数\n{count}個",
        ]
        prompt_parts.append("タイトル案を番号付きの箇条書きで出力してください。")
        if include_subheadings:
            prompt_parts.append(
                "タイトル案とは別のセクションとして、記事内で使えるh2見出し案も5〜8個、箇条書きで出力してください。"
            )
        prompt = "\n\n".join(prompt_parts)

        system_instruction = (
            "あなたは日本語コンテンツのタイトル・見出し作成が得意な編集者です。"
            "読者の興味を引きつつ、内容を誤解させないタイトルを作ります。"
        )

        st.divider()
        try:
            usage_holder = {}
            with st.spinner("タイトルを生成しています..."):
                result = st.write_stream(
                    generate_stream(
                        prompt,
                        system_instruction=system_instruction,
                        temperature=1.1,
                        usage_holder=usage_holder,
                    )
                )
            st.session_state["title_output"] = result
            st.session_state["title_usage"] = usage_holder
            record_usage(
                "タイトル生成",
                usage_holder.get("prompt_tokens", 0),
                usage_holder.get("output_tokens", 0),
            )
        except RuntimeError as e:
            render_api_error(e)
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

if st.session_state.get("title_output"):
    st.divider()
    render_output(st.session_state["title_output"], "titles.txt", "title_output_area")
    render_token_count(st.session_state.get("title_usage"), "output")
