"""モデル選択肢と、無料枠の目安判定に使う「軽量度」の並び順を定義する。

Gemini APIの無料枠の対象・上限はモデルやGoogle側の仕様変更によって
異なる場合があるため、ここでの並び順・区分は「相対的にどちらが
軽量（低負荷）か」という目安としてのみ利用する。特定モデルが
無料枠の対象外であると断定するものではない。
"""

MODEL_OPTIONS = {
    "Gemini Flash-Lite": "gemini-flash-lite-latest",
    "Gemini Flash": "gemini-flash-latest",
    "Gemini Pro": "gemini-pro-latest",
}

# プルダウンの選択肢名（上記）は短く保ち、説明文はこちらから別途表示する
# （選択肢内にカッコ書きで詰め込むと、プルダウン内で文字が見切れるため）。
MODEL_DESCRIPTIONS = {
    "gemini-flash-lite-latest": "軽量・低コスト／無料枠向け",
    "gemini-flash-latest": "高速・バランス型／無料枠向け",
    "gemini-pro-latest": "高精度・じっくり／無料枠の上限が低め",
}

# モデルIDからラベルを引くための逆引き辞書。
MODEL_LABELS = {model_id: label for label, model_id in MODEL_OPTIONS.items()}

# 429発生時の案内文を出し分けるためだけに使う、軽量→高負荷の並び。
MODEL_ORDER = list(MODEL_OPTIONS.values())


def get_model_weight_tier(model_id: str) -> str:
    """モデルの相対的な負荷傾向を "lightest" / "standard" / "heavy" のいずれかで返す。

    あくまで429（クォータ超過）発生時にどの案内文を出すかを決めるための
    簡易的な目安であり、実際の無料枠条件を保証するものではない。
    """
    if model_id not in MODEL_ORDER or len(MODEL_ORDER) <= 1:
        return "standard"
    idx = MODEL_ORDER.index(model_id)
    if idx == 0:
        return "lightest"
    if idx == len(MODEL_ORDER) - 1:
        return "heavy"
    return "standard"


def get_lighter_model(model_id: str):
    """指定モデルより一段階軽量なモデルのIDを返す。もっとも軽量な場合はNoneを返す。"""
    if model_id not in MODEL_ORDER:
        return MODEL_ORDER[0] if MODEL_ORDER else None
    idx = MODEL_ORDER.index(model_id)
    if idx <= 0:
        return None
    return MODEL_ORDER[idx - 1]
