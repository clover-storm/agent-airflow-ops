#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dividend Data Loader
Fetches dividend data from yfinance and saves to JSON.
- yield: stored as decimal (e.g., 0.055 for 5.5%)
- payments: array of {date, amount} for accurate monthly cashflow
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List

import pandas as pd
import yfinance as yf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
SEED_FILE = os.path.join(DATA_DIR, "universe_seed.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "dividend_universe.json")


class DividendDataLoader:
    def __init__(self, data_dir: str = DATA_DIR):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.tickers = self._load_universe()

    def _load_universe(self) -> List[str]:
        if os.path.exists(SEED_FILE):
            try:
                with open(SEED_FILE, "r", encoding="utf-8") as f:
                    seed_data = json.load(f)
                if isinstance(seed_data, list):
                    tickers = [item.get("symbol") for item in seed_data if item.get("symbol")]
                else:
                    tickers = list(seed_data.keys())
                logger.info("Loaded %d tickers from universe_seed.json", len(tickers))
                return tickers
            except Exception as exc:
                logger.error("Failed to load universe_seed.json: %s", exc)
        logger.warning("universe_seed.json not found. Using fallback list.")
        return ["SCHD", "JEPI", "JEPQ", "DGRO", "O", "KO", "PEP", "JNJ"]

    def fetch_data(self) -> Dict:
        logger.info("Fetching dividend data...")
        data_map: Dict[str, Dict] = {}

        for ticker in self.tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info

                price = info.get("currentPrice") or info.get("regularMarketPreviousClose") or 0
                if price is None:
                    price = 0

                hist = stock.dividends
                if hist.empty:
                    logger.warning("%s: No dividend history", ticker)
                    continue

                hist.index = hist.index.tz_localize(None)
                one_year_ago = pd.Timestamp.now() - pd.Timedelta(days=370)
                recent_divs = hist[hist.index > one_year_ago]

                ttm_div = float(recent_divs.sum()) if not recent_divs.empty else 0.0
                div_yield = (ttm_div / price) if price > 0 else 0.0

                frequency = len(recent_divs)
                if frequency >= 10:
                    freq_str = "Monthly"
                elif frequency >= 3:
                    freq_str = "Quarterly"
                elif frequency >= 1:
                    freq_str = "Semi-Annual/Annual"
                else:
                    freq_str = "Unknown"

                payments = [
                    {"date": dt.strftime("%Y-%m-%d"), "amount": float(amt)}
                    for dt, amt in recent_divs.items()
                ]

                last_amount = float(recent_divs.iloc[-1]) if not recent_divs.empty else 0

                data_map[ticker] = {
                    "name": info.get("shortName", ticker),
                    "sector": info.get("sector", "ETF"),
                    "price": float(price),
                    "yield": div_yield,
                    "ttm_dividend": ttm_div,
                    "frequency": freq_str,
                    "last_div": last_amount,
                    "payments": payments,
                    "currency": info.get("currency", "USD"),
                }

                logger.info("%s: %.2f%% (%s, %d payments)", ticker, div_yield * 100, freq_str, len(payments))

            except Exception as exc:
                logger.error("Error fetching %s: %s", ticker, exc)

        data_map["_meta"] = {
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_tickers": len(data_map),
        }

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(data_map, f, ensure_ascii=False, indent=2)

        logger.info("Saved %d tickers to %s", len(data_map) - 1, OUTPUT_FILE)
        return data_map


if __name__ == "__main__":
    loader = DividendDataLoader()
    loader.fetch_data()
