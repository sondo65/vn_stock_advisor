from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import math
import time
import random

import pandas as pd


DEFAULT_CRITERIA: Dict[str, Any] = {
    # a) Growth & profitability
    "eps_growth_years": 2,  # positive years consecutively
    "roe_min": 12.0,
    "roa_min": 5.0,
    # b) Valuation
    "pe_max": 9.0,
    "pb_max": 1.2,
    # c) Financial health
    "debt_assets_max_pct": 50.0,
    "current_ratio_min": 1.0,
    # d) Stability & dividend
    "dividend_years_min": 3,
    "gross_margin_min": 20.0,
    # e) Liquidity & risk
    "avg20d_volume_min": 200_000,
    "beta_max": 1.2,
}


@dataclass
class StockMetrics:
    symbol: str
    pe: Optional[float] = None
    pb: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    eps_history: Optional[List[Tuple[str, float]]] = None  # [(year, eps), ...]
    debt_assets_pct: Optional[float] = None
    current_ratio: Optional[float] = None
    dividend_years: Optional[int] = None
    gross_margin: Optional[float] = None
    avg20d_volume: Optional[int] = None
    beta: Optional[float] = None


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return None
        return float(value)
    except Exception:
        return None


def _get_vnstock_handles(symbol: str):
    # Lazy import to avoid heavy import costs when not used
    from vnstock import Vnstock

    last_error = None
    sources = ["VCI", "TCBS", "DNSE", "SSI"]
    random.shuffle(sources)
    for source in sources:
        # Retry a couple of times per source with small backoff
        for attempt in range(3):
            try:
                stock = Vnstock().stock(symbol=symbol, source=source)
                return stock
            except Exception as e:
                last_error = e
                msg = str(e).lower()
                # If rate limit or gateway errors, wait longer
                if "too many" in msg or "429" in msg or "502" in msg or "bad gateway" in msg:
                    time.sleep(2.0 + attempt * 1.0)
                else:
                    time.sleep(random.uniform(0.3, 0.9))
                continue
    raise last_error or RuntimeError("Unable to init vnstock")


