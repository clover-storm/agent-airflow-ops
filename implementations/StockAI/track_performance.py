#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
track_performance.py
추천 종목의 성과를 추적하는 시스템

사용법:
    python track_performance.py --save     # 오늘 추천 저장
    python track_performance.py --report   # 성과 리포트 생성
    python track_performance.py --days 5   # 5일 후 성과 계산
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_FILE = os.path.join(BASE_DIR, 'wave_transition_analysis_results.csv')
HISTORY_DIR = os.path.join(BASE_DIR, 'history')
PERFORMANCE_FILE = os.path.join(BASE_DIR, 'performance_report.csv')


class PerformanceTracker:
    """추천 종목 성과 추적기"""

    def __init__(self):
        os.makedirs(HISTORY_DIR, exist_ok=True)

    def save_recommendations(self, grades: List[str] = None) -> str:
        """
        오늘의 추천 종목을 히스토리에 저장합니다.

        Args:
            grades: 저장할 등급 목록 (기본: S급, A급)

        Returns:
            저장된 파일 경로
        """
        if grades is None:
            grades = ['S급 (즉시 매수)', 'A급 (적극 매수)']

        if not os.path.exists(RESULTS_FILE):
            logger.error(f"Results file not found: {RESULTS_FILE}")
            return ""

        df = pd.read_csv(RESULTS_FILE, dtype={'ticker': str})
        df['ticker'] = df['ticker'].str.zfill(6)

        # 등급 필터링
        filtered = df[df['investment_grade'].isin(grades)]

        if filtered.empty:
            logger.warning("No stocks found with specified grades")
            return ""

        # 저장할 데이터 구성
        today = datetime.now().strftime('%Y-%m-%d')
        picks = []

        for _, row in filtered.iterrows():
            picks.append({
                'ticker': row['ticker'],
                'name': row.get('name', ''),
                'price': row.get('current_price', 0),
                'score': row.get('final_investment_score', 0),
                'grade': row.get('investment_grade', ''),
                'wave_stage': row.get('wave_stage', ''),
                'rsi': row.get('rsi', 50),
                'recommendation_date': today
            })

        # JSON 파일로 저장
        history_file = os.path.join(HISTORY_DIR, f'picks_{today}.json')
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(picks, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(picks)} picks to {history_file}")
        return history_file

    def get_current_price(self, ticker: str) -> Optional[float]:
        """
        현재 가격을 가져옵니다 (daily_prices.csv에서).
        """
        prices_file = os.path.join(BASE_DIR, 'daily_prices.csv')
        if not os.path.exists(prices_file):
            return None

        df = pd.read_csv(prices_file, dtype={'ticker': str})
        df['ticker'] = df['ticker'].str.zfill(6)

        stock = df[df['ticker'] == ticker]
        if stock.empty:
            return None

        # 가장 최근 가격
        stock = stock.sort_values('date', ascending=False)
        return stock.iloc[0]['close']

    def calculate_performance(self, days: int = 5) -> pd.DataFrame:
        """
        N일 전 추천 종목의 성과를 계산합니다.

        Args:
            days: 며칠 전 추천 기준

        Returns:
            성과 데이터프레임
        """
        target_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        history_file = os.path.join(HISTORY_DIR, f'picks_{target_date}.json')

        if not os.path.exists(history_file):
            logger.warning(f"No history found for {target_date}")
            return pd.DataFrame()

        with open(history_file, 'r', encoding='utf-8') as f:
            picks = json.load(f)

        results = []
        for pick in picks:
            ticker = pick['ticker']
            rec_price = pick['price']

            current_price = self.get_current_price(ticker)

            if current_price and rec_price > 0:
                return_pct = ((current_price / rec_price) - 1) * 100
            else:
                current_price = None
                return_pct = None

            results.append({
                'recommendation_date': pick['recommendation_date'],
                'ticker': ticker,
                'name': pick['name'],
                'grade': pick['grade'],
                'rec_price': rec_price,
                'current_price': current_price,
                'return_pct': return_pct,
                'days_held': days
            })

        return pd.DataFrame(results)

    def generate_report(self) -> Dict:
        """
        전체 성과 리포트를 생성합니다.

        Returns:
            성과 통계 딕셔너리
        """
        all_results = []

        # 모든 히스토리 파일 처리
        for filename in os.listdir(HISTORY_DIR):
            if not filename.startswith('picks_') or not filename.endswith('.json'):
                continue

            date_str = filename.replace('picks_', '').replace('.json', '')

            try:
                rec_date = datetime.strptime(date_str, '%Y-%m-%d')
                days_ago = (datetime.now() - rec_date).days

                if days_ago < 1:
                    continue  # 오늘 추천은 제외

                history_file = os.path.join(HISTORY_DIR, filename)
                with open(history_file, 'r', encoding='utf-8') as f:
                    picks = json.load(f)

                for pick in picks:
                    ticker = pick['ticker']
                    rec_price = pick['price']
                    current_price = self.get_current_price(ticker)

                    if current_price and rec_price > 0:
                        return_pct = ((current_price / rec_price) - 1) * 100
                    else:
                        return_pct = None

                    all_results.append({
                        'recommendation_date': date_str,
                        'ticker': ticker,
                        'name': pick['name'],
                        'grade': pick['grade'],
                        'rec_price': rec_price,
                        'current_price': current_price,
                        'return_pct': return_pct,
                        'days_held': days_ago
                    })

            except Exception as e:
                logger.warning(f"Error processing {filename}: {e}")
                continue

        if not all_results:
            logger.warning("No historical data to analyze")
            return {}

        df = pd.DataFrame(all_results)

        # 유효한 수익률만 필터링
        valid_df = df[df['return_pct'].notna()]

        if valid_df.empty:
            return {}

        # 통계 계산
        report = {
            'total_picks': len(df),
            'valid_picks': len(valid_df),
            'avg_return': valid_df['return_pct'].mean(),
            'median_return': valid_df['return_pct'].median(),
            'std_return': valid_df['return_pct'].std(),
            'win_rate': (valid_df['return_pct'] > 0).sum() / len(valid_df) * 100,
            'best_pick': valid_df.loc[valid_df['return_pct'].idxmax()].to_dict() if len(valid_df) > 0 else None,
            'worst_pick': valid_df.loc[valid_df['return_pct'].idxmin()].to_dict() if len(valid_df) > 0 else None,
            'avg_days_held': valid_df['days_held'].mean(),
            'by_grade': {}
        }

        # 등급별 통계
        for grade in valid_df['grade'].unique():
            grade_df = valid_df[valid_df['grade'] == grade]
            report['by_grade'][grade] = {
                'count': len(grade_df),
                'avg_return': grade_df['return_pct'].mean(),
                'win_rate': (grade_df['return_pct'] > 0).sum() / len(grade_df) * 100 if len(grade_df) > 0 else 0
            }

        # CSV 저장
        df.to_csv(PERFORMANCE_FILE, index=False)
        logger.info(f"Saved performance report to {PERFORMANCE_FILE}")

        return report

    def get_history_dates(self) -> List[str]:
        """사용 가능한 히스토리 날짜 목록을 반환합니다."""
        dates = []
        for filename in os.listdir(HISTORY_DIR):
            if filename.startswith('picks_') and filename.endswith('.json'):
                date_str = filename.replace('picks_', '').replace('.json', '')
                dates.append(date_str)
        return sorted(dates, reverse=True)

    def get_picks_by_date(self, date: str) -> List[Dict]:
        """특정 날짜의 추천 종목을 반환합니다."""
        history_file = os.path.join(HISTORY_DIR, f'picks_{date}.json')
        if not os.path.exists(history_file):
            return []

        with open(history_file, 'r', encoding='utf-8') as f:
            return json.load(f)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Performance Tracker')
    parser.add_argument('--save', action='store_true', help='Save today\'s recommendations')
    parser.add_argument('--report', action='store_true', help='Generate performance report')
    parser.add_argument('--days', type=int, default=5, help='Days for performance calculation')
    parser.add_argument('--list', action='store_true', help='List available history dates')
    args = parser.parse_args()

    tracker = PerformanceTracker()

    if args.save:
        tracker.save_recommendations()

    elif args.report:
        report = tracker.generate_report()
        if report:
            print("\n" + "=" * 60)
            print("PERFORMANCE REPORT")
            print("=" * 60)
            print(f"Total Picks: {report['total_picks']}")
            print(f"Valid Picks: {report['valid_picks']}")
            print(f"Average Return: {report['avg_return']:.2f}%")
            print(f"Median Return: {report['median_return']:.2f}%")
            print(f"Win Rate: {report['win_rate']:.1f}%")
            print(f"Avg Days Held: {report['avg_days_held']:.1f}")

            if report['best_pick']:
                bp = report['best_pick']
                print(f"\nBest Pick: {bp['ticker']} {bp['name']} (+{bp['return_pct']:.1f}%)")

            if report['worst_pick']:
                wp = report['worst_pick']
                print(f"Worst Pick: {wp['ticker']} {wp['name']} ({wp['return_pct']:.1f}%)")

            print("\nBy Grade:")
            for grade, stats in report['by_grade'].items():
                print(f"  {grade}: {stats['count']} picks, avg {stats['avg_return']:.2f}%, win {stats['win_rate']:.1f}%")
        else:
            print("No historical data available for report")

    elif args.list:
        dates = tracker.get_history_dates()
        print("Available history dates:")
        for d in dates[:20]:
            print(f"  {d}")

    else:
        # 기본: N일 전 성과 계산
        perf = tracker.calculate_performance(days=args.days)
        if not perf.empty:
            print(f"\n{args.days}-day Performance:")
            print(perf[['ticker', 'name', 'grade', 'rec_price', 'current_price', 'return_pct']].to_string())

            valid = perf[perf['return_pct'].notna()]
            if len(valid) > 0:
                print(f"\nAverage Return: {valid['return_pct'].mean():.2f}%")
                print(f"Win Rate: {(valid['return_pct'] > 0).sum() / len(valid) * 100:.1f}%")
        else:
            print(f"No recommendations found from {args.days} days ago")


if __name__ == "__main__":
    main()
