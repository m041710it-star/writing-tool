# AI ライティングツール

Gemini APIを使った個人用のAIライティングアシスタント集です。認証・データベースなしで、ローカルで動かすことを想定しています。

## 機能

- 📝 ブログ記事作成
- ✉️ メール返信作成
- 📄 文章要約
- ✏️ 校正・リライト
- 🎨 文体変換
- 💡 タイトル生成
- 🌐 翻訳

## セットアップ

1. 依存パッケージをインストール

   ```bash
   pip install -r requirements.txt
   ```

2. Gemini APIキーを取得

   [Google AI Studio](https://aistudio.google.com/apikey) で無料のAPIキーを発行します。

3. APIキーを設定（以下のいずれか）

   - `.env` ファイルを作成し、`.env.example` を参考に `GEMINI_API_KEY=...` を記入する
   - `.streamlit/secrets.toml` に `GEMINI_API_KEY = "..."` を記入する
   - アプリ起動後、サイドバーに直接入力する（このセッション中のみ有効）

4. アプリを起動

   ```bash
   streamlit run app.py
   ```

   ブラウザで `http://localhost:8501` が開きます。

## 構成

```
app.py                  # ホーム画面
pages/                  # 各ライティング機能（Streamlitマルチページ）
utils/gemini_client.py  # Gemini APIラッパー
utils/common.py         # サイドバー設定・出力表示の共通UI
```

## 注意

個人利用向けのため、ユーザー認証やデータベースへの保存機能はありません。生成結果は各ページのダウンロードボタンから保存してください。
