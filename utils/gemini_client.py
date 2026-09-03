"""Gemini APIとの通信をまとめた薄いラッパー。"""
import json
import os
from typing import Any, Iterator, Optional

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from utils import usage_tracker

load_dotenv()

DEFAULT_MODEL = "gemini-flash-lite-latest"


class QuotaExceededError(RuntimeError):
    """Gemini APIの無料枠クォータ超過(HTTP 429)を表す例外。"""


def get_api_key() -> Optional[str]:
    """優先順位: 「設定」ページで入力したキー > secrets.toml > 環境変数(.env)"""
    session_key = st.session_state.get("gemini_api_key")
    if session_key:
        return session_key

    try:
        secret_key = st.secrets["GEMINI_API_KEY"]
        if secret_key:
            return secret_key
    except Exception:
        pass

    return os.environ.get("GEMINI_API_KEY")


def get_client() -> Optional[genai.Client]:
    api_key = get_api_key()
    if not api_key:
        return None
    return genai.Client(api_key=api_key)


def _raise_friendly_error(error: genai_errors.ClientError) -> None:
    """429（クォータ超過）の場合は、案内を添えて例外を投げ直す。

    無料枠利用中（デフォルト）の場合のみ、有料切り替え時の注意点（予算アラートの
    設定推奨）と、課金後にこのツールへ金額を反映させる手順を追加で案内する。
    有料利用中（「⚙️ 設定」ページで切り替え済み）の場合はこの案内を出さない。
    """
    if getattr(error, "code", None) == 429:
        message = (
            "Gemini APIのレート制限・クォータの上限に達しました。"
            "しばらく時間をおいて再度お試しいただくか、"
            "サイドバーの「使用するモデル」を Gemini Flash-Lite など"
            "より軽量なモデルに切り替えてからもう一度実行してください。"
        )
        if not usage_tracker.get_paid_mode():
            message += (
                "\n\n"
                "- 無料枠の利用上限に達した可能性があります。\n"
                "- 有料利用への切り替えを検討する場合は、想定外の高額請求を防ぐため、"
                "先にGoogle Cloudで「支出上限（予算アラート）」を設定してから"
                "切り替えることをおすすめします。\n"
                "- 設定方法: "
                "[支出予算とアラートを設定する（Google Cloud公式）]"
                "(https://cloud.google.com/billing/docs/how-to/budgets)\n"
                "- 実際に課金（支払い設定）をした場合は、「⚙️ 設定」ページで"
                "「有料利用に切り替えました」をONにしたうえで、"
                "「📊 API利用状況」ページの課金履歴の入力欄に、その課金金額を"
                "入力してください。\n"
                "- 金額を入力すると、サイドバーにトークンの残り目安が"
                "表示されるようになります。"
            )
        raise QuotaExceededError(message) from error
    raise error


def _record_usage(usage_holder: Optional[dict], usage_metadata: Any) -> None:
    if usage_holder is None or usage_metadata is None:
        return
    usage_holder["prompt_tokens"] = usage_metadata.prompt_token_count
    usage_holder["output_tokens"] = usage_metadata.candidates_token_count
    usage_holder["total_tokens"] = usage_metadata.total_token_count


def generate_stream(
    prompt: str,
    *,
    system_instruction: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 1.0,
    usage_holder: Optional[dict] = None,
) -> Iterator[str]:
    """Geminiにプロンプトを送り、テキストチャンクを逐次yieldする。

    `usage_holder` に空の辞書を渡すと、ストリーミング完了時点でその辞書に
    `prompt_tokens` / `output_tokens` / `total_tokens` が書き込まれる
    （呼び出し側で`st.write_stream()`実行後に参照する）。
    """
    client = get_client()
    if client is None:
        raise RuntimeError(
            "Gemini APIキーが設定されていません。「⚙️ 設定」ページでAPIキーを入力してください。"
        )

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=temperature,
    )

    try:
        stream = client.models.generate_content_stream(
            model=model or st.session_state.get("gemini_model", DEFAULT_MODEL),
            contents=prompt,
            config=config,
        )
        for chunk in stream:
            if chunk.text:
                yield chunk.text
            _record_usage(usage_holder, chunk.usage_metadata)
    except genai_errors.ClientError as e:
        _raise_friendly_error(e)


def generate_json(
    prompt: str,
    *,
    schema: dict,
    system_instruction: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 1.0,
    usage_holder: Optional[dict] = None,
) -> dict[str, Any]:
    """Geminiに1回だけリクエストを送り、指定したJSONスキーマに沿った結果をまとめて受け取る。

    本文・タイトル案・メタディスクリプションなど複数項目を、無料枠のリクエスト回数を
    抑えるために1回のAPI呼び出しでまとめて生成したい場合に使う。
    `usage_holder` に空の辞書を渡すと、`prompt_tokens` / `output_tokens` / `total_tokens`
    が書き込まれる。
    """
    client = get_client()
    if client is None:
        raise RuntimeError(
            "Gemini APIキーが設定されていません。「⚙️ 設定」ページでAPIキーを入力してください。"
        )

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=temperature,
        response_mime_type="application/json",
        response_schema=schema,
    )

    try:
        response = client.models.generate_content(
            model=model or st.session_state.get("gemini_model", DEFAULT_MODEL),
            contents=prompt,
            config=config,
        )
    except genai_errors.ClientError as e:
        _raise_friendly_error(e)

    _record_usage(usage_holder, response.usage_metadata)

    try:
        return json.loads(response.text)
    except (json.JSONDecodeError, TypeError) as e:
        raise RuntimeError(
            f"Geminiの応答をJSONとして解析できませんでした（{e}）。"
            "もう一度実行するか、モデルを変更してお試しください。"
        ) from e
