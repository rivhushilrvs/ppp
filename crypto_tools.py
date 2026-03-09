import requests
from datetime import datetime
from typing import Any
from langchain_core.tools import tool


TOP_10_IDS = [
    "bitcoin", "ethereum", "tether", "binancecoin", "solana",
    "usd-coin", "xrp", "dogecoin", "toncoin", "cardano"
]

TOP_10_SYMBOLS = {
    "bitcoin": "BTC", "ethereum": "ETH", "tether": "USDT",
    "binancecoin": "BNB", "solana": "SOL", "usd-coin": "USDC",
    "xrp": "XRP", "dogecoin": "DOGE", "toncoin": "TON", "cardano": "ADA"
}


@tool
def get_crypto_prices(coins: list[str] = None) -> dict[str, Any]:
    """
    Fetch real-time prices and 24h % change for top 10 cryptocurrencies.
    Returns price in USD, 24h change %, market cap, and volume.
    Use this when the user asks about crypto prices, gains, losses, or market data.
    """
    ids = coins if coins else TOP_10_IDS
    ids_str = ",".join(ids)
    url = (
        f"https://api.coingecko.com/api/v3/coins/markets"
        f"?vs_currency=usd&ids={ids_str}"
        f"&order=market_cap_desc&per_page=10&page=1"
        f"&sparkline=false&price_change_percentage=24h"
    )
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        result = {}
        for coin in data:
            change = coin.get("price_change_percentage_24h") or 0
            result[coin["symbol"].upper()] = {
                "name": coin["name"],
                "price_usd": round(coin["current_price"], 4),
                "change_24h_pct": round(change, 2),
                "direction": "▲ UP" if change >= 0 else "▼ DOWN",
                "market_cap_usd": coin.get("market_cap"),
                "volume_24h_usd": coin.get("total_volume"),
                "last_updated": coin.get("last_updated", datetime.utcnow().isoformat()),
            }
        return {"status": "success", "data": result, "fetched_at": datetime.utcnow().isoformat()}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@tool
