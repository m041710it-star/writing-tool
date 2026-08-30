import streamlit as st

from utils.common import render_output, render_sidebar
from utils.gemini_client import generate_json, generate_stream, get_api_key

st.set_page_config(page_title="ブログ記事作成", page_icon="📝", layout="wide")
render_sidebar()

st.title("📝 ブログ記事作成")
st.caption("テーマやキーワードから、構成の整ったブログ記事のたたき台を生成します。")

SEO_BLOG_SCHEMA = {
    "type": "object",
    "properties": {
        "title_candidates": {
            "type": "array",
            "items": {"type": "string"},
        },
        "meta_description": {"type": "string"},
        "body": {"type": "string"},
        "faq": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "answer": {"type": "string"},
                },
                "required": ["question", "answer"],
            },
        },
    },
    "required": ["title_candidates", "meta_description", "body", "faq"],
}

article_type = st.radio(
    "記事タイプ",
    ["note記事（エッセイ・体験談風）", "Webブログ記事（SEO重視）"],
    horizontal=True,
    key="blog_article_type",
)
is_seo = article_type.startswith("Webブログ")

with st.form("blog_form"):
    topic = st.text_input("記事のテーマ・タイトル案", placeholder="例：初心者向けのNISA活用法")

    if is_seo:
        main_keyword = st.text_input(
            "メインキーワード（検索されたい単語）", placeholder="例：NISA 始め方"
        )
        sub_keywords = st.text_input(
            "関連キーワード（カンマ区切りで複数可）",
            placeholder="例：つみたてNISA, 非課税, 投資信託",
        )
        persona = st.selectbox(
            "想定読者（ペルソナ）",
            ["初心者向け", "中級者向け", "専門家向け", "経営者・意思決定者向け"],
        )
        col1, col2 = st.columns(2)
        with col1:
            h2_count = st.selectbox("見出し（H2）の数", [3, 4, 5, 6, 7], index=2)
        with col2:
            length = st.selectbox(
                "文字数の目安", ["1000字前後", "2000字前後", "3000字前後"], index=1
            )
        include_faq = st.checkbox("FAQ（よくある質問）も生成する", value=True)
        extra = st.text_area(
            "その他の指示（任意）", placeholder="例：競合との差別化ポイントを入れてほしい"
        )
    else:
        audience = st.text_input("想定読者", placeholder="例：投資を始めたばかりの20代会社員")
        keywords = st.text_input("含めたいキーワード（カンマ区切り）", placeholder="例：NISA, つみたて投資, 節税")

        col1, col2 = st.columns(2)
        with col1:
            tone = st.selectbox(
                "トーン",
                ["丁寧・解説調", "カジュアル・親しみやすい", "専門的・硬め", "ユーモアを交えて"],
            )
        with col2:
            length = st.selectbox(
                "文章量の目安",
                ["短め（600字程度）", "標準（1200字程度）", "長め（2000字以上）"],
                index=1,
            )

        structure = st.multiselect(
            "含めたい構成要素",
            ["導入（フック）", "見出し（H2/H3）", "具体例", "まとめ", "CTA（行動喚起）", "よくある質問(FAQ)"],
            default=["導入（フック）", "見出し（H2/H3）", "まとめ"],
        )

        extra = st.text_area("その他の指示（任意）", placeholder="例：専門用語には簡単な補足を入れてほしい")

    submitted = st.form_submit_button(
        "🚀 記事を生成する", type="primary", disabled=not get_api_key()
    )

if not get_api_key():
    st.info("サイドバーでGemini APIキーを設定すると生成できます。")

