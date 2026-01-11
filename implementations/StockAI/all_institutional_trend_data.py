#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
all_institutional_trend_data.py
기관 및 외국인 투자자의 수급 데이터를 분석합니다.

주요 기능:
- 네이버 금융에서 기관/외국인 순매수 데이터 수집
- 수급 추세 분석 (누적 순매수, 연속 매수일 등)
- 수급 점수 산출
"""

import os
import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from tqdm import tqdm
from typing import Optional, Dict, List, Tuple
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 상수 정의
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STOCKS_LIST_FILE = os.path.join(BASE_DIR, 'korean_stocks_list.csv')
OUTPUT_FILE = os.path.join(BASE_DIR, 'all_institutional_trend_data.csv')

# 네이버 금융 투자자별 매매동향 URL
NAVER_INVESTOR_URL = "https://finance.naver.com/item/frgn.naver"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://finance.naver.com/'
}


def get_investor_trading_data(ticker: str, pages: int = 5) -> pd.DataFrame:
    """
    네이버 금융에서 투자자별 매매동향을 가져옵니다.
    
    Args:
        ticker: 종목 코드 (6자리)
        pages: 가져올 페이지 수
    
    Returns:
        DataFrame with investor trading data
    """
    all_data = []
    
    for page in range(1, pages + 1):
        try:
            url = f"{NAVER_INVESTOR_URL}?code={ticker}&page={page}"
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.encoding = 'euc-kr'
            
            tables = pd.read_html(response.text, encoding='euc-kr')
            
            # 투자자별 매매동향 테이블 찾기 (보통 2번째 테이블)
            for table in tables:
                if '기관' in str(table.columns) or '외국인' in str(table.columns):
                    df = table.dropna(how='all')
                    if not df.empty:
                        all_data.append(df)
                    break
                # 컬럼이 다른 형태일 수 있음
                if '날짜' in str(table.values):
                    df = table.dropna(subset=[table.columns[0]])
                    if not df.empty:
                        all_data.append(df)
                    break
            
            time.sleep(0.1)
            
        except Exception as e:
            logger.warning(f"Error fetching investor data for {ticker} page {page}: {e}")
            break
    
    if not all_data:
        return pd.DataFrame()
    
    result = pd.concat(all_data, ignore_index=True)
    return result


def parse_investor_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    투자자 데이터를 파싱하여 정리합니다.
    """
    if df.empty:
        return pd.DataFrame()
    
    # 컬럼명 정규화
    col_map = {}
    for col in df.columns:
        col_str = str(col).strip()
        if '날짜' in col_str:
            col_map[col] = 'date'
        elif '기관' in col_str:
            col_map[col] = 'institutional'
        elif '외국인' in col_str:
            col_map[col] = 'foreign'
        elif '개인' in col_str:
            col_map[col] = 'individual'
        elif '종가' in col_str:
            col_map[col] = 'close'
    
    if not col_map:
        return pd.DataFrame()
    
    df = df.rename(columns=col_map)
    
    # 필요한 컬럼만 선택
    available_cols = [col for col in ['date', 'institutional', 'foreign', 'individual', 'close'] 
                      if col in df.columns]
    
    if 'date' not in available_cols:
        return pd.DataFrame()
    
    result = df[available_cols].copy()
    
    # 날짜 변환
    result['date'] = pd.to_datetime(result['date'], format='%Y.%m.%d', errors='coerce')
    result = result.dropna(subset=['date'])
    
    # 숫자 변환
    for col in ['institutional', 'foreign', 'individual', 'close']:
        if col in result.columns:
            result[col] = pd.to_numeric(
                result[col].astype(str).str.replace(',', '').str.replace('+', ''),
                errors='coerce'
            )
    
    return result