def _fetch_metrics(symbol: str) -> StockMetrics:
    stock = _get_vnstock_handles(symbol)

    pe = pb = roe = roa = None
    eps_hist: List[Tuple[str, float]] = []
    debt_assets_pct = None
    current_ratio = None
    dividend_years = None
    gross_margin = None
    avg20d_volume = None
    beta = None

    # Financial ratios (quarterly and yearly)
    try:
        ratios_q = stock.finance.ratio(period="quarter")
    except Exception:
        ratios_q = None

    try:
        ratios_y = stock.finance.ratio(period="year")
    except Exception:
        ratios_y = None

    # Income statement for gross margin if needed
    try:
        income_y = stock.finance.income_statement(period="year")
    except Exception:
        income_y = None

    # Price history for avg20d volume
    try:
        # Try to get last ~30 trading days; vnstock v2 may provide .price.history
        # We'll attempt a generic recent range fetch via .price.history with count
        price_df = None
        try:
            price_df = stock.price.history(count=30)
        except Exception:
            pass
        if price_df is not None and not price_df.empty:
            vol_col = None
            for candidate in ("volume", "vol", "total_vol", "nm_volume"):
                if candidate in price_df.columns:
                    vol_col = candidate
                    break
            if vol_col:
                avg20 = (
                    price_df[vol_col].head(20).astype(float).mean()
                    if len(price_df) >= 20
                    else price_df[vol_col].astype(float).mean()
                )
                avg20d_volume = int(avg20) if pd.notna(avg20) else None
    except Exception:
        pass

    # Beta may exist in ratios
    # Extract latest available ratios row helper
    def latest_row(df: Optional[pd.DataFrame]) -> Optional[pd.Series]:
        if df is None or df.empty:
            return None
        # Different sources order differently; try last then first
        try:
            return df.iloc[0]
        except Exception:
            try:
                return df.iloc[-1]
            except Exception:
                return None

    r_q = latest_row(ratios_q)
    r_y = latest_row(ratios_y)

    def get_any(series: Optional[pd.Series], keys: List[str]) -> Optional[float]:
        if series is None:
            return None
        for k in keys:
            if k in series:
                v = _safe_float(series.get(k))
                if v is not None:
                    return v
        return None

    pe = get_any(r_q, ["price_to_earning", "pe"]) or get_any(r_y, ["price_to_earning", "pe"])
    pb = get_any(r_q, ["price_to_book", "pb"]) or get_any(r_y, ["price_to_book", "pb"])
    roe = get_any(r_q, ["roe"]) or get_any(r_y, ["roe"])
    roa = get_any(r_q, ["roa"]) or get_any(r_y, ["roa"])
    gross_margin = get_any(r_q, ["gross_profit_margin"]) or get_any(r_y, ["gross_profit_margin"])
    current_ratio = get_any(r_q, ["current_ratio"]) or get_any(r_y, ["current_ratio"])
    beta = get_any(r_q, ["beta"]) or get_any(r_y, ["beta"])

    # Debt / Assets %; try several keys
    debt_assets_pct = (
        get_any(r_q, ["debt_on_assets", "debt_to_assets"]) or get_any(r_y, ["debt_on_assets", "debt_to_assets"]) or None
    )
    if debt_assets_pct is not None and debt_assets_pct > 1.5:
        # Some sources store as ratio (0-1); convert to % if needed
        debt_assets_pct = debt_assets_pct if debt_assets_pct > 100 else debt_assets_pct

    # EPS history (yearly) for growth check
    if ratios_y is not None and not ratios_y.empty:
        # Try to find a year column or index
        possible_eps_cols = ["earning_per_share", "eps"]
        eps_col = None
        for c in possible_eps_cols:
            if c in ratios_y.columns:
                eps_col = c
                break
        if eps_col:
            # Assume top is latest; collect 5 rows if available
            take = min(5, len(ratios_y))
            subset = ratios_y.head(take)
            for i in range(len(subset)):
                row = subset.iloc[i]
                year_label = str(row.get("year", f"y{i}"))
                eps_val = _safe_float(row.get(eps_col))
                if eps_val is not None:
                    eps_hist.append((year_label, eps_val))

    # Dividend years: attempt to read dividend/cash dividend tables if available
    try:
        company = _get_vnstock_handles(symbol).company
        div_df = None
        for method in ("dividend", "cash_dividend", "dividends"):
            if hasattr(company, method):
                try:
                    div_df = getattr(company, method)()
                    if div_df is not None and not div_df.empty:
                        break
                except Exception:
                    continue
        if div_df is not None and not div_df.empty:
            # Count distinct latest years with positive cash dividend
            year_col = None
            for c in ("year", "ex_year", "exYear", "record_year"):
                if c in div_df.columns:
                    year_col = c
                    break
            cash_col = None
            for c in ("cash", "cash_dividend", "dividend_cash", "cashDividend"):
                if c in div_df.columns:
                    cash_col = c
                    break
            if year_col:
                df_years = div_df.copy()
                if cash_col and cash_col in df_years:
                    df_years = df_years[df_years[cash_col].fillna(0) > 0]
                dividend_years = df_years[year_col].dropna().astype(int).nunique()
    except Exception:
        pass

    return StockMetrics(
        symbol=symbol,
        pe=pe,
        pb=pb,
        roe=roe,
        roa=roa,
        eps_history=eps_hist or None,
        debt_assets_pct=debt_assets_pct,
        current_ratio=current_ratio,
        dividend_years=dividend_years,
        gross_margin=gross_margin,
        avg20d_volume=avg20d_volume,
        beta=beta,
    )


def _check_eps_growth_positive(eps_hist: Optional[List[Tuple[str, float]]], min_years: int) -> bool:
    if not eps_hist or len(eps_hist) < min_years:
        return False
    # Assume list is newest-first; check consecutive positives
    positives = 0
    for _, v in eps_hist:
        if v is not None and v > 0:
            positives += 1
        else:
            break
    return positives >= min_years