if submitted:
    if not topic:
        st.warning("テーマを入力してください。")
    elif is_seo and not main_keyword:
        st.warning("メインキーワードを入力してください。")
    elif is_seo:
        prompt_parts = [
            "以下の条件でSEOを意識したWebブログ記事を執筆してください。",
            f"# テーマ・タイトル案\n{topic}",
            f"# メインキーワード\n{main_keyword}",
        ]
        if sub_keywords:
            prompt_parts.append(f"# 関連キーワード\n{sub_keywords}")
        prompt_parts.append(f"# 想定読者（ペルソナ）\n{persona}")
        prompt_parts.append(f"# 見出し（H2）の数\n{h2_count}個程度")
        prompt_parts.append(f"# 文字数の目安\n{length}")
        if extra:
            prompt_parts.append(f"# その他の指示\n{extra}")
        prompt_parts.append(
            "以下の項目をすべて指定のJSONスキーマに沿って出力してください。\n"
            "- title_candidates: SEOを意識した記事タイトル案を3〜5個\n"
            "- meta_description: 120字程度の日本語メタディスクリプション（記事概要の要約文）\n"
            f"- body: Markdown形式の記事本文。##（H2）見出しを{h2_count}個程度使い、"
            "必要に応じて###（H3）で細分化し、メインキーワード・関連キーワードを"
            "自然な文脈の中で使うこと。本文の末尾には必ず「## まとめ」セクションを含めること"
        )
        if include_faq:
            prompt_parts.append(
                "- faq: 読者が抱きやすい質問と回答のペアを3〜5個"
            )
        else:
            prompt_parts.append("- faq: 空の配列でよい")
        prompt = "\n\n".join(prompt_parts)

        system_instruction = (
            "あなたはSEOに精通した経験豊富な日本語Webライター兼編集者です。"
            "検索意図を満たす、客観的で網羅的な解説記事を書きます。"
            "メインキーワードや関連キーワードは、文章として不自然にならない範囲で"
            "本文に含めてください。同じキーワードを不自然に繰り返す・詰め込む"
            "（キーワードスタッフィング）ことは絶対に避けてください。"
            "出力は必ず指定されたJSONスキーマの形式に従ってください。"
        )

        st.divider()
        try:
            with st.spinner("記事一式（本文・タイトル案・メタ情報など）を生成しています..."):
                result = generate_json(
                    prompt,
                    schema=SEO_BLOG_SCHEMA,
                    system_instruction=system_instruction,
                    temperature=st.session_state.get("gemini_temperature", 1.0),
                )
            st.session_state["blog_seo_result"] = result
        except RuntimeError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
    else:
        prompt_parts = [
            "以下の条件でnote向けのエッセイ・体験談風のブログ記事を執筆してください。",
            f"# テーマ\n{topic}",
        ]
        if audience:
            prompt_parts.append(f"# 想定読者\n{audience}")
        if keywords:
            prompt_parts.append(f"# 含めるキーワード\n{keywords}")
        prompt_parts.append(f"# トーン\n{tone}")
        prompt_parts.append(f"# 文章量の目安\n{length}")
        if structure:
            prompt_parts.append(f"# 含めたい構成要素\n{'、'.join(structure)}")
        if extra:
            prompt_parts.append(f"# その他の指示\n{extra}")
        prompt_parts.append(
            "Markdown形式で、見出し（##, ###）を使いながら読みやすく執筆してください。"
        )
        prompt = "\n\n".join(prompt_parts)

        system_instruction = (
            "あなたは一人称視点でエッセイや体験談を書くのが得意な、日本語のnoteクリエイターです。"
            "自身の体験や感想を交えながら、親しみやすく人間味のある語り口で書きます。"
            "冗長な前置きは避けつつ、読者が共感できる具体的なエピソードを盛り込みます。"
            "タイトルは読者の興味を引く、キャッチーな表現を意識してください。"
        )

        st.divider()
        try:
            with st.spinner("記事を生成しています..."):
                result = st.write_stream(
                    generate_stream(
                        prompt,
                        system_instruction=system_instruction,
                        temperature=st.session_state.get("gemini_temperature", 1.0),
                    )
                )
            st.session_state["blog_output"] = result
        except RuntimeError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

if st.session_state.get("blog_seo_result"):
    result = st.session_state["blog_seo_result"]
    st.divider()

    st.subheader("🏷️ SEOタイトル案")
    titles = result.get("title_candidates") or []
    if titles:
        st.radio(
            "使用するタイトルを選択（コピーしてお使いください）",
            titles,
            key="blog_seo_title_choice",
        )
    else:
        st.caption("タイトル案は生成されませんでした。")

    st.subheader("🔍 メタディスクリプション")
    meta_description = result.get("meta_description", "")
    st.text_area(
        "メタディスクリプション（編集・コピー可）",
        value=meta_description,
        height=90,
        key="blog_seo_meta_area",
    )
    st.caption(f"文字数: {len(meta_description)}字")

    st.subheader("📄 記事本文")
    render_output(result.get("body", ""), "blog_post_seo.md", "blog_seo_body_area")

    faq = result.get("faq") or []
    if faq:
        st.subheader("❓ よくある質問（FAQ）")
        for item in faq:
            with st.expander(item.get("question", "")):
                st.write(item.get("answer", ""))

if st.session_state.get("blog_output"):
    st.divider()
    render_output(st.session_state["blog_output"], "blog_post.md", "blog_output_area")