def calculate_trend_metrics(df: pd.DataFrame) -> Dict:
    """
    수급 추세 지표를 계산합니다.
    
    Returns:
        Dict containing trend metrics
    """
    if df.empty or len(df) < 5:
        return {}
    
    df = df.sort_values('date', ascending=True).reset_index(drop=True)
    
    metrics = {}
    
    # 기관 지표
    if 'institutional' in df.columns:
        inst = df['institutional'].fillna(0)
        
        # 최근 N일 누적 순매수
        metrics['inst_5d_sum'] = inst.tail(5).sum()
        metrics['inst_10d_sum'] = inst.tail(10).sum()
        metrics['inst_20d_sum'] = inst.tail(20).sum()
        
        # 연속 매수일
        recent = inst.tail(10).values
        consecutive = 0
        for val in reversed(recent):
            if val > 0:
                consecutive += 1
            else:
                break
        metrics['inst_consecutive_buy'] = consecutive
        
        # 매수 비율 (최근 20일 중 순매수 일수)
        recent_20 = inst.tail(20)
        metrics['inst_buy_ratio'] = (recent_20 > 0).sum() / len(recent_20) if len(recent_20) > 0 else 0
        
        # 추세 (기울기)
        if len(inst) >= 5:
            x = np.arange(len(inst.tail(20)))
            y = inst.tail(20).values
            if len(x) == len(y) and len(x) > 1:
                slope = np.polyfit(x, y, 1)[0]
                metrics['inst_trend_slope'] = slope
    
    # 외국인 지표
    if 'foreign' in df.columns:
        frgn = df['foreign'].fillna(0)
        
        metrics['frgn_5d_sum'] = frgn.tail(5).sum()
        metrics['frgn_10d_sum'] = frgn.tail(10).sum()
        metrics['frgn_20d_sum'] = frgn.tail(20).sum()
        
        # 연속 매수일
        recent = frgn.tail(10).values
        consecutive = 0
        for val in reversed(recent):
            if val > 0:
                consecutive += 1
            else:
                break
        metrics['frgn_consecutive_buy'] = consecutive
        
        # 매수 비율
        recent_20 = frgn.tail(20)
        metrics['frgn_buy_ratio'] = (recent_20 > 0).sum() / len(recent_20) if len(recent_20) > 0 else 0
        
        # 추세
        if len(frgn) >= 5:
            x = np.arange(len(frgn.tail(20)))
            y = frgn.tail(20).values
            if len(x) == len(y) and len(x) > 1:
                slope = np.polyfit(x, y, 1)[0]
                metrics['frgn_trend_slope'] = slope
    
    return metrics


def calculate_supply_demand_score(metrics: Dict) -> Tuple[float, str]:
    """
    수급 종합 점수를 계산합니다.
    
    Returns:
        (score, stage) 튜플
    """
    if not metrics:
        return 0, "Unknown"
    
    score = 50  # 기본 점수
    
    # 기관 점수 (+/- 25점)
    if metrics.get('inst_20d_sum', 0) > 0:
        score += 10
    if metrics.get('inst_consecutive_buy', 0) >= 3:
        score += 10
    if metrics.get('inst_buy_ratio', 0) >= 0.6:
        score += 5
    if metrics.get('inst_trend_slope', 0) > 0:
        score += 5
    
    # 외국인 점수 (+/- 25점)
    if metrics.get('frgn_20d_sum', 0) > 0:
        score += 10
    if metrics.get('frgn_consecutive_buy', 0) >= 3:
        score += 10
    if metrics.get('frgn_buy_ratio', 0) >= 0.6:
        score += 5
    if metrics.get('frgn_trend_slope', 0) > 0:
        score += 5
    
    # 감점 요소
    if metrics.get('inst_20d_sum', 0) < 0:
        score -= 10
    if metrics.get('frgn_20d_sum', 0) < 0:
        score -= 10
    
    # 점수 범위 제한
    score = max(0, min(100, score))
    
    # 단계 결정
    if score >= 80:
        stage = "Strong Accumulation"
    elif score >= 65:
        stage = "Accumulation"
    elif score >= 50:
        stage = "Neutral"
    elif score >= 35:
        stage = "Distribution"
    else:
        stage = "Strong Distribution"
    
    return score, stage


