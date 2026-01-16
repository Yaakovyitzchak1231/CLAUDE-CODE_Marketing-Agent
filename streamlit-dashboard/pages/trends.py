"""
Trends Analysis Dashboard - Market Trend Intelligence

Principles:
- Deterministic scoring (no LLM inference for the score itself)
- Transparent inputs: show the URLs used for each calculation
- No demo/mock trend data shown to users
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import plotly.graph_objects as go
import psycopg2
import requests
import streamlit as st
from psycopg2.extras import RealDictCursor


st.set_page_config(
    page_title="Trends Analysis - Marketing Dashboard",
    page_icon="📈",
    layout="wide",
)


# =========================
# Configuration
# =========================

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "database": os.getenv("POSTGRES_DB", "marketing"),
    "user": os.getenv("POSTGRES_USER", "n8n"),
    "password": os.getenv("POSTGRES_PASSWORD", "n8npassword"),
}

SEARXNG_URL = os.getenv("SEARXNG_URL", "http://searxng:8080")


SOURCE_WEIGHTS = {
    # Only sources that are actually computed in this page are weighted.
    "news_mentions": 0.45,
    "job_postings": 0.35,
    "social_sentiment": 0.20,
}

CREDIBILITY_TIERS = {
    "tier1_authoritative": {"weight": 1.0, "label": "Gov/Academic/Wire"},
    "tier2_business_news": {"weight": 0.8, "label": "Major Business"},
    "tier3_industry_pubs": {"weight": 0.6, "label": "Industry/Tech"},
    "tier4_general_news": {"weight": 0.4, "label": "Other"},
}


# =========================
# DB helpers
# =========================

@st.cache_resource
def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        return conn
    except Exception as e:
        st.warning(f"Database not available: {e}")
        return None


def get_previous_score(topic: str) -> Optional[float]:
    conn = get_db_connection()
    if not conn:
        return None

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT score
                FROM trends
                WHERE topic ILIKE %s
                ORDER BY detected_at DESC
                OFFSET 1
                LIMIT 1
                """,
                (topic,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return float(row["score"]) if row.get("score") is not None else None
    except Exception:
        return None


def save_trend_result(
    topic: str,
    score: float,
    metadata: Dict[str, Any],
    category: Optional[str] = None,
    source: str = "trend_dashboard",
) -> None:
    conn = get_db_connection()
    if not conn:
        return

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO trends (topic, score, category, source, metadata_json, detected_at)
                VALUES (%s, %s, %s, %s, %s::jsonb, %s)
                """,
                (topic, score, category, source, json.dumps(metadata), datetime.utcnow()),
            )
    except Exception as e:
        st.warning(f"Could not store trend result: {e}")


def get_recent_trends(limit: int = 25) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    if not conn:
        return []

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT topic, score, category, source, metadata_json, detected_at
                FROM trends
                ORDER BY detected_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cursor.fetchall()
    except Exception:
        return []


# =========================
# SearXNG helpers
# =========================

@st.cache_data(ttl=900)
def searxng_search(query: str, *, categories: str, time_range: str, max_results: int) -> List[Dict[str, Any]]:
    try:
        response = requests.get(
            f"{SEARXNG_URL}/search",
            params={
                "q": query,
                "format": "json",
                "categories": categories,
                "time_range": time_range,
            },
            timeout=10,
        )
        if response.status_code != 200:
            return []
        results = (response.json() or {}).get("results", []) or []
        return results[:max_results]
    except Exception:
        return []


def tier_news_mentions(results: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
    tier1_domains = [".gov", ".edu", "reuters.com", "apnews.com"]
    tier2_domains = ["wsj.com", "bloomberg.com", "ft.com", "forbes.com", "fortune.com", "businessinsider.com"]
    tier3_domains = ["techcrunch.com", "venturebeat.com", "wired.com", "zdnet.com", "cnet.com"]

    counts = {"tier1_authoritative": 0, "tier2_business_news": 0, "tier3_industry_pubs": 0, "tier4_general_news": 0}
    sources: List[Dict[str, str]] = []

    for r in results:
        url = (r.get("url") or "").lower()
        title = r.get("title") or ""
        if url:
            sources.append({"title": title, "url": r.get("url")})
        if any(d in url for d in tier1_domains):
            counts["tier1_authoritative"] += 1
        elif any(d in url for d in tier2_domains):
            counts["tier2_business_news"] += 1
        elif any(d in url for d in tier3_domains):
            counts["tier3_industry_pubs"] += 1
        else:
            counts["tier4_general_news"] += 1

    return counts, dedupe_sources(sources)


def dedupe_sources(sources: List[Dict[str, str]]) -> List[Dict[str, str]]:
    seen: set[str] = set()
    deduped: List[Dict[str, str]] = []
    for s in sources:
        url = s.get("url") or ""
        if not url or url in seen:
            continue
        seen.add(url)
        deduped.append(s)
    return deduped


def job_postings_signal(results: List[Dict[str, Any]]) -> Tuple[int, List[Dict[str, str]]]:
    job_like = 0
    sources: List[Dict[str, str]] = []
    for r in results:
        title = (r.get("title") or "").lower()
        url = r.get("url") or ""
        if url:
            sources.append({"title": r.get("title") or "", "url": url})
        if any(w in title for w in ["job", "jobs", "hiring", "career", "position", "role"]):
            job_like += 1
    return job_like, dedupe_sources(sources)


def sentiment_signal(results: List[Dict[str, Any]]) -> Tuple[float, int, float, List[Dict[str, str]]]:
    texts: List[str] = []
    sources: List[Dict[str, str]] = []
    for r in results:
        title = r.get("title") or ""
        content = r.get("content") or ""
        url = r.get("url") or ""
        if url:
            sources.append({"title": title, "url": url})
        texts.append(f"{title} {content}".lower())

    positive_words = ["good", "great", "excellent", "amazing", "love", "best", "increase", "growth", "surge"]
    negative_words = ["bad", "poor", "terrible", "hate", "worst", "decline", "drop", "fall", "risk"]
    pos = sum(sum(1 for w in positive_words if w in t) for t in texts)
    neg = sum(sum(1 for w in negative_words if w in t) for t in texts)
    total = pos + neg
    avg_sentiment = (pos - neg) / max(total, 1)
    positive_ratio = pos / max(total, 1)

    return round(avg_sentiment, 3), len(results), round(positive_ratio, 3), dedupe_sources(sources)


def fetch_trend_data(topic: str) -> Dict[str, Any]:
    news_results = searxng_search(topic, categories="news", time_range="month", max_results=25)
    news_counts, news_sources = tier_news_mentions(news_results)

    job_results = searxng_search(f"{topic} jobs hiring", categories="general", time_range="month", max_results=25)
    job_count, job_sources = job_postings_signal(job_results)

    sentiment_results = searxng_search(topic, categories="general", time_range="month", max_results=25)
    avg_sentiment, mention_volume, positive_ratio, social_sources = sentiment_signal(sentiment_results)

    data_sources: Dict[str, Any] = {}

    if any(v > 0 for v in news_counts.values()):
        data_sources["news_mentions"] = {**news_counts, "sample_sources": news_sources[:10]}

    if job_count > 0:
        data_sources["job_postings"] = {"total_postings": job_count, "growth_pct": None, "sample_sources": job_sources[:10]}

    if mention_volume > 0:
        data_sources["social_sentiment"] = {
            "avg_sentiment": avg_sentiment,
            "mention_volume": mention_volume,
            "positive_ratio": positive_ratio,
            "sample_sources": social_sources[:10],
            "method": "keyword_heuristic",
        }

    return data_sources


# =========================
# Deterministic scoring
# =========================

def calculate_trend_score(topic: str, data_sources: Dict[str, Any]) -> Dict[str, Any]:
    scores: Dict[str, float] = {}

    # News mentions score (0-100) - credibility weighted
    if "news_mentions" in data_sources:
        nm = data_sources["news_mentions"]
        tier1 = float(nm.get("tier1_authoritative", 0)) * CREDIBILITY_TIERS["tier1_authoritative"]["weight"]
        tier2 = float(nm.get("tier2_business_news", 0)) * CREDIBILITY_TIERS["tier2_business_news"]["weight"]
        tier3 = float(nm.get("tier3_industry_pubs", 0)) * CREDIBILITY_TIERS["tier3_industry_pubs"]["weight"]
        weighted_mentions = tier1 * 20 + tier2 * 10 + tier3 * 5
        scores["news_mentions"] = min(weighted_mentions, 100.0)

    # Job postings score (0-100)
    if "job_postings" in data_sources:
        jp = data_sources["job_postings"]
        posting_count = float(jp.get("total_postings", 0))
        scores["job_postings"] = min(posting_count * 4.0, 100.0)

    # Social sentiment score (0-100)
    if "social_sentiment" in data_sources:
        ss = data_sources["social_sentiment"]
        sentiment = float(ss.get("avg_sentiment", 0.0))  # -1..1
        volume = float(ss.get("mention_volume", 0))
        sentiment_score = 50.0 + sentiment * 50.0
        volume_multiplier = min(1.0, volume / 1000.0) if volume > 0 else 0.0
        scores["social_sentiment"] = max(0.0, min(100.0, sentiment_score * max(volume_multiplier, 0.25)))

    if not scores:
        return {
            "topic": topic,
            "trend_score": 0.0,
            "error": "No live data sources available",
            "component_scores": {},
            "weights_used": {},
            "sources_count": 0,
            "confidence": "low",
            "direction": "unknown",
            "algorithm": "Multi-source weighted scoring",
            "is_verified": False,
            "calculated_at": datetime.utcnow().isoformat(),
        }

    total_weight = sum(SOURCE_WEIGHTS[k] for k in scores.keys())
    weighted_score = sum(scores[k] * SOURCE_WEIGHTS[k] for k in scores.keys()) / max(total_weight, 1e-9)

    confidence = "high" if len(scores) >= 3 else "medium" if len(scores) == 2 else "low"
    if weighted_score >= 70:
        direction = "strong_positive"
    elif weighted_score >= 55:
        direction = "positive"
    elif weighted_score >= 45:
        direction = "neutral"
    elif weighted_score >= 30:
        direction = "negative"
    else:
        direction = "strong_negative"

    return {
        "topic": topic,
        "trend_score": round(weighted_score, 1),
        "component_scores": {k: round(v, 1) for k, v in scores.items()},
        "weights_used": {k: SOURCE_WEIGHTS[k] for k in scores.keys()},
        "sources_count": len(scores),
        "confidence": confidence,
        "direction": direction,
        "algorithm": "Multi-source weighted scoring",
        "is_verified": True,
        "calculated_at": datetime.utcnow().isoformat(),
    }


def calculate_momentum(current: float, previous: Optional[float]) -> Dict[str, Any]:
    if previous is None or previous == 0:
        return {"is_verified": False}
    momentum_pct = ((current - previous) / previous) * 100.0
    if momentum_pct > 25:
        direction = "surging"
    elif momentum_pct > 10:
        direction = "rising"
    elif momentum_pct > -10:
        direction = "stable"
    elif momentum_pct > -25:
        direction = "declining"
    else:
        direction = "collapsing"
    return {"is_verified": True, "momentum_pct": round(momentum_pct, 2), "direction": direction}


def collect_source_links(data_sources: Dict[str, Any]) -> List[Dict[str, str]]:
    links: List[Dict[str, str]] = []
    for source in data_sources.values():
        if not isinstance(source, dict):
            continue
        for item in source.get("sample_sources", []) or []:
            url = item.get("url")
            if url:
                links.append({"title": item.get("title", ""), "url": url})
    return dedupe_sources(links)


# =========================
# UI
# =========================

def main():
    st.title("Trends Analysis")
    st.caption("Deterministic scoring with transparent source URLs (no demo data).")

    with st.sidebar:
        st.subheader("Scoring Weights")
        st.write(SOURCE_WEIGHTS)
        st.caption("Weights are fixed to keep results comparable over time.")

    col1, col2 = st.columns([3, 1])
    with col1:
        topic = st.text_input("Topic", placeholder="e.g., AI automation, remote work tools, cybersecurity")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        analyze = st.button("Analyze", type="primary", use_container_width=True)

    if analyze and topic:
        with st.spinner("Fetching live sources (SearXNG)..."):
            data_sources = fetch_trend_data(topic)

        if not data_sources:
            st.error("No live data sources available. Ensure `searxng` is running and reachable.")
            return

        with st.spinner("Calculating deterministic score..."):
            result = calculate_trend_score(topic, data_sources)
            previous = get_previous_score(topic)
            momentum = calculate_momentum(result.get("trend_score", 0.0), previous)
            links = collect_source_links(data_sources)

        st.markdown("---")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Trend Score", f"{result.get('trend_score', 0)}/100")
        with m2:
            st.metric("Confidence", result.get("confidence", "low").upper(), delta=f"{result.get('sources_count', 0)} sources")
        with m3:
            st.metric("Direction", result.get("direction", "unknown").replace("_", " ").title())
        with m4:
            if momentum.get("is_verified"):
                st.metric("Momentum", momentum["direction"].title(), delta=f"{momentum['momentum_pct']:+.1f}%")
            else:
                st.metric("Momentum", "N/A")

        component_scores = result.get("component_scores", {})
        if component_scores:
            df_scores = pd.DataFrame([{"Source": k.replace("_", " ").title(), "Score": v} for k, v in component_scores.items()])
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df_scores["Source"], y=df_scores["Score"], marker_color="#667eea"))
            fig.update_layout(height=320, showlegend=False, yaxis_title="Score (0-100)", yaxis_range=[0, 100])
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Sources Used")
        if links:
            for link in links[:12]:
                st.write(f"- {link['title']} ({link['url']})")
        else:
            st.info("No URLs returned by SearXNG for this query.")

        # Persist the result in DB (no demo values; all metadata derived from live sources)
        metadata = {
            "data_sources": data_sources,
            "result": result,
            "momentum": momentum if momentum.get("is_verified") else None,
            "source_links": links,
        }
        save_trend_result(topic=topic, score=float(result.get("trend_score", 0.0)), metadata=metadata)
        st.success("Saved trend analysis to database.")

    st.markdown("---")
    st.subheader("Recent Trend Analyses")
    rows = get_recent_trends(limit=25)
    if not rows:
        st.info("No trend analyses stored yet.")
        return

    df = pd.DataFrame(
        [
            {
                "topic": r.get("topic"),
                "score": float(r.get("score") or 0),
                "source": r.get("source"),
                "detected_at": r.get("detected_at"),
            }
            for r in rows
        ]
    )
    st.dataframe(df, use_container_width=True)


if __name__ == "__main__":
    main()
