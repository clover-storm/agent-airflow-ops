#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dividend Sustainability Analyzer
Payout Ratio, Growth Rate, Streak, Safety Score
"""

import logging
from datetime import datetime
from typing import Dict, Optional

import numpy as np
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class DividendAnalyzer:
    _info_cache: Dict[str, Dict] = {}

    def _get_stock_info(self, ticker: str) -> Optional[Dict]:
        if ticker in self._info_cache:
            return self._info_cache[ticker]
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            self._info_cache[ticker] = info
            return info
        except Exception:
            return None

    def calculate_payout_ratio(self, ticker: str) -> Optional[float]:
        info = self._get_stock_info(ticker)
        if not info:
            return None

        ttm_dividend = info.get("dividendRate", 0) or 0
        eps = info.get("trailingEps", 0) or 0

        if eps <= 0:
            return None

        return round(ttm_dividend / eps, 3)

    def calculate_dividend_growth_rate(self, ticker: str, years: int = 5) -> Optional[float]:
        try:
            stock = yf.Ticker(ticker)
            dividends = stock.dividends
            if dividends.empty or len(dividends) < 4:
                return None

            dividends.index = dividends.index.tz_localize(None)
            now = pd.Timestamp.now()
            start = now - pd.Timedelta(days=years * 365)

            recent = dividends[dividends.index >= start]
            if len(recent) < 4:
                return None

            first_year = recent.iloc[:4].sum()
            last_year = recent.iloc[-4:].sum()

            if first_year <= 0:
                return None

            cagr = (last_year / first_year) ** (1 / years) - 1
            return round(float(cagr), 4)
        except Exception:
            return None

    def get_dividend_streak(self, ticker: str) -> int:
        try:
            stock = yf.Ticker(ticker)
            dividends = stock.dividends
            if dividends.empty:
                return 0

            dividends.index = dividends.index.tz_localize(None)
            years = sorted(set(dividends.index.year), reverse=True)

            streak = 0
            current_year = datetime.now().year
            for year in years:
                if year <= current_year and len(dividends[dividends.index.year == year]) > 0:
                    streak += 1
                    current_year = year - 1
                else:
                    break

            return streak
        except Exception:
            return 0

    def get_dividend_safety_score(self, ticker: str) -> Dict:
        payout = self.calculate_payout_ratio(ticker)
        growth = self.calculate_dividend_growth_rate(ticker)
        streak = self.get_dividend_streak(ticker)

        score = 0
        breakdown = {}

        if payout is not None:
            if payout < 0.3:
                pr_score = 30
            elif payout < 0.5:
                pr_score = 25
            elif payout < 0.7:
                pr_score = 15
            else:
                pr_score = 5
            score += pr_score
            breakdown["payout_ratio"] = {"value": payout, "score": pr_score, "max": 30}

        if growth is not None:
            if growth > 0.10:
                gr_score = 25
            elif growth > 0.05:
                gr_score = 20
            elif growth > 0:
                gr_score = 15
            else:
                gr_score = 5
            score += gr_score
            breakdown["dividend_growth"] = {"value": growth, "score": gr_score, "max": 25}

        if streak >= 25:
            st_score = 25
        elif streak >= 10:
            st_score = 20
        elif streak >= 5:
            st_score = 15
        else:
            st_score = streak * 2
        score += st_score
        breakdown["dividend_streak"] = {"value": streak, "score": st_score, "max": 25}

        if score >= 80:
            grade = "A"
        elif score >= 60:
            grade = "B"
        elif score >= 40:
            grade = "C"
        else:
            grade = "D"

        return {
            "ticker": ticker,
            "safety_score": score,
            "safety_grade": grade,
            "breakdown": breakdown,
        }

    def get_all_metrics(self, ticker: str) -> Dict:
        return {
            "payout_ratio": self.calculate_payout_ratio(ticker),
            "dividend_growth_5y": self.calculate_dividend_growth_rate(ticker),
            "dividend_streak": self.get_dividend_streak(ticker),
            "safety": self.get_dividend_safety_score(ticker),
        }
