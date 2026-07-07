"""半导体设备监控仪表盘 — yfinance 数据获取模块"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional


def _safe_download(ticker: str, period: str = "6mo") -> Optional[pd.DataFrame]:
    """安全获取历史数据，网络异常返回 None"""
    try:
        data = yf.download(ticker, period=period, progress=False, auto_adjust=True)
        if data.empty:
            return None
        return data
    except Exception:
        return None


def get_stock_snapshot(ticker: str) -> dict:
    """获取单只股票的实时快照"""
    # 尝试通过 fast_info 获取实时价格
    try:
        stock = yf.Ticker(ticker)
        info = stock.fast_info
        price = info.get("lastPrice") or info.get("regularMarketPreviousClose")
        if price is None:
            # fallback 到昨日收盘
            data = stock.history(period="5d")
            if not data.empty:
                price = float(data["Close"].iloc[-1])
    except Exception:
        price = None

    # 历史数据用于计算变化
    hist = _safe_download(ticker, period="6mo")
    if hist is None or hist.empty:
        return {
            "ticker": ticker,
            "price": price,
            "error": True,
            "message": "数据获取失败",
        }

    try:
        closes = hist["Close"].squeeze()
        if not isinstance(closes, pd.Series):
            closes = pd.Series(closes, index=hist.index)

        current_price = price or float(closes.iloc[-1])
        prev_close = float(closes.iloc[-2]) if len(closes) >= 2 else current_price
        day_change = current_price - prev_close
        day_change_pct = (day_change / prev_close) * 100 if prev_close else 0

        # YTD
        ytd_start = datetime(datetime.now().year, 1, 1)
        ytd_data = closes[closes.index >= pd.Timestamp(ytd_start)]
        if not ytd_data.empty:
            ytd_start_price = float(ytd_data.iloc[0])
            ytd_change = current_price - ytd_start_price
            ytd_change_pct = (ytd_change / ytd_start_price) * 100
        else:
            ytd_change_pct = 0

        # Simple RSI (14-day)
        rsi = _calc_rsi(closes, 14)

        # MA50 状态
        ma50 = float(closes.rolling(window=50).mean().iloc[-1]) if len(closes) >= 50 else None
        above_ma50 = (current_price > ma50) if ma50 is not None else None
        ma50_pct = ((current_price - ma50) / ma50 * 100) if ma50 else None

        return {
            "ticker": ticker,
            "price": round(current_price, 2),
            "day_change": round(day_change, 2),
            "day_change_pct": round(day_change_pct, 2),
            "ytd_change_pct": round(ytd_change_pct, 2),
            "rsi": round(rsi, 1) if rsi is not None else None,
            "ma50": round(ma50, 2) if ma50 else None,
            "above_ma50": above_ma50,
            "ma50_pct": round(ma50_pct, 2) if ma50_pct else None,
            "error": False,
        }
    except Exception:
        return {
            "ticker": ticker,
            "price": price,
            "error": True,
            "message": "数据处理异常",
        }


def _calc_rsi(series: pd.Series, period: int = 14) -> Optional[float]:
    """计算 RSI"""
    if len(series) < period + 1:
        return None
    try:
        delta = series.diff()
        gain = delta.where(delta > 0, 0.0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])
    except Exception:
        return None


def get_index_snapshot(ticker: str) -> dict:
    """获取指数快照（SOX 等）"""
    hist = _safe_download(ticker, period="6mo")
    if hist is None or hist.empty:
        return {"ticker": ticker, "error": True}

    try:
        closes = hist["Close"].squeeze()
        if not isinstance(closes, pd.Series):
            closes = pd.Series(closes, index=hist.index)

        current = float(closes.iloc[-1])
        prev = float(closes.iloc[-2]) if len(closes) >= 2 else current
        day_change_pct = ((current - prev) / prev) * 100 if prev else 0

        ytd_start = datetime(datetime.now().year, 1, 1)
        ytd_data = closes[closes.index >= pd.Timestamp(ytd_start)]
        if not ytd_data.empty:
            ytd_pct = ((current - float(ytd_data.iloc[0])) / float(ytd_data.iloc[0])) * 100
        else:
            ytd_pct = 0

        # MA50 状态
        ma50 = float(closes.rolling(window=50).mean().iloc[-1]) if len(closes) >= 50 else None
        above_ma50 = (current > ma50) if ma50 is not None else None

        return {
            "ticker": ticker,
            "price": round(current, 2),
            "day_change_pct": round(day_change_pct, 2),
            "ytd_change_pct": round(ytd_pct, 2),
            "ma50": round(ma50, 2) if ma50 else None,
            "above_ma50": above_ma50,
            "error": False,
        }
    except Exception:
        return {"ticker": ticker, "error": True}
