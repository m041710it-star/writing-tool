"""API利用状況（トークン数・概算コスト）をローカルファイルに記録するユーティリティ。

外部には一切送信せず、プロジェクト直下の `usage_data.json` に保存する
（`.gitignore` 済み・個人利用のローカルデータ）。ここで計算する金額・残高は
あくまでアプリ内での目安であり、実際の請求額の代わりにはならない。
"""
import json
import os
from datetime import datetime
from typing import Any

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "usage_data.json")

DEFAULT_PRICING = {
    "input_price_per_million": 15.0,
    "output_price_per_million": 60.0,
}


def _load() -> dict[str, Any]:
    if not os.path.exists(DATA_FILE):
        return {"usage": [], "billing": [], "pricing": DEFAULT_PRICING.copy()}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"usage": [], "billing": [], "pricing": DEFAULT_PRICING.copy()}
    data.setdefault("usage", [])
    data.setdefault("billing", [])
    data.setdefault("pricing", DEFAULT_PRICING.copy())
    return data


def _save(data: dict[str, Any]) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_pricing() -> dict[str, float]:
    return _load()["pricing"]


def set_pricing(input_price_per_million: float, output_price_per_million: float) -> None:
    data = _load()
    data["pricing"] = {
        "input_price_per_million": float(input_price_per_million),
        "output_price_per_million": float(output_price_per_million),
    }
    _save(data)


def record_usage(page: str, input_tokens: int, output_tokens: int) -> None:
    """1回の生成結果をトークン数・概算コストとともに履歴へ追記する。"""
    input_tokens = int(input_tokens or 0)
    output_tokens = int(output_tokens or 0)
    if not input_tokens and not output_tokens:
        return

    data = _load()
    pricing = data["pricing"]
    cost = (
        input_tokens / 1_000_000 * pricing["input_price_per_million"]
        + output_tokens / 1_000_000 * pricing["output_price_per_million"]
    )
    data["usage"].append(
        {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "page": page,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_yen": round(cost, 3),
        }
    )
    _save(data)


def get_usage_records() -> list[dict[str, Any]]:
    return _load()["usage"]


def add_billing_entry(date_str: str, amount_yen: float) -> None:
    data = _load()
    data["billing"].append({"date": date_str, "amount_yen": float(amount_yen)})
    _save(data)


def get_billing_records() -> list[dict[str, Any]]:
    return _load()["billing"]


def compute_summary() -> dict[str, Any]:
    """残高の目安計算に必要な集計値をまとめて返す。"""
    data = _load()
    usage = data["usage"]
    billing = data["billing"]
    pricing = data["pricing"]

    total_input = sum(r["input_tokens"] for r in usage)
    total_output = sum(r["output_tokens"] for r in usage)
    total_tokens = total_input + total_output
    total_cost = sum(r["cost_yen"] for r in usage)
    total_billing = sum(b["amount_yen"] for b in billing)
    balance_yen = total_billing - total_cost

    if total_tokens > 0:
        blended_price = (
            total_input / total_tokens * pricing["input_price_per_million"]
            + total_output / total_tokens * pricing["output_price_per_million"]
        )
    else:
        blended_price = (
            pricing["input_price_per_million"] + pricing["output_price_per_million"]
        ) / 2

    target_tokens = (
        total_billing / (blended_price / 1_000_000)
        if blended_price > 0 and total_billing > 0
        else 0
    )
    usage_ratio = (total_tokens / target_tokens) if target_tokens > 0 else 0.0

    return {
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_tokens": total_tokens,
        "total_cost_yen": total_cost,
        "total_billing_yen": total_billing,
        "balance_yen": balance_yen,
        "target_tokens": target_tokens,
        "usage_ratio": usage_ratio,
    }


def compute_daily_subtotals() -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for r in get_usage_records():
        day = r["timestamp"][:10]
        b = buckets.setdefault(
            day,
            {"date": day, "input_tokens": 0, "output_tokens": 0, "cost_yen": 0.0, "count": 0},
        )
        b["input_tokens"] += r["input_tokens"]
        b["output_tokens"] += r["output_tokens"]
        b["cost_yen"] += r["cost_yen"]
        b["count"] += 1
    return sorted(buckets.values(), key=lambda b: b["date"], reverse=True)


def compute_page_subtotals() -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for r in get_usage_records():
        page = r["page"]
        b = buckets.setdefault(
            page,
            {"page": page, "input_tokens": 0, "output_tokens": 0, "cost_yen": 0.0, "count": 0},
        )
        b["input_tokens"] += r["input_tokens"]
        b["output_tokens"] += r["output_tokens"]
        b["cost_yen"] += r["cost_yen"]
        b["count"] += 1
    return sorted(buckets.values(), key=lambda b: b["cost_yen"], reverse=True)
