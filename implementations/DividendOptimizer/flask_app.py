#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask app for Dividend Optimizer
"""

from datetime import datetime, timedelta
from flask import Flask, jsonify, render_template, request
import yfinance as yf

app = Flask(__name__, template_folder="templates", static_folder="static")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/app")
def dashboard():
    return render_template("dashboard.html")


@app.route("/dividend")
def dividend_page():
    return render_template("dividend.html")


@app.route("/api/dividend/themes")
def get_dividend_themes():
    try:
        from engine import DividendEngine

        engine = DividendEngine()
        return jsonify(engine.get_themes())
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/dividend/all-tiers", methods=["POST"])
def get_all_tier_portfolios():
    try:
        data = request.json or {}
        theme_id = data.get("theme_id", "max_monthly_income")
        target_monthly_krw = float(data.get("target_monthly_krw", 1_000_000))
        fx_rate = float(data.get("fx_rate", 1420))
        tax_rate = float(data.get("tax_rate", 15.4)) / 100.0
        optimize_mode = data.get("optimize_mode", "greedy")

        from engine import DividendEngine

        engine = DividendEngine()

        results = {}
        for tier in ["defensive", "balanced", "aggressive"]:
            result = engine.generate_portfolio(
                theme_id=theme_id,
                tier_id=tier,
                target_monthly_krw=target_monthly_krw,
                fx_rate=fx_rate,
                tax_rate=tax_rate,
                optimize_mode=optimize_mode,
            )
            results[tier] = result
        return jsonify(results)

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/dividend/risk-metrics/<ticker>")
def get_dividend_risk_metrics(ticker):
    try:
        from risk_analytics import RiskAnalytics
        import numpy as np

        period = request.args.get("period", "1y")
        ra = RiskAnalytics()
        metrics = ra.get_all_risk_metrics(ticker, period)

        vol = metrics.get("volatility_annual")
        drawdown = metrics.get("max_drawdown")
        if vol is not None and drawdown is not None:
            if vol < 0.15 and abs(drawdown) < 0.20:
                metrics["risk_grade"] = "A"
            elif vol < 0.25 and abs(drawdown) < 0.35:
                metrics["risk_grade"] = "B"
            else:
                metrics["risk_grade"] = "C"
        else:
            metrics["risk_grade"] = "N/A"

        # Calculate beta vs SPY
        try:
            stock = yf.Ticker(ticker)
            spy = yf.Ticker("SPY")
            stock_hist = stock.history(period=period)["Close"]
            spy_hist = spy.history(period=period)["Close"]

            if len(stock_hist) > 20 and len(spy_hist) > 20:
                stock_ret = np.log(stock_hist / stock_hist.shift(1)).dropna()
                spy_ret = np.log(spy_hist / spy_hist.shift(1)).dropna()

                # Align indices
                common = stock_ret.index.intersection(spy_ret.index)
                if len(common) > 20:
                    stock_ret = stock_ret.loc[common]
                    spy_ret = spy_ret.loc[common]

                    cov = np.cov(stock_ret, spy_ret)[0, 1]
                    var = np.var(spy_ret)
                    if var > 0:
                        metrics["beta"] = round(cov / var, 2)
        except Exception:
            metrics["beta"] = None

        return jsonify(metrics)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/dividend/sustainability/<ticker>")
def get_dividend_sustainability(ticker):
    try:
        from dividend_analyzer import DividendAnalyzer

        da = DividendAnalyzer()
        metrics = da.get_all_metrics(ticker)

        # Get current yield from yfinance
        current_yield = None
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            current_yield = info.get("dividendYield", None)
        except Exception:
            pass

        # Format response for frontend
        safety = metrics.get("safety", {})
        return jsonify({
            "ticker": ticker,
            "sustainability_score": safety.get("safety_score", 0),
            "sustainability_grade": safety.get("safety_grade", "N/A"),
            "consecutive_years": metrics.get("dividend_streak", 0),
            "div_growth_5y": metrics.get("dividend_growth_5y"),
            "payout_ratio": metrics.get("payout_ratio"),
            "current_yield": current_yield,
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/dividend/optimize-advanced", methods=["POST"])
def optimize_dividend_advanced():
    try:
        data = request.json or {}
        theme_id = data.get("theme_id", "max_monthly_income")
        tier_id = data.get("tier_id", "balanced")
        target_monthly_krw = float(data.get("target_monthly_krw", 1_000_000))
        fx_rate = float(data.get("fx_rate", 1420))
        tax_rate = float(data.get("tax_rate", 15.4)) / 100.0
        optimize_mode = data.get("optimize_mode", "risk_parity")

        from engine import DividendEngine

        engine = DividendEngine()

        result = engine.generate_portfolio(
            theme_id=theme_id,
            tier_id=tier_id,
            target_monthly_krw=target_monthly_krw,
            fx_rate=fx_rate,
            tax_rate=tax_rate,
            optimize_mode=optimize_mode,
        )
        return jsonify(result)

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/dividend/backtest", methods=["POST"])
def run_dividend_backtest():
    try:
        from backtest import BacktestEngine

        data = request.json or {}
        portfolio = data.get("portfolio", [])
        start_date = data.get("start_date", "2022-01-01")
        end_date = data.get("end_date")
        initial_capital = float(data.get("initial_capital", 100000))

        if not portfolio:
            return jsonify({"error": "Portfolio is required"}), 400

        portfolio_tuples = [(p["ticker"], p["weight"]) for p in portfolio]

        engine = BacktestEngine()
        result = engine.run_backtest(
            portfolio=portfolio_tuples,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
        )

        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/dividend/realtime-prices", methods=["POST"])
def get_realtime_prices():
    """Fetch real-time prices for multiple tickers"""
    try:
        data = request.json or {}
        tickers = data.get("tickers", [])

        if not tickers:
            return jsonify({"error": "No tickers provided"}), 400

        result = {}
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.fast_info
                price = getattr(info, "last_price", None)
                prev_close = getattr(info, "previous_close", None)

                if price is not None:
                    change = 0
                    change_pct = 0
                    if prev_close and prev_close > 0:
                        change = price - prev_close
                        change_pct = (change / prev_close) * 100

                    result[ticker] = {
                        "price": round(price, 2),
                        "change": round(change, 2),
                        "change_pct": round(change_pct, 2),
                    }
            except Exception:
                continue

        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/dividend/stock-history/<ticker>")
def get_stock_history(ticker):
    """Fetch OHLC price history for charts"""
    try:
        period = request.args.get("period", "1y")

        # Map period to yfinance format
        period_map = {
            "1m": "1mo",
            "3m": "3mo",
            "6m": "6mo",
            "1y": "1y",
            "2y": "2y",
            "5y": "5y",
        }
        yf_period = period_map.get(period, "1y")

        stock = yf.Ticker(ticker)
        hist = stock.history(period=yf_period)

        if hist.empty:
            return jsonify({"error": "No data available", "prices": []})

        # Format for Lightweight Charts
        prices = []
        for date, row in hist.iterrows():
            prices.append({
                "time": date.strftime("%Y-%m-%d"),
                "open": round(row["Open"], 2),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
                "close": round(row["Close"], 2),
            })

        return jsonify({
            "ticker": ticker,
            "period": period,
            "prices": prices,
        })
    except Exception as exc:
        return jsonify({"error": str(exc), "prices": []}), 500


if __name__ == "__main__":
    app.run(port=5001, debug=True, use_reloader=False)
