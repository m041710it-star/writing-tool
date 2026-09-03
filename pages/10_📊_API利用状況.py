from datetime import date

import streamlit as st

from utils import usage_tracker
from utils.common import render_sidebar, render_usage_progress

render_sidebar()

st.title("📊 API利用状況")
st.caption("トークン数・概算コストの履歴、課金履歴、単価設定をここで管理します。")

st.subheader("残高の目安")
render_usage_progress(target=st)

st.divider()

st.subheader("💰 課金履歴")

if not usage_tracker.get_paid_mode():
    st.info(
        "現在は無料枠でご利用中です。「⚙️ 設定」ページで「有料利用に切り替えました」を"
        "ONにすると、ここから課金履歴を入力できるようになります。"
    )
else:
    with st.form("billing_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            billing_date = st.date_input("日付", value=date.today())
        with col2:
            billing_amount = st.number_input("金額（円）", min_value=0, step=100)
        billing_submitted = st.form_submit_button("追加")

    if billing_submitted:
        if billing_amount > 0:
            usage_tracker.add_billing_entry(billing_date.isoformat(), billing_amount)
            st.success(f"{billing_date} に ¥{billing_amount:,.0f} を記録しました。")
            st.rerun()
        else:
            st.warning("金額を入力してください。")

    billing_records = usage_tracker.get_billing_records()
    if billing_records:
        st.dataframe(
            [
                {"日付": b["date"], "金額（円）": f"¥{b['amount_yen']:,.0f}"}
                for b in sorted(billing_records, key=lambda b: b["date"], reverse=True)
            ],
            use_container_width=True,
            hide_index=True,
        )
        st.caption(f"課金累計: ¥{sum(b['amount_yen'] for b in billing_records):,.0f}")
    else:
        st.caption("まだ課金履歴が記録されていません。")

st.divider()

st.subheader("⚙️ 単価設定")

pricing = usage_tracker.get_pricing()
with st.form("pricing_form"):
    col1, col2 = st.columns(2)
    with col1:
        input_price = st.number_input(
            "入力単価（100万トークンあたり円）",
            min_value=0.0,
            value=float(pricing["input_price_per_million"]),
            step=1.0,
        )
    with col2:
        output_price = st.number_input(
            "出力単価（100万トークンあたり円）",
            min_value=0.0,
            value=float(pricing["output_price_per_million"]),
            step=1.0,
        )
    pricing_submitted = st.form_submit_button("保存")

if pricing_submitted:
    usage_tracker.set_pricing(input_price, output_price)
    st.success("単価を保存しました。")
    st.rerun()

st.caption(
    "デフォルト値はGemini Flash-Liteの目安単価です。実際の料金体系に合わせて調整してください。"
)

st.divider()

st.subheader("📈 利用履歴")

records = usage_tracker.get_usage_records()
if records:
    sorted_records = sorted(records, key=lambda r: r["timestamp"], reverse=True)
    st.dataframe(
        [
            {
                "日時": r["timestamp"],
                "ページ": r["page"],
                "入力トークン": r["input_tokens"],
                "出力トークン": r["output_tokens"],
                "概算コスト（円）": round(r["cost_yen"], 2),
            }
            for r in sorted_records
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("**日ごとの小計**")
    daily = usage_tracker.compute_daily_subtotals()
    st.dataframe(
        [
            {
                "日付": d["date"],
                "回数": d["count"],
                "入力トークン": d["input_tokens"],
                "出力トークン": d["output_tokens"],
                "概算コスト（円）": round(d["cost_yen"], 2),
            }
            for d in daily
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("**機能（ページ）ごとの小計**")
    per_page = usage_tracker.compute_page_subtotals()
    st.dataframe(
        [
            {
                "ページ": p["page"],
                "回数": p["count"],
                "入力トークン": p["input_tokens"],
                "出力トークン": p["output_tokens"],
                "概算コスト（円）": round(p["cost_yen"], 2),
            }
            for p in per_page
        ],
        use_container_width=True,
        hide_index=True,
    )
else:
    st.caption("まだ利用履歴がありません。各ページで生成を行うと、ここに記録されます。")
