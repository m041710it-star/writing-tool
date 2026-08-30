"""Gemini APIとの通信をまとめた薄いラッパー。"""
import json
import os
from typing import Any, Iterator, Optional

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

load_dotenv()

DEFAULT_MODEL = "gemini-flash-latest"


class QuotaExceededError(RuntimeError):
    """Gemini APIの無料枠クォータ超過(HTTP 429)を表す例外。"""


def get_api_key() -> Optional[str]:
    """優先順位: サイドバーで入力したキー > secrets.toml > 環境変数(.env)"""
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
    """429（クォータ超過）の場合は、モデル切り替えなどの案内を添えて例外を投げ直す。"""
    if getattr(error, "code", None) == 429:
        raise QuotaExceededError(
            "Gemini APIの無料枠の上限（レート制限・クォータ）に達しました。"
            "しばらく時間をおいて再度お試しいただくか、"
            "サイドバーの「使用するモデル」を Gemini Flash-Lite など"
            "より軽量なモデルに切り替えてからもう一度実行してください。"
        ) from error
    raise error


def generate_stream(
    prompt: str,
    *,
    system_instruction: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 1.0,
) -> Iterator[str]:
    """Geminiにプロンプトを送り、テキストチャンクを逐次yieldする。"""
    client = get_client()
    if client is None:
        raise RuntimeError(
            "Gemini APIキーが設定されていません。サイドバーからAPIキーを入力してください。"
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
    except genai_errors.ClientError as e:
        _raise_friendly_error(e)


def generate_json(
    prompt: str,
    *,
    schema: dict,
    system_instruction: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 1.0,
) -> dict[str, Any]:
    """Geminiに1回だけリクエストを送り、指定したJSONスキーマに沿った結果をまとめて受け取る。

    本文・タイトル案・メタディスクリプションなど複数項目を、無料枠のリクエスト回数を
    抑えるために1回のAPI呼び出しでまとめて生成したい場合に使う。
    """
    client = get_client()
    if client is None:
        raise RuntimeError(
            "Gemini APIキーが設定されていません。サイドバーからAPIキーを入力してください。"
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

    try:
        return json.loads(response.text)
    except (json.JSONDecodeError, TypeError) as e:
        raise RuntimeError(
            f"Geminiの応答をJSONとして解析できませんでした（{e}）。"
            "もう一度実行するか、モデルを変更してお試しください。"
        ) from e
