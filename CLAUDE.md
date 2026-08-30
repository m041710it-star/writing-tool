# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## これは何か

Gemini APIをラップした、個人利用向けのStreamlitマルチページアプリです。日本語のライティング作業（ブログ下書き、メール返信、要約、校正・リライト、トーン変換、タイトル生成、翻訳）を扱います。認証・データベースはなく、すべてセッション内で完結し、生成結果はダウンロードボタンで保存します。

## コマンド

```bash
pip install -r requirements.txt   # 依存パッケージのインストール
streamlit run app.py              # アプリの起動 (http://localhost:8501)
```

このリポジトリにテストスイート・lint設定・ビルド手順はありません。

## APIキーの解決順序

`utils/gemini_client.py:get_api_key()` は以下の順でキーを確認します: サイドバーのテキスト入力 (`st.session_state["gemini_api_key"]`) → `.streamlit/secrets.toml` (`GEMINI_API_KEY`) → `.env` / 環境変数 (`GEMINI_API_KEY`)。新しいコードで環境変数を直接読むのではなく `get_api_key()` / `get_client()` を必ず経由させ、サイドバーからの上書きが効くようにしてください。

## アーキテクチャ

- `app.py` — ホーム画面。`render_sidebar()` を呼び出し、利用可能なツール一覧を表示するだけ。
- `pages/N_<絵文字>_<名前>.py` — 各ライティング機能ごとに1ファイル。Streamlitのマルチページ規約に従い、先頭の数字がサイドバーの表示順、ファイル名がナビラベルになります。各ページは独立しており、他のページに依存しません。
- `utils/gemini_client.py` — `google-genai` の薄いラッパー。`generate_stream()` はテキストをストリーミングで逐次yieldし（`st.write_stream` 用）、`generate_json()` は1回のリクエストで指定した `response_schema`（プレーンなJSON Schema辞書）に沿った構造化出力をまとめて受け取る（`json.loads(response.text)` を返す）。複数項目を無料枠のリクエスト回数を抑えて生成したい場合は後者を使う。モデル名・temperatureは、呼び出し側で指定しない限り `st.session_state`（サイドバーがセット）から読まれる。どちらの関数も `google.genai.errors.ClientError` の429（クォータ超過）を捕捉し、`QuotaExceededError`（`RuntimeError` のサブクラス）に変換してモデル切り替えを促すメッセージを付与する。既存ページの `except RuntimeError` はそのままこれも拾う。
- `utils/common.py` — 共通UI。`render_sidebar()`（サイドバー最上部の🏠トップページへの `st.page_link`、APIキー入力、`MODEL_OPTIONS` からのモデル選択、temperatureスライダー）と `render_output()`（編集可能なテキストエリア＋結果のダウンロードボタン）。`MODEL_OPTIONS` は無料枠で安定しやすいFlash / Flash-Lite系を先頭にし、Proは無料枠の上限が低い旨をラベルに明記している。

## ページの共通パターン

`pages/` 内の各ページは同じ構成に従っています。新しいツールを追加する際はゼロから書かず、既存ページ（例: `pages/4_✏️_校正リライト.py`）をコピーしてください。

1. `st.set_page_config(...)` の後に `render_sidebar()` を呼ぶ。
2. 入力項目は `st.form(...)` の中にまとめ、最後に `st.form_submit_button(..., disabled=not get_api_key())` を置く。
3. 送信時: 必須項目を `st.warning` で検証し、ラベル付きセクション（`# セクション名\n内容`）からプロンプト文字列を組み立て、タスク固有の `system_instruction` を定義したうえで、`st.spinner` 内で `st.write_stream()` 経由の `generate_stream()` を呼び出す。
4. 結果は `st.session_state["<tool>_output"]` に保存し、フォームの後段で `render_output(text, filename, area_key)` を使って表示する（こうすることで送信直後だけでなく再実行後も結果が表示され続ける）。
5. 生成処理の呼び出しは `try/except RuntimeError`（`generate_stream` からのAPIキー未設定メッセージ用）と、それ以外のエラー用の `except Exception` で囲み、いずれも `st.error` で表示する。

temperatureは基本的にサイドバーの値（`st.session_state.get("gemini_temperature", 1.0)`）を使いますが、より確定的な出力が必要なタスク（例: 校正では固定値 `0.4`）では例外的に固定しています。

## 例外: ブログ記事作成ページの2モード構成

`pages/1_📝_ブログ記事作成.py` は上記の単純なパターンから分岐しており、`st.form(...)` の外に置いた `st.radio`（記事タイプ: note記事 / Webブログ記事）で条件付きフォームを実現している（フォーム内の要素はsubmitまでrerunされないため、条件分岐させたい入力はフォームの外側の要素で制御する必要がある）。

- **note記事**: 既存のシンプルな `generate_stream()` ストリーミング生成フローをそのまま維持（`st.session_state["blog_output"]`）。
- **Webブログ記事（SEO重視）**: `generate_json()` を1回だけ呼び、`title_candidates` / `meta_description` / `body` / `faq` をまとめて生成して `st.session_state["blog_seo_result"]` に保存する。新しいSEO関連の出力項目を増やす場合は、ページ内の `SEO_BLOG_SCHEMA` にプロパティを足し、プロンプトの指示文にも生成してほしい項目を明記すること（スキーマだけ変えてもモデルには伝わらない）。

新しいツールで「複数の出力を1回のAPI呼び出しでまとめたい」場合は、このページを参考に `generate_json()` を使う。