def _evaluate(metrics: StockMetrics, criteria: Dict[str, Any]) -> Tuple[Dict[str, bool], float, str, str]:
    checks: Dict[str, bool] = {}

    # Growth & profitability
    checks["eps_growth_positive"] = _check_eps_growth_positive(
        metrics.eps_history, int(criteria.get("eps_growth_years", DEFAULT_CRITERIA["eps_growth_years"]))
    )
    checks["roe_min"] = metrics.roe is not None and metrics.roe >= float(criteria.get("roe_min", DEFAULT_CRITERIA["roe_min"]))
    checks["roa_min"] = metrics.roa is not None and metrics.roa >= float(criteria.get("roa_min", DEFAULT_CRITERIA["roa_min"]))

    # Valuation
    checks["pe_max"] = metrics.pe is not None and metrics.pe <= float(criteria.get("pe_max", DEFAULT_CRITERIA["pe_max"]))
    checks["pb_max"] = metrics.pb is not None and metrics.pb <= float(criteria.get("pb_max", DEFAULT_CRITERIA["pb_max"]))

    # Financial health
    checks["debt_assets_max_pct"] = (
        metrics.debt_assets_pct is not None
        and metrics.debt_assets_pct <= float(criteria.get("debt_assets_max_pct", DEFAULT_CRITERIA["debt_assets_max_pct"]))
    )
    checks["current_ratio_min"] = (
        metrics.current_ratio is not None
        and metrics.current_ratio >= float(criteria.get("current_ratio_min", DEFAULT_CRITERIA["current_ratio_min"]))
    )

    # Stability & dividend
    checks["dividend_years_min"] = (
        metrics.dividend_years is not None
        and metrics.dividend_years >= int(criteria.get("dividend_years_min", DEFAULT_CRITERIA["dividend_years_min"]))
    )
    checks["gross_margin_min"] = (
        metrics.gross_margin is not None
        and metrics.gross_margin >= float(criteria.get("gross_margin_min", DEFAULT_CRITERIA["gross_margin_min"]))
    )

    # Liquidity & risk
    checks["avg20d_volume_min"] = (
        metrics.avg20d_volume is not None
        and metrics.avg20d_volume >= int(criteria.get("avg20d_volume_min", DEFAULT_CRITERIA["avg20d_volume_min"]))
    )
    checks["beta_max"] = metrics.beta is not None and metrics.beta <= float(criteria.get("beta_max", DEFAULT_CRITERIA["beta_max"]))

    # Score: equally weight available checks
    available = [v for v in checks.values() if isinstance(v, bool)]
    if available:
        score = 100.0 * (sum(1 for v in available if v) / len(available))
    else:
        score = 0.0

    # Rating
    if score >= 80:
        rating = "⭐⭐⭐⭐"  # 4/5
        conclusion = "Tiềm năng"
    elif score >= 60:
        rating = "⭐⭐⭐"
        conclusion = "Cần theo dõi"
    else:
        rating = "⭐⭐"
        conclusion = "Loại"

    return checks, float(round(score, 2)), rating, conclusion


def find_potential_stocks(stock_list: List[str], criteria: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """Scan a list of stock symbols and return a scored DataFrame.

    Columns include metrics, pass/fail per criterion, total score (0-100), a star rating,
    and a conclusion label ("Tiềm năng" / "Cần theo dõi" / "Loại").
    """
    if not stock_list:
        return pd.DataFrame()

    criteria = {**DEFAULT_CRITERIA, **(criteria or {})}

    rows: List[Dict[str, Any]] = []

    for symbol in stock_list:
        try:
            metrics = _fetch_metrics(symbol)
            checks, score, rating, conclusion = _evaluate(metrics, criteria)

            row: Dict[str, Any] = {
                "symbol": metrics.symbol,
                # Core metrics
                "PE": metrics.pe,
                "PB": metrics.pb,
                "ROE": metrics.roe,
                "ROA": metrics.roa,
                "DebtAssetsPct": metrics.debt_assets_pct,
                "CurrentRatio": metrics.current_ratio,
                "GrossMargin": metrics.gross_margin,
                "Avg20dVolume": metrics.avg20d_volume,
                "Beta": metrics.beta,
                # Derived
                "EPS_PositiveYears": (
                    sum(1 for _, v in (metrics.eps_history or []) if v is not None and v > 0)
                    if metrics.eps_history
                    else None
                ),
                "DividendYears": metrics.dividend_years,
                # Scoring
                "Score": score,
                "Rating": rating,
                "Conclusion": conclusion,
            }

            # Append pass/fail per criterion with nice names
            pretty_map = {
                "eps_growth_positive": "EPS_Positive",
                "roe_min": "ROE_Pass",
                "roa_min": "ROA_Pass",
                "pe_max": "PE_Pass",
                "pb_max": "PB_Pass",
                "debt_assets_max_pct": "DebtAssets_Pass",
                "current_ratio_min": "CurrentRatio_Pass",
                "dividend_years_min": "Dividend_Pass",
                "gross_margin_min": "GrossMargin_Pass",
                "avg20d_volume_min": "Avg20dVol_Pass",
                "beta_max": "Beta_Pass",
            }
            for k, v in checks.items():
                row[pretty_map.get(k, k)] = "✅" if v else "❌"

            rows.append(row)
        except Exception as e:
            rows.append({
                "symbol": symbol,
                "error": str(e),
                "Score": 0.0,
                "Rating": "",
                "Conclusion": "Loại",
            })

        # Gentle pacing to avoid rate limits
        time.sleep(random.uniform(0.6, 1.2))

    df = pd.DataFrame(rows)
    df = df.sort_values(by=["Score", "symbol"], ascending=[False, True]).reset_index(drop=True)
    return df


__all__ = [
    "find_potential_stocks",
    "DEFAULT_CRITERIA",
]