def get_single_coin_price(coin_name: str) -> dict[str, Any]:
    """
    Fetch real-time price for a specific cryptocurrency by name or symbol.
    E.g. 'bitcoin', 'BTC', 'ethereum', 'ETH', 'solana', 'SOL'.
    Use this when the user asks about a specific coin's price.
    """
    name_map = {
        "btc": "bitcoin", "eth": "ethereum", "sol": "solana",
        "bnb": "binancecoin", "xrp": "xrp", "doge": "dogecoin",
        "ada": "cardano", "ton": "toncoin", "usdt": "tether", "usdc": "usd-coin"
    }
    coin_id = name_map.get(coin_name.lower(), coin_name.lower())
    url = (
        f"https://api.coingecko.com/api/v3/coins/markets"
        f"?vs_currency=usd&ids={coin_id}&price_change_percentage=24h"
    )
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return {"status": "error", "message": f"Coin '{coin_name}' not found."}
        coin = data[0]
        change = coin.get("price_change_percentage_24h") or 0
        return {
            "status": "success",
            "name": coin["name"],
            "symbol": coin["symbol"].upper(),
            "price_usd": round(coin["current_price"], 4),
            "change_24h_pct": round(change, 2),
            "direction": "▲ UP" if change >= 0 else "▼ DOWN",
            "high_24h": coin.get("high_24h"),
            "low_24h": coin.get("low_24h"),
            "market_cap_usd": coin.get("market_cap"),
            "volume_24h_usd": coin.get("total_volume"),
            "ath": coin.get("ath"),
            "last_updated": coin.get("last_updated"),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@tool
def get_crypto_news(query: str = "cryptocurrency") -> dict[str, Any]:
    """
    Fetch latest crypto news headlines using CryptoPanic public API.
    Use this when the user asks for news, updates, or recent events about crypto.
    Query can be a coin name like 'bitcoin', 'ethereum', or 'crypto'.
    """
    url = f"https://cryptopanic.com/api/v1/posts/?auth_token=pub_free&kind=news&filter=rising&public=true"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        articles = data.get("results", [])[:8]
        news_list = []
        for a in articles:
            news_list.append({
                "title": a.get("title"),
                "url": a.get("url"),
                "published_at": a.get("published_at"),
                "source": a.get("source", {}).get("title", "Unknown"),
                "currencies": [c.get("code") for c in a.get("currencies", [])]
            })
        return {
            "status": "success",
            "query": query,
            "count": len(news_list),
            "articles": news_list,
            "fetched_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        # Fallback to CoinGecko news if CryptoPanic fails
        try:
            fallback_url = "https://api.coingecko.com/api/v3/news"
            r2 = requests.get(fallback_url, timeout=10)
            r2.raise_for_status()
            items = r2.json().get("data", [])[:8]
            news_list = [{"title": i.get("title"), "url": i.get("url"),
                          "published_at": i.get("updated_at"), "source": i.get("author", "CoinGecko")}
                         for i in items]
            return {"status": "success", "query": query, "count": len(news_list),
                    "articles": news_list, "fetched_at": datetime.utcnow().isoformat()}
        except Exception as e2:
            return {"status": "error", "message": str(e2)}


@tool
def get_market_summary() -> dict[str, Any]:
    """
    Get global crypto market summary: total market cap, BTC dominance, 24h volume.
    Use when the user asks about overall market conditions or market cap.
    """
    url = "https://api.coingecko.com/api/v3/global"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        d = resp.json().get("data", {})
        return {
            "status": "success",
            "total_market_cap_usd": d.get("total_market_cap", {}).get("usd"),
            "total_volume_24h_usd": d.get("total_volume", {}).get("usd"),
            "btc_dominance_pct": round(d.get("market_cap_percentage", {}).get("btc", 0), 2),
            "eth_dominance_pct": round(d.get("market_cap_percentage", {}).get("eth", 0), 2),
            "active_cryptocurrencies": d.get("active_cryptocurrencies"),
            "market_cap_change_24h_pct": round(d.get("market_cap_change_percentage_24h_usd", 0), 2),
            "fetched_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}





@tool
def get_price_trend(coin_name: str) -> dict[str, Any]:
    """
    Analyze whether a cryptocurrency is likely to rise or fall based on:
    - 1h, 24h, 7d price change
    - Volume trend
    - Price vs 7-day high/low position
    Use this when user asks if a coin will go up or down, rise or fall.
    """
    name_map = {
        "btc": "bitcoin", "eth": "ethereum", "sol": "solana",
        "bnb": "binancecoin", "xrp": "xrp", "doge": "dogecoin",
        "ada": "cardano", "ton": "toncoin", "usdt": "tether", "usdc": "usd-coin"
    }
    coin_id = name_map.get(coin_name.lower(), coin_name.lower())
    url = (
        f"https://api.coingecko.com/api/v3/coins/markets"
        f"?vs_currency=usd&ids={coin_id}"
        f"&price_change_percentage=1h,24h,7d"
    )
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return {"status": "error", "message": f"Coin '{coin_name}' not found."}
        c = data[0]

        change_1h  = c.get("price_change_percentage_1h_in_currency") or 0
        change_24h = c.get("price_change_percentage_24h_in_currency") or 0
        change_7d  = c.get("price_change_percentage_7d_in_currency") or 0
        current    = c.get("current_price", 0)
        high_24h   = c.get("high_24h", current)
        low_24h    = c.get("low_24h", current)
        volume     = c.get("total_volume", 0)
        market_cap = c.get("market_cap", 0)

        # Score: positive = bullish, negative = bearish
        score = 0
        signals = []

        if change_1h > 0:
            score += 1
            signals.append(f"📈 Up {change_1h:.2f}% in last 1 hour")
        else:
            score -= 1
            signals.append(f"📉 Down {abs(change_1h):.2f}% in last 1 hour")

        if change_24h > 0:
            score += 2
            signals.append(f"📈 Up {change_24h:.2f}% in last 24 hours")
        else:
            score -= 2
            signals.append(f"📉 Down {abs(change_24h):.2f}% in last 24 hours")

        if change_7d > 0:
            score += 2
            signals.append(f"📈 Up {change_7d:.2f}% over last 7 days")
        else:
            score -= 2
            signals.append(f"📉 Down {abs(change_7d):.2f}% over last 7 days")

        # Where is price within 24h range?
        if high_24h != low_24h:
            position = (current - low_24h) / (high_24h - low_24h)
            if position > 0.7:
                score += 1
                signals.append(f"💪 Trading near 24h HIGH (strong momentum)")
            elif position < 0.3:
                score -= 1
                signals.append(f"⚠️ Trading near 24h LOW (weak momentum)")
            else:
                signals.append(f"➡️ Trading in middle of 24h range")

        # Volume/market cap ratio (high = active interest)
        if market_cap > 0:
            vol_ratio = volume / market_cap
            if vol_ratio > 0.15:
                score += 1
                signals.append(f"🔥 Very high trading volume (strong interest)")
            elif vol_ratio > 0.05:
                signals.append(f"📊 Normal trading volume")
            else:
                score -= 1
                signals.append(f"😴 Low trading volume (weak interest)")

        if score >= 3:
            verdict = "🚀 LIKELY TO RISE"
            confidence = "High"
            reasoning = "Multiple bullish signals across short and long timeframes."
        elif score >= 1:
            verdict = "📈 SLIGHT UPWARD BIAS"
            confidence = "Moderate"
            reasoning = "More bullish signals than bearish, but not conclusive."
        elif score == 0:
            verdict = "➡️ NEUTRAL / UNCERTAIN"
            confidence = "Low"
            reasoning = "Mixed signals — could go either way."
        elif score >= -2:
            verdict = "📉 SLIGHT DOWNWARD BIAS"
            confidence = "Moderate"
            reasoning = "More bearish signals than bullish."
        else:
            verdict = "⚠️ LIKELY TO FALL"
            confidence = "High"
            reasoning = "Multiple bearish signals across timeframes."

        return {
            "status": "success",
            "coin": c["name"],
            "symbol": c["symbol"].upper(),
            "current_price_usd": current,
            "verdict": verdict,
            "confidence": confidence,
            "score": score,
            "reasoning": reasoning,
            "signals": signals,
            "change_1h_pct": round(change_1h, 2),
            "change_24h_pct": round(change_24h, 2),
            "change_7d_pct": round(change_7d, 2),
            "disclaimer": "This is technical signal analysis only, NOT financial advice.",
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

ALL_TOOLS = [get_crypto_prices, get_single_coin_price, get_crypto_news, get_market_summary, get_price_trend]