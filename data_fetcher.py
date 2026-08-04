"""Investment Dashboard — yfinance 数据获取模块（带 retry + fallback + NaN 防护）
技术指标：RSI / MACD / 布林带 / KDJ / 多周期均线"""

import math
import time as _time
import yfinance as yf
import pandas as pd
import numpy as np
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


# ══════════════════════════════════════════════════════════
# 技术指标计算
# ══════════════════════════════════════════════════════════

def _calc_rsi(series: pd.Series, period: int = 14) -> Optional[float]:
    """RSI — 相对强弱指数"""
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


def _calc_macd(closes: pd.Series) -> dict:
    """MACD — 指数平滑异同移动平均线
    返回: {macd_line, signal_line, histogram, signal}"""
    if len(closes) < 35:
        return {}
    try:
        ema12 = closes.ewm(span=12, adjust=False).mean()
        ema26 = closes.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line

        cur_macd = _safe_float(macd_line.iloc[-1])
        cur_signal = _safe_float(signal_line.iloc[-1])
        cur_hist = _safe_float(histogram.iloc[-1])
        prev_macd = _safe_float(macd_line.iloc[-2])
        prev_signal = _safe_float(signal_line.iloc[-2])

        # 金叉/死叉检测
        macd_signal = None
        if cur_macd is not None and cur_signal is not None and prev_macd is not None and prev_signal is not None:
            if prev_macd <= prev_signal and cur_macd > cur_signal:
                macd_signal = "golden_cross"  # 金叉
            elif prev_macd >= prev_signal and cur_macd < cur_signal:
                macd_signal = "death_cross"  # 死叉

        return {
            "macd_line": round(cur_macd, 4) if cur_macd else None,
            "signal_line": round(cur_signal, 4) if cur_signal else None,
            "histogram": round(cur_hist, 4) if cur_hist else None,
            "signal": macd_signal,
        }
    except Exception:
        return {}


def _calc_bollinger(closes: pd.Series, current_price: Optional[float]) -> dict:
    """布林带 — 波动率通道
    返回: {upper, middle, lower, position, bandwidth_pct}"""
    if len(closes) < 20:
        return {}
    try:
        middle = closes.rolling(window=20).mean()
        std = closes.rolling(window=20).std()
        upper = middle + 2 * std
        lower = middle - 2 * std

        cur_upper = _safe_float(upper.iloc[-1])
        cur_middle = _safe_float(middle.iloc[-1])
        cur_lower = _safe_float(lower.iloc[-1])

        # 价格在带内的位置
        position = "unknown"
        if current_price is not None and cur_upper is not None and cur_lower is not None:
            if current_price >= cur_upper:
                position = "above_upper"
            elif current_price <= cur_lower:
                position = "below_lower"
            else:
                position = "inside"

        # 带宽（波动率指标）
        bandwidth = ((cur_upper - cur_lower) / cur_middle * 100) if (cur_upper and cur_lower and cur_middle) else None

        return {
            "upper": round(cur_upper, 2) if cur_upper else None,
            "middle": round(cur_middle, 2) if cur_middle else None,
            "lower": round(cur_lower, 2) if cur_lower else None,
            "position": position,
            "bandwidth_pct": round(bandwidth, 1) if bandwidth else None,
        }
    except Exception:
        return {}


def _calc_kdj(highs: pd.Series, lows: pd.Series, closes: pd.Series) -> dict:
    """KDJ — 随机指标
    返回: {k, d, j, status}"""
    if len(closes) < 12:
        return {}
    try:
        period = 9
        low_min = lows.rolling(window=period).min()
        high_max = highs.rolling(window=period).max()

        rsv = ((closes - low_min) / (high_max - low_min)) * 100

        # 用简单移动平均迭代 K/D
        k_vals = [50.0] * period
        d_vals = [50.0] * period
        for i in range(period, len(rsv)):
            rsv_i = _safe_float(rsv.iloc[i]) or 50.0
            k_vals.append((2/3) * k_vals[-1] + (1/3) * rsv_i)
            d_vals.append((2/3) * d_vals[-1] + (1/3) * k_vals[-1])

        cur_k = round(k_vals[-1], 2)
        cur_d = round(d_vals[-1], 2)
        cur_j = round(3 * cur_k - 2 * cur_d, 2)

        # 状态判断
        if cur_k > 80 and cur_d > 80:
            status = "overbought"
        elif cur_k < 20 and cur_d < 20:
            status = "oversold"
        else:
            status = "normal"

        return {"k": cur_k, "d": cur_d, "j": cur_j, "status": status}
    except Exception:
        return {}


def _calc_ma_system(closes: pd.Series, current_price: Optional[float]) -> dict:
    """多周期均线系统
    返回: {ma5, ma10, ma20, ma50, ma200, alignment, crosses}"""
    result = {}
    periods = [5, 10, 20, 50, 200]
    ma_values = {}
    for p in periods:
        if len(closes) >= p:
            ma = _safe_float(closes.rolling(window=p).mean().iloc[-1])
            result[f"ma{p}"] = round(ma, 2) if ma else None
            if ma is not None:
                ma_values[p] = ma

    # 均线排列判断
    if len(ma_values) >= 3:
        sorted_periods = sorted(ma_values.keys())
        ma_list = [ma_values[p] for p in sorted_periods]
        if all(ma_list[i] >= ma_list[i+1] for i in range(len(ma_list)-1)):
            result["alignment"] = "bullish"  # 多头排列（短>长）
        elif all(ma_list[i] <= ma_list[i+1] for i in range(len(ma_list)-1)):
            result["alignment"] = "bearish"  # 空头排列（短<长）
        else:
            result["alignment"] = "mixed"

    # 近期交叉检测（MA5/MA20）
    crosses = []
    if 5 in ma_values and 20 in ma_values and len(closes) >= 25:
        ma5_series = closes.rolling(window=5).mean()
        ma20_series = closes.rolling(window=20).mean()
        prev_ma5 = _safe_float(ma5_series.iloc[-2])
        prev_ma20 = _safe_float(ma20_series.iloc[-2])
        cur_ma5 = ma_values.get(5)
        cur_ma20 = ma_values.get(20)
        if prev_ma5 and prev_ma20 and cur_ma5 and cur_ma20:
            if prev_ma5 <= prev_ma20 and cur_ma5 > cur_ma20:
                crosses.append("ma5_cross_above_ma20")
            elif prev_ma5 >= prev_ma20 and cur_ma5 < cur_ma20:
                crosses.append("ma5_cross_below_ma20")
    result["crosses"] = crosses

    return result


# ══════════════════════════════════════════════════════════
# 快照获取
# ══════════════════════════════════════════════════════════

def get_stock_snapshot(ticker: str) -> dict:
    """获取单只股票的实时快照 + 全部技术指标"""
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

        highs = hist["High"].squeeze() if "High" in hist.columns else None
        lows = hist["Low"].squeeze() if "Low" in hist.columns else None
        if isinstance(highs, pd.DataFrame): highs = highs.squeeze()
        if isinstance(lows, pd.DataFrame): lows = lows.squeeze()

        current_price = price or _safe_float(closes.iloc[-1])
        prev_close = _safe_float(closes.iloc[-2]) if len(closes) >= 2 else current_price
        day_change = current_price - prev_close if (current_price is not None and prev_close is not None) else 0
        day_change_pct = (day_change / prev_close) * 100 if prev_close else 0

        # YTD
        ytd_start = datetime(datetime.now().year, 1, 1)
        ytd_data = closes[closes.index >= pd.Timestamp(ytd_start)]
        if not ytd_data.empty:
            ytd_start_price = _safe_float(ytd_data.iloc[0])
            ytd_change_pct = ((current_price - ytd_start_price) / ytd_start_price) * 100 if (ytd_start_price and current_price) else 0
        else:
            ytd_change_pct = 0

        # RSI
        rsi = _calc_rsi(closes, 14)

        # MA20 / MA50 / MA60
        ma20 = _safe_float(closes.rolling(window=20).mean().iloc[-1]) if len(closes) >= 20 else None
        ma50 = _safe_float(closes.rolling(window=50).mean().iloc[-1]) if len(closes) >= 50 else None
        ma60 = _safe_float(closes.rolling(window=60).mean().iloc[-1]) if len(closes) >= 60 else None
        above_ma20 = (current_price > ma20) if (ma20 is not None and current_price is not None) else None
        above_ma50 = (current_price > ma50) if (ma50 is not None and current_price is not None) else None
        above_ma60 = (current_price > ma60) if (ma60 is not None and current_price is not None) else None
        ma50_pct = ((current_price - ma50) / ma50 * 100) if (ma50 and current_price is not None) else None

        # ── 技术指标 ──
        indicators = {
            "macd": _calc_macd(closes),
            "bollinger": _calc_bollinger(closes, current_price),
            "ma_system": _calc_ma_system(closes, current_price),
        }
        if highs is not None and lows is not None:
            indicators["kdj"] = _calc_kdj(highs, lows, closes)
        else:
            indicators["kdj"] = {}

        return {
            "ticker": ticker,
            "price": round(current_price, 2) if current_price is not None else None,
            "day_change": round(day_change, 2) if day_change is not None else 0,
            "day_change_pct": round(day_change_pct, 2) if day_change_pct is not None else 0,
            "ytd_change_pct": round(ytd_change_pct, 2) if ytd_change_pct is not None else 0,
            "rsi": round(rsi, 1) if rsi is not None else None,
            "ma20": round(ma20, 2) if ma20 else None,
            "ma50": round(ma50, 2) if ma50 else None,
            "ma60": round(ma60, 2) if ma60 else None,
            "above_ma20": above_ma20,
            "above_ma50": above_ma50,
            "above_ma60": above_ma60,
            "ma50_pct": round(ma50_pct, 2) if ma50_pct else None,
            "indicators": indicators,
            "error": False,
        }
    except Exception:
        return {
            "ticker": ticker,
            "price": price,
            "error": True,
            "message": "数据处理异常",
        }


def get_index_snapshot(ticker: str) -> dict:
    """获取指数快照"""
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

        ma20 = _safe_float(closes.rolling(window=20).mean().iloc[-1]) if len(closes) >= 20 else None
        ma50 = _safe_float(closes.rolling(window=50).mean().iloc[-1]) if len(closes) >= 50 else None
        ma60 = _safe_float(closes.rolling(window=60).mean().iloc[-1]) if len(closes) >= 60 else None
        above_ma20 = (current > ma20) if (ma20 is not None and current is not None) else None
        above_ma50 = (current > ma50) if (ma50 is not None and current is not None) else None
        above_ma60 = (current > ma60) if (ma60 is not None and current is not None) else None

        return {
            "ticker": ticker,
            "price": round(current, 2) if current is not None else None,
            "day_change_pct": round(day_change_pct, 2) if day_change_pct is not None else 0,
            "ytd_change_pct": round(ytd_pct, 2) if ytd_pct is not None else 0,
            "ma20": round(ma20, 2) if ma20 else None,
            "ma50": round(ma50, 2) if ma50 else None,
            "ma60": round(ma60, 2) if ma60 else None,
            "above_ma20": above_ma20,
            "above_ma50": above_ma50,
            "above_ma60": above_ma60,
            "error": False,
        }
    except Exception:
        return {"ticker": ticker, "error": True}