def analyze_institutional_trend(ticker: str, name: str, market: str) -> Dict:
    """
    특정 종목의 기관/외국인 수급 추세를 분석합니다.
    """
    # 데이터 수집
    raw_data = get_investor_trading_data(ticker, pages=5)
    
    if raw_data.empty:
        return {
            'ticker': ticker,
            'name': name,
            'market': market,
            'supply_demand_score': 0,
            'supply_demand_stage': 'Unknown'
        }
    
    # 데이터 파싱
    parsed_data = parse_investor_data(raw_data)
    
    if parsed_data.empty:
        return {
            'ticker': ticker,
            'name': name,
            'market': market,
            'supply_demand_score': 0,
            'supply_demand_stage': 'Unknown'
        }
    
    # 지표 계산
    metrics = calculate_trend_metrics(parsed_data)
    
    # 점수 산출
    score, stage = calculate_supply_demand_score(metrics)
    
    # 결과 조합
    result = {
        'ticker': ticker,
        'name': name,
        'market': market,
        'supply_demand_score': score,
        'supply_demand_stage': stage,
        **metrics
    }
    
    return result


def collect_all_institutional_data() -> pd.DataFrame:
    """
    모든 종목의 기관/외국인 수급 데이터를 수집합니다.
    """
    if not os.path.exists(STOCKS_LIST_FILE):
        logger.error(f"Stock list file not found: {STOCKS_LIST_FILE}")
        return pd.DataFrame()
    
    stocks_df = pd.read_csv(STOCKS_LIST_FILE, dtype={'ticker': str})
    stocks_df['ticker'] = stocks_df['ticker'].str.zfill(6)
    
    logger.info(f"Analyzing institutional trends for {len(stocks_df)} stocks...")
    
    results = []
    
    for _, row in tqdm(stocks_df.iterrows(), total=len(stocks_df), desc="Analyzing supply/demand"):
        ticker = row['ticker']
        name = row['name']
        market = row.get('market', 'KOSPI')
        
        try:
            result = analyze_institutional_trend(ticker, name, market)
            results.append(result)
        except Exception as e:
            logger.warning(f"Failed to analyze {ticker}: {e}")
            results.append({
                'ticker': ticker,
                'name': name,
                'market': market,
                'supply_demand_score': 0,
                'supply_demand_stage': 'Error'
            })
        
        time.sleep(0.2)  # Rate limiting
    
    result_df = pd.DataFrame(results)
    return result_df


def main():
    """메인 실행 함수"""
    logger.info("=" * 50)
    logger.info("Starting Institutional Trend Analysis")
    logger.info("=" * 50)
    
    start_time = time.time()
    
    result = collect_all_institutional_data()
    
    if not result.empty:
        result.to_csv(OUTPUT_FILE, index=False)
        logger.info(f"Saved {len(result)} rows to {OUTPUT_FILE}")
        
        # 요약 출력
        logger.info("\n" + "=" * 50)
        logger.info("Analysis Summary:")
        logger.info(f"  - Total stocks analyzed: {len(result)}")
        logger.info(f"  - Average S/D score: {result['supply_demand_score'].mean():.1f}")
        
        # 단계별 분포
        stage_dist = result['supply_demand_stage'].value_counts()
        logger.info(f"  - Stage distribution:")
        for stage, count in stage_dist.items():
            logger.info(f"      {stage}: {count}")
        
        # 상위 종목
        top_5 = result.nlargest(5, 'supply_demand_score')[['ticker', 'name', 'supply_demand_score', 'supply_demand_stage']]
        logger.info(f"\n  - Top 5 by S/D Score:")
        for _, row in top_5.iterrows():
            logger.info(f"      {row['ticker']} {row['name']}: {row['supply_demand_score']:.0f} ({row['supply_demand_stage']})")
        
        logger.info(f"\n  - Elapsed time: {time.time() - start_time:.1f} seconds")
        logger.info("=" * 50)
    else:
        logger.error("No data to save!")


if __name__ == "__main__":
    main()
