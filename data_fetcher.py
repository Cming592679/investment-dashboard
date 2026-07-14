"""Investment Dashboard — yfinance 数据获取模块（带 retry + fallback + NaN 防护）"""

import math
import time as _time
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional


def _safe_float(val) -> Optional[float]:
    """将值转为 float，NaN/Inf 转为 None"""
    if val is None:
        return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None

RETRY_COUNT = 3
RETRY_DELAY = 1.5  # 秒，指数退避


def _safe_download(ticker: str, period: str = "6mo") -> Optional[pd.DataFrame]:
    """安全获取历史数据，带重试 + 指数退避"""
    for attempt in range(RETRY_COUNT):
        try:
            data = yf.download(ticker, period=period, progress=False, auto_adjust=True)
            if data is not None and not data.empty:
                return data
        except Exception:
            pass
        if attempt < RETRY_COUNT - 1:
            _time.sleep(RETRY_DELAY * (2 ** attempt))  # 1.5s, 3s, 6s
    return None


def get_stock_snapshot(ticker: str) -> dict:
    """获取单只股票的实时快照（带 retry）"""
    price = None
    for attempt in range(RETRY_COUNT):
        try:
            stock = yf.Ticker(ticker)
            info = stock.fast_info
            price = info.get("lastPrice") or info.get("regularMarketPreviousClose")
            if price is None:
                data = stock.history(period="5d")
                if not data.empty:
                    price = float(data["Close"].iloc[-1])
            if price is not None:
                break
        except Exception:
            if attempt < RETRY_COUNT - 1:
                _time.sleep(RETRY_DELAY * (2 ** attempt))
            else:
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

        current_price = price or _safe_float(closes.iloc[-1])
        prev_close = _safe_float(closes.iloc[-2]) if len(closes) >= 2 else current_price
        day_change = current_price - prev_close if (current_price is not None and prev_close is not None) else 0
        day_change_pct = (day_change / prev_close) * 100 if prev_close else 0

        # YTD
        ytd_start = datetime(datetime.now().year, 1, 1)
        ytd_data = closes[closes.index >= pd.Timestamp(ytd_start)]
        if not ytd_data.empty:
            ytd_start_price = _safe_float(ytd_data.iloc[0])
            ytd_change = current_price - ytd_start_price if (current_price is not None and ytd_start_price is not None) else 0
            ytd_change_pct = (ytd_change / ytd_start_price) * 100 if ytd_start_price else 0
        else:
            ytd_change_pct = 0

        # Simple RSI (14-day)
        rsi = _calc_rsi(closes, 14)

        # MA50 状态
        ma50 = _safe_float(closes.rolling(window=50).mean().iloc[-1]) if len(closes) >= 50 else None
        above_ma50 = (current_price > ma50) if (ma50 is not None and current_price is not None) else None
        ma50_pct = ((current_price - ma50) / ma50 * 100) if (ma50 and current_price is not None) else None

        return {
            "ticker": ticker,
            "price": round(current_price, 2) if current_price is not None else None,
            "day_change": round(day_change, 2) if day_change is not None else 0,
            "day_change_pct": round(day_change_pct, 2) if day_change_pct is not None else 0,
            "ytd_change_pct": round(ytd_change_pct, 2) if ytd_change_pct is not None else 0,
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
        return _safe_float(rsi.iloc[-1])
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

        current = _safe_float(closes.iloc[-1])
        prev = _safe_float(closes.iloc[-2]) if len(closes) >= 2 else current
        day_change_pct = ((current - prev) / prev) * 100 if prev else 0

        ytd_start = datetime(datetime.now().year, 1, 1)
        ytd_data = closes[closes.index >= pd.Timestamp(ytd_start)]
        if not ytd_data.empty:
            ytd_start_price = _safe_float(ytd_data.iloc[0])
            ytd_pct = ((current - ytd_start_price) / ytd_start_price) * 100 if ytd_start_price else 0
        else:
            ytd_pct = 0

        # MA50 状态
        ma50 = _safe_float(closes.rolling(window=50).mean().iloc[-1]) if len(closes) >= 50 else None
        above_ma50 = (current > ma50) if (ma50 is not None and current is not None) else None

        return {
            "ticker": ticker,
            "price": round(current, 2) if current is not None else None,
            "day_change_pct": round(day_change_pct, 2) if day_change_pct is not None else 0,
            "ytd_change_pct": round(ytd_pct, 2) if ytd_pct is not None else 0,
            "ma50": round(ma50, 2) if ma50 else None,
            "above_ma50": above_ma50,
            "error": False,
        }
    except Exception:
        return {"ticker": ticker, "error": True}
