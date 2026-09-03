# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## これは何か

Gemini APIをラップした、個人利用向けのStreamlitマルチページアプリです。日本語のライティング作業（ブログ下書き、メール返信、要約、校正・リライト、文体変換、タイトル生成、翻訳）を扱います。データベースはなく、すべてセッション内で完結し、生成結果はダウンロードボタンで保存します。「設定」ページのみ簡易パスワード認証があり、それ以外のページに認証はありません。

## コマンド

```bash
pip install -r requirements.txt   # 依存パッケージのインストール
streamlit run app.py              # アプリの起動 (http://localhost:8501)
```

このリポジトリにテストスイート・lint設定・ビルド手順はありません。

## APIキーの解決順序

`utils/gemini_client.py:get_api_key()` は以下の順でキーを確認します: 「設定」ページのテキスト入力 (`st.session_state["gemini_api_key"]`) → `.streamlit/secrets.toml` (`GEMINI_API_KEY`) → `.env` / 環境変数 (`GEMINI_API_KEY`)。新しいコードで環境変数を直接読むのではなく `get_api_key()` / `get_client()` を必ず経由させ、「設定」ページからの上書きが効くようにしてください。

## アーキテクチャ

- `app.py` — ルーター。`st.set_page_config(...)` を1回だけ呼び出したうえで `st.Page(...)` を並べて `st.navigation({...}).run()` する。サイドバーのメニュー順序・ラベル・アイコンはここで一元管理しており、`pages/` 内のファイル名の連番は表示順に影響しない（人が識別しやすいよう慣習的に付けているだけ）。`st.navigation` には空白文字だけの見出し（`""`, `" "`, `"  "`, `"   "`）をキーにした辞書を渡しており、見出しテキストを見せずにグループの切れ目にメニュー項目間の余白だけを入れている（トップページ/ブログ記事作成の間、タイトル生成/翻訳の間、翻訳/設定の間）。余白の位置を変える場合はこのグループ分けを調整する。
- `pages/0_🏠_トップページ.py` — ホーム画面本体。利用可能なツール一覧をカード表示する。
- `pages/N_<絵文字>_<名前>.py`（N=1〜7） — 各ライティング機能ごとに1ファイル。各ページは独立しており、他のページに依存しません（8=設定、9=変更履歴、10=API利用状況、11=仕様書は番号を空けて別枠にしている）。
- `pages/8_⚙️_設定.py` — Gemini APIキーの入力欄。`st.session_state["gemini_api_key"]` を更新する唯一の場所（サイドバーには表示しない）。`utils/common.py:get_settings_password()`（`SETTINGS_PASSWORD`: `.streamlit/secrets.toml` > `.env`/環境変数）と一致するパスワードを入力し `st.session_state["settings_authenticated"]` が真になるまで、ページ本体（APIキー入力欄）は表示されない。このページ限定の認証であり、他のページには影響しない。`SETTINGS_PASSWORD` 未設定時はページ自体を利用不可にする（フェイルクローズ）。APIキー入力欄の下に「有料利用に切り替えました」トグルがあり、`utils/usage_tracker.py:set_paid_mode()` を更新する唯一の場所（`usage_data.json` に永続化）。
- `pages/9_📜_変更履歴.py` — リポジトリ直下の `CHANGELOG.md` を読み込んで表示するだけ。変更履歴を追記するときはこのMarkdownファイルを更新すればページ側の修正は不要。
- `pages/11_📘_仕様書.py` — リポジトリ直下の `SPEC.md`（利用者向けの機能一覧・最新仕様書）を読み込んで表示するだけ。機能追加・変更を行ったときは、`CHANGELOG.md` への追記とあわせて `SPEC.md` も最新の内容に更新すること（ページ側の修正は不要）。
- `pages/10_📊_API利用状況.py` — `utils/usage_tracker.py` が管理する利用履歴・課金履歴・単価設定を一覧表示し、課金額の入力や単価の変更を行うページ。認証なし。冒頭で `render_usage_status(target=st)` を呼び、無料枠・有料枠の状況（下記）をページ本文にも表示する。課金履歴の入力欄は `usage_tracker.get_paid_mode()` が真（＝「⚙️ 設定」ページで有料利用に切り替え済み）のときのみ表示され、無料枠利用中は案内メッセージのみ表示する。
- `utils/models.py` — モデル選択肢 `MODEL_OPTIONS`（プルダウン用の短いラベル→モデルID。カッコ書きの説明文は含めない）、モデルIDごとの説明文 `MODEL_DESCRIPTIONS`（`render_sidebar()` がプルダウンの下にキャプション表示する）、その逆引き `MODEL_LABELS`、429発生時の案内を出し分けるための「軽量→高負荷」の並び `MODEL_ORDER` を定義する。`get_model_weight_tier(model_id)` はモデルを `"lightest"`/`"standard"`/`"heavy"` に区分し、`get_lighter_model(model_id)` は一段階軽量なモデルIDを返す（最軽量なら`None`）。これは429時の案内文言を出し分けるためだけの相対的な目安であり、特定モデルが無料枠の対象外だと断定するものではない。`utils/common.py` と `utils/gemini_client.py` の両方から参照されるため、循環importを避けるためにstreamlitにも他のutilsモジュールにも依存しない独立ファイルにしている。
- `utils/gemini_client.py` — `google-genai` の薄いラッパー。`generate_stream()` はテキストをストリーミングで逐次yieldし（`st.write_stream` 用）、`generate_json()` は1回のリクエストで指定した `response_schema`（プレーンなJSON Schema辞書）に沿った構造化出力をまとめて受け取る（`json.loads(response.text)` を返す）。複数項目を無料枠のリクエスト回数を抑えて生成したい場合は後者を使う。モデル名・temperatureは、呼び出し側で指定しない限り `st.session_state`（サイドバーがセット）から読まれ、未設定時のフォールバックは `DEFAULT_MODEL`（現在 `gemini-flash-lite-latest`）。どちらの関数も、呼び出しが成功すると `usage_tracker.set_last_call_ok()` を、`google.genai.errors.ClientError` の429（クォータ超過）を捕捉すると `usage_tracker.set_last_call_quota_exceeded(model)` を呼び、直近の呼び出し結果を無料枠状態表示（簡易的な目安）に反映させる。429は `QuotaExceededError`（`RuntimeError` のサブクラス、実際に使用したモデルIDを`.model`に保持）に変換してメッセージを付与する。`usage_tracker.get_paid_mode()` が偽（無料枠利用中）の場合のみ、`_build_free_tier_quota_message()` が `utils/models.py:get_model_weight_tier()` の区分（heavy/standard/lightest）に応じた段階的な案内（軽量モデルへの切り替え・再試行の目安・無料枠リセット時間の目安）と、有料切り替え時の予算アラート設定の推奨・公式ドキュメントへのリンク・課金後の反映手順（`_PAID_SWITCH_GUIDANCE`）を組み立てる（有料利用中はこの案内を出さず、簡潔なメッセージのみ）。案内文には必ず `FREE_TIER_DISCLAIMER`（「現時点の簡易的な目安である」旨と[Gemini API 料金ページ](https://ai.google.dev/gemini-api/docs/pricing)へのリンク）を添える。既存ページの `except RuntimeError` はそのままこれも拾う。`generate_stream()`/`generate_json()` に空の辞書を `usage_holder=` で渡すと、完了後に `prompt_tokens`/`output_tokens`/`total_tokens` が書き込まれる（`render_token_count()` での表示、`record_usage()` への記録に使う）。
- `utils/common.py` — 共通UI。`render_sidebar()`（`utils/models.py:MODEL_OPTIONS` からのモデル選択、`render_usage_status()` による無料枠・有料枠のまとめ表示、temperatureスライダー、APIキー設定状況の表示のみ。APIキー入力欄自体は含まない）、`render_token_count(usage, kind)`（入力欄・出力欄それぞれのトークン数キャプション）、`render_usage_status(target=None)`（省略時はサイドバー、`st` を渡すとページ本文にも表示可能。無料枠は `usage_tracker.get_last_call_status()` を見て「✅ 利用可能」/「⚠️ 利用制限に達した可能性」を表示し、有料枠は `usage_tracker.get_paid_mode()` が偽なら「未設定」＋設定ページへの `page_link`、真かつ課金履歴があれば `[■■■□□□]` 形式のテキスト進捗バーと残高目安を表示し、末尾に必ず `FREE_TIER_DISCLAIMER` を添える）、`render_api_error(error)`（`except RuntimeError as e:` の受け皿。`QuotaExceededError` かつ無料枠利用中の場合のみ、`error.model` から軽量モデルへの切り替えボタン・「⚙️ 設定」ページへのリンクを追加表示する）、`render_output()`（編集可能なテキストエリア＋結果のダウンロードボタン）。モデル選択の `st.sidebar.selectbox` には `key="gemini_model_label"` を付けており、`render_api_error()` の切り替えボタンはこのキーへ直接書き込んで `st.rerun()` することでモデルを切り替える。
- `utils/usage_tracker.py` — トークン数・概算コストの利用履歴、課金履歴、入出力単価、課金モードのON/OFF（`paid_mode`、既定は`False`＝無料枠）、直近のAPI呼び出し結果（`last_call`: `status`/`model`/`timestamp`）をリポジトリ直下の `usage_data.json`（`.gitignore` 済み・外部送信なし）に読み書きする。生成に成功した各ページは `record_usage(page_name, input_tokens, output_tokens)` を呼んで1件記録する。`get_paid_mode()`/`set_paid_mode()` は「⚙️ 設定」ページのトグル（無料枠の状態に関わらずいつでもON/OFF可能）から更新される。`get_last_call_status()`/`set_last_call_ok()`/`set_last_call_quota_exceeded(model)` は `gemini_client.py` からのみ更新され、Gemini APIに残量取得の仕組みがないための簡易的な代替指標として使う。`compute_summary()` が「課金累計 ÷ 実績ベースの単価」から算出する `target_tokens`（使用可能な目安トークン数）と実績トークン数の比率 `usage_ratio`、残高目安 `balance_yen` を返し、`render_usage_status()` の色分け・テキスト進捗バーに使われる（`paid_mode` が真の場合のみ）。

## ページの共通パターン

`pages/` 内の各ツールページ（1〜7）は同じ構成に従っています。新しいツールを追加する際はゼロから書かず、既存ページ（例: `pages/4_✏️_校正リライト.py`）をコピーしてください。`st.set_page_config(...)` は `app.py` が1回だけ呼び出すため、個々のページファイルでは呼ばないこと（二重に呼ぶとエラーになる）。新しいページを追加したら `app.py` の `st.navigation({...})` の該当グループにも `st.Page(...)` を追加してメニューに載せる。

1. 先頭で `render_sidebar()` を呼ぶ。
2. 入力項目は `st.form(...)` の中にまとめ、最後に `st.form_submit_button(..., disabled=not get_api_key())` を置く。
3. 送信時: 必須項目を `st.warning` で検証し、ラベル付きセクション（`# セクション名\n内容`）からプロンプト文字列を組み立て、タスク固有の `system_instruction` を定義したうえで、`st.spinner` 内で `st.write_stream()` 経由の `generate_stream()` を呼び出す（`usage_holder={}` を渡す）。
4. 結果は `st.session_state["<tool>_output"]` に、トークン数は `st.session_state["<tool>_usage"]` に保存し、`record_usage("<ページ表示名>", ...)` で利用履歴に記録する。フォームの後段で `render_output(text, filename, area_key)` を使って表示する（こうすることで送信直後だけでなく再実行後も結果が表示され続ける）。入力欄の直後・出力欄の直後にそれぞれ `render_token_count(usage, "input"/"output")` を呼んでトークン数を表示する。
5. 生成処理の呼び出しは `try/except RuntimeError`（`generate_stream` からのAPIキー未設定メッセージ、および429の `QuotaExceededError` 用。`render_api_error(e)` で表示する）と、それ以外のエラー用の `except Exception`（`st.error` で表示）で囲む。

temperatureは基本的にサイドバーの値（`st.session_state.get("gemini_temperature", 1.0)`）を使いますが、より確定的な出力が必要なタスク（例: 校正では固定値 `0.4`）では例外的に固定しています。

## 例外: ブログ記事作成ページの2モード構成

`pages/1_📝_ブログ記事作成.py` は上記の単純なパターンから分岐しており、`st.form(...)` の外に置いた `st.selectbox`（記事タイプ: note記事 / Webブログ記事、および note記事モードでの「トーン」）で条件付きフォームを実現している（フォーム内の要素はsubmitまでrerunされないため、条件分岐させたい入力はフォームの外側の要素で制御する必要がある）。同様に `pages/2_✉️_メール返信作成.py` の「トーン」も、「カスタム」選択時に自由入力欄を出すためフォームの外に置いている。

- **note記事**: 既存のシンプルな `generate_stream()` ストリーミング生成フローをそのまま維持（`st.session_state["blog_output"]`）。
- **Webブログ記事（SEO重視）**: `generate_json()` を1回だけ呼び、`title_candidates` / `meta_description` / `body` / `faq` をまとめて生成して `st.session_state["blog_seo_result"]` に保存する。新しいSEO関連の出力項目を増やす場合は、ページ内の `SEO_BLOG_SCHEMA` にプロパティを足し、プロンプトの指示文にも生成してほしい項目を明記すること（スキーマだけ変えてもモデルには伝わらない）。

新しいツールで「複数の出力を1回のAPI呼び出しでまとめたい」場合は、このページを参考に `generate_json()` を使う。
