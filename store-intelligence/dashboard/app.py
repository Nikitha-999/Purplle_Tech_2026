"""Streamlit dashboard for Store Intelligence."""

from __future__ import annotations

import os
from datetime import date

import httpx
import streamlit as st
from streamlit import st_autorefresh

API_URL = os.getenv("STORE_API_URL", "http://localhost:8000").rstrip("/")
DEFAULT_STORE = os.getenv("STORE_ID", "ST1008")
REFRESH_SECONDS = 5


def fetch_json(path: str, params: dict[str, str] | None = None) -> dict | None:
    try:
        response = httpx.get(path, params=params, timeout=10.0)
        if response.status_code != 200:
            st.error(f"API error {response.status_code}: {response.text}")
            return None
        return response.json()
    except Exception as exc:
        st.error(f"Unable to reach API: {exc}")
        return None


def build_page():
    st.set_page_config(page_title="Store Intelligence Dashboard", layout="wide")
    st.title("Store Intelligence Dashboard")

    with st.sidebar:
        st.header("Configuration")
        store_id = st.text_input("Store ID", DEFAULT_STORE)
        selected_date = st.date_input("Date", date.today())
        st.write(f"Polling every {REFRESH_SECONDS} seconds")
        st.write(f"API: {API_URL}")
        st.markdown("---")
        st.write("Use this dashboard to inspect store trends and CV-derived insights.")

    st_autorefresh(interval=REFRESH_SECONDS * 1000, limit=None, key="dashboard_refresh")

    params = {"date": selected_date.isoformat()}
    metrics = fetch_json(f"{API_URL}/stores/{store_id}/metrics", params)
    funnel = fetch_json(f"{API_URL}/stores/{store_id}/funnel", params)
    heatmap = fetch_json(f"{API_URL}/stores/{store_id}/heatmap", params)
    anomalies = fetch_json(f"{API_URL}/stores/{store_id}/anomalies", params)

    if metrics:
        col1, col2, col3 = st.columns(3)
        col1.metric("Visitors", metrics.get("unique_visitors", 0))
        col1.metric("Conversion Rate", f"{metrics.get('conversion_rate', 0.0):.2%}")
        col1.metric("Queue Depth", metrics.get("current_queue_depth", 0))
        col2.metric("Transactions", metrics.get("total_transactions", 0))
        col2.metric("Queue Abandonment", f"{metrics.get('queue_abandonment_rate', 0.0):.2%}")
        col2.metric("Data As Of", metrics.get("data_as_of", "-"))

    if funnel:
        st.subheader("Funnel")
        funnel_data = {
            stage["label"]: stage["count"] for stage in funnel.get("stages", [])
        }
        st.bar_chart(funnel_data)

    if heatmap:
        st.subheader("Heatmap Zones")
        st.table(heatmap.get("zones", []))
        st.markdown(f"**Data confidence:** {heatmap.get('data_confidence', 'low')}")

    if anomalies is not None:
        st.subheader("Anomalies")
        if anomalies.get("anomalies"):
            for item in anomalies["anomalies"]:
                st.warning(f"{item['anomaly_type']} ({item['severity']}): {item['description']}")
        else:
            st.success("No anomalies detected.")

    st.caption("This dashboard polls the API every 5 seconds.")


if __name__ == "__main__":
    build_page()
