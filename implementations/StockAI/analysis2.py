#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analysis2.py
파동 분석 및 투자 등급 산출 엔진 (핵심 모듈)

주요 기능:
- 기술적 지표 계산 (이동평균, RSI, 거래량 등)
- 파동 단계 분류 (1단계~4단계)
- 펀더멘털 점수 산출
- 종합 투자 점수 및 등급 결정
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 상수 정의
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DAILY_PRICES_FILE = os.path.join(BASE_DIR, 'daily_prices.csv')
INSTITUTIONAL_FILE = os.path.join(BASE_DIR, 'all_institutional_trend_data.csv')
OUTPUT_FILE = os.path.join(BASE_DIR, 'wave_transition_analysis_results.csv')


class EnhancedWaveTransitionAnalyzerV3:
    """
    파동 전환 분석기 v3
    
    분석 방법론:
    1. 기술적 지표 계산 (MA, RSI, Volume 등)
    2. 파동 단계 분류 (90점 ~ 60점)
    3. 펀더멘털 점수 가산
    4. 수급 점수 가산
    5. 종합 등급 산출
    """
    
    def __init__(self, prices_df: pd.DataFrame, institutional_df: Optional[pd.DataFrame] = None):
        """
        Args:
            prices_df: 일별 시세 데이터
            institutional_df: 기관/외국인 수급 데이터
        """
        self.prices_df = prices_df.copy()
        self.institutional_df = institutional_df
        
        # 데이터 전처리
        self._preprocess_data()
    
    def _preprocess_data(self):
        """데이터 전처리"""
        # 날짜 변환
        if 'date' in self.prices_df.columns:
            self.prices_df['date'] = pd.to_datetime(self.prices_df['date'])
        
        # ticker 정규화
        if 'ticker' in self.prices_df.columns:
            self.prices_df['ticker'] = self.prices_df['ticker'].astype(str).str.zfill(6)
        
        # 정렬
        self.prices_df = self.prices_df.sort_values(['ticker', 'date'])
    
    def _calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        기술적 지표를 계산합니다.
        
        계산 지표:
        - 이동평균선 (MA5, MA20, MA50, MA200)
        - RSI (14일)
        - 거래량 이동평균
        - 52주 고가/저가 대비 위치
        - 가격 변화율
        """
        df = df.copy()
        
        # 이동평균선
        df['ma5'] = df['close'].rolling(window=5, min_periods=1).mean()
        df['ma20'] = df['close'].rolling(window=20, min_periods=1).mean()
        df['ma50'] = df['close'].rolling(window=50, min_periods=1).mean()
        df['ma200'] = df['close'].rolling(window=200, min_periods=1).mean()
        
        # RSI 계산
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
        rs = gain / loss.replace(0, np.nan)
        df['rsi'] = 100 - (100 / (1 + rs))
        df['rsi'] = df['rsi'].fillna(50)
        
        # 거래량 이동평균
        df['volume_ma20'] = df['volume'].rolling(window=20, min_periods=1).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma20'].replace(0, 1)
        
        # 52주 고저 대비 위치
        df['high_52w'] = df['high'].rolling(window=252, min_periods=20).max()
        df['low_52w'] = df['low'].rolling(window=252, min_periods=20).min()
        price_range = df['high_52w'] - df['low_52w']
        df['position_52w'] = ((df['close'] - df['low_52w']) / price_range.replace(0, 1)) * 100
        
        # 가격 변화율
        df['price_change_5d'] = df['close'].pct_change(5)
        df['price_change_20d'] = df['close'].pct_change(20)
        df['price_change_60d'] = df['close'].pct_change(60)
        
        # 골든크로스/데드크로스 감지
        df['golden_cross'] = (df['ma20'] > df['ma50']) & (df['ma20'].shift(1) <= df['ma50'].shift(1))
        df['death_cross'] = (df['ma20'] < df['ma50']) & (df['ma20'].shift(1) >= df['ma50'].shift(1))
        
        # 이동평균 정배열 여부
        df['ma_aligned'] = (df['ma20'] > df['ma50']) & (df['ma50'] > df['ma200'])
        
        return df
    
    def _classify_wave_stage(self, row: pd.Series) -> Tuple[int, str]:
        """
        파동 단계를 분류합니다.
        
        Returns:
            (score, stage_name) 튜플
        """
        # 필요한 지표 추출
        close = row.get('close', 0)
        ma20 = row.get('ma20', 0)
        ma50 = row.get('ma50', 0)
        ma200 = row.get('ma200', 0)
        rsi = row.get('rsi', 50)
        position_52w = row.get('position_52w', 50)
        volume_ratio = row.get('volume_ratio', 1)
        price_change_20d = row.get('price_change_20d', 0)
        ma_aligned = row.get('ma_aligned', False)
        
        # NaN 처리
        if pd.isna(ma50) or pd.isna(ma200) or ma50 == 0 or ma200 == 0:
            return 50, "Insufficient Data"
        
        # === 2단계 중기 (Strong Uptrend) - 90점 ===
        # 조건: 정배열, 52주 위치 60-90%, 거래량 1.3배 이상, RSI 55-75
        if (ma_aligned and 
            60 <= position_52w <= 90 and 
            volume_ratio >= 1.3 and 
            55 <= rsi <= 75 and
            price_change_20d >= 0.10):
            return 90, "Stage 2 Mid (Strong Uptrend)"
        
        # === 2단계 초기 (Early Uptrend) - 80점 ===
        # 조건: MA20 > MA50, 52주 위치 40-75%, 20일선 지지, 거래량 1.2배 이상
        if (ma20 > ma50 and 
            40 <= position_52w <= 75 and 
            close >= ma20 * 0.98 and  # 20일선 근처
            volume_ratio >= 1.2):
            return 80, "Stage 2 Early (Early Uptrend)"
        
        # === 1단계 → 2단계 전환 (Transition) - 70점 ===
        # 조건: MA20과 MA50 수렴, 52주 위치 25-60%, RSI 45-65
        ma_convergence = abs(ma20 - ma50) / ma50 < 0.03 if ma50 > 0 else False
        if (ma_convergence and 
            25 <= position_52w <= 60 and 
            45 <= rsi <= 65):
            return 70, "Stage 1-2 Transition"
        
        # === 일반 상승 추세 (General Uptrend) - 60점 ===
        # 조건: MA20 > MA50, 52주 위치 30-70%, 거래량 80% 이상 유지
        if (ma20 > ma50 and 
            30 <= position_52w <= 70 and 
            volume_ratio >= 0.8):
            return 60, "General Uptrend"
        
        # === 4단계 (Decline) - 30점 ===
        # 조건: MA20 < MA50 < MA200, RSI < 40
        if (ma20 < ma50 and 
            ma50 < ma200 and 
            rsi < 40):
            return 30, "Stage 4 (Decline)"
        
        # === 3단계 (Distribution) - 40점 ===
        # 조건: 고점 근처에서 횡보, 거래량 감소
        if (position_52w >= 75 and 
            volume_ratio < 0.8):
            return 40, "Stage 3 (Distribution)"
        
        # === 1단계 (Base) - 50점 ===
        # 조건: 바닥권 횡보
        if (position_52w < 40 and 
            abs(price_change_20d) < 0.05):
            return 50, "Stage 1 (Base)"
        
        # 기본값
        return 50, "Neutral"
    
    def _calculate_fundamental_score(self, row: pd.Series) -> float:
        """
        펀더멘털 점수를 계산합니다 (0-20점).
        
        Note: 현재는 기술적 지표만 사용하여 근사값 계산
        실제 구현 시 PER, PBR, ROE 등 데이터 필요
        """
        score = 10  # 기본 점수
        
        # 거래량 지표 기반 가산점
        volume_ratio = row.get('volume_ratio', 1)
        if volume_ratio >= 1.5:
            score += 5
        elif volume_ratio >= 1.2:
            score += 3
        
        # RSI 기반 가산점
        rsi = row.get('rsi', 50)
        if 50 <= rsi <= 70:
            score += 5
        elif 40 <= rsi < 50:
            score += 2
        
        return min(20, score)
    
    def analyze_stock(self, ticker: str) -> Dict:
        """
        개별 종목을 분석합니다.
        
        Returns:
            분석 결과 딕셔너리
        """
        # 해당 종목 데이터 추출
        stock_data = self.prices_df[self.prices_df['ticker'] == ticker].copy()
        
        if stock_data.empty or len(stock_data) < 20:
            return {
                'ticker': ticker,
                'wave_score': 0,
                'wave_stage': 'Insufficient Data',
                'final_investment_score': 0,
                'investment_grade': '분석 불가'
            }
        
        # 기술적 지표 계산
        stock_data = self._calculate_technical_indicators(stock_data)
        
        # 가장 최근 데이터
        latest = stock_data.iloc[-1]
        
        # 파동 단계 분류
        wave_score, wave_stage = self._classify_wave_stage(latest)
        
        # 펀더멘털 점수
        fundamental_score = self._calculate_fundamental_score(latest)
        
        # 수급 점수 (있는 경우)
        supply_demand_score = 0
        supply_demand_stage = 'N/A'
        
        if self.institutional_df is not None and not self.institutional_df.empty:
            inst_row = self.institutional_df[self.institutional_df['ticker'] == ticker]
            if not inst_row.empty:
                supply_demand_score = inst_row.iloc[0].get('supply_demand_score', 0)
                supply_demand_stage = inst_row.iloc[0].get('supply_demand_stage', 'N/A')
        
        # 종합 점수 계산
        # 가중치: 파동 60%, 펀더멘털 20%, 수급 20%
        final_score = (wave_score * 0.6) + (fundamental_score * 1.0) + (supply_demand_score * 0.2)
        
        # 투자 등급 결정
        if final_score >= 85:
            grade = 'S급 (즉시 매수)'
        elif final_score >= 75:
            grade = 'A급 (적극 매수)'
        elif final_score >= 65:
            grade = 'B급 (매수 고려)'
        elif final_score >= 55:
            grade = 'C급 (중립)'
        elif final_score >= 45:
            grade = 'D급 (매도 고려)'
        else:
            grade = 'F급 (회피)'
        
        # 결과 조합
        result = {
            'ticker': ticker,
            'name': latest.get('name', ''),
            'market': latest.get('market', ''),
            'current_date': latest['date'].strftime('%Y-%m-%d') if pd.notna(latest['date']) else '',
            'current_price': latest.get('close', 0),
            
            # 기술적 지표
            'ma20': round(latest.get('ma20', 0), 2),
            'ma50': round(latest.get('ma50', 0), 2),
            'ma200': round(latest.get('ma200', 0), 2),
            'rsi': round(latest.get('rsi', 0), 2),
            'volume_ratio': round(latest.get('volume_ratio', 0), 2),
            'position_52w': round(latest.get('position_52w', 0), 2),
            
            # 가격 변화율
            'price_change_5d': round(latest.get('price_change_5d', 0), 4),
            'price_change_20d': round(latest.get('price_change_20d', 0), 4),
            'price_change_60d': round(latest.get('price_change_60d', 0), 4),
            
            # 파동 분석
            'wave_score': wave_score,
            'wave_stage': wave_stage,
            
            # 수급 분석
            'supply_demand_score': supply_demand_score,
            'supply_demand_stage': supply_demand_stage,
            
            # 종합 점수
            'fundamental_score': fundamental_score,
            'final_investment_score': round(final_score, 2),
            'investment_grade': grade
        }
        
        return result
    
    def analyze_all_stocks(self) -> pd.DataFrame:
        """
        전체 종목을 분석합니다.
        
        Returns:
            분석 결과 DataFrame
        """
        from tqdm import tqdm
        
        tickers = self.prices_df['ticker'].unique()
        logger.info(f"Analyzing {len(tickers)} stocks...")
        
        results = []
        
        for ticker in tqdm(tickers, desc="Wave Analysis"):
            try:
                result = self.analyze_stock(ticker)
                results.append(result)
            except Exception as e:
                logger.warning(f"Failed to analyze {ticker}: {e}")
                results.append({
                    'ticker': ticker,
                    'wave_score': 0,
                    'wave_stage': 'Error',
                    'final_investment_score': 0,
                    'investment_grade': '분석 오류'
                })
        
        result_df = pd.DataFrame(results)
        
        # 점수 기준 정렬
        result_df = result_df.sort_values('final_investment_score', ascending=False)
        
        return result_df


def load_data() -> Tuple[pd.DataFrame, Optional[pd.DataFrame]]:
    """
    분석에 필요한 데이터를 로드합니다.
    """
    # 일별 시세 데이터
    if not os.path.exists(DAILY_PRICES_FILE):
        logger.error(f"Daily prices file not found: {DAILY_PRICES_FILE}")
        return pd.DataFrame(), None
    
    prices_df = pd.read_csv(DAILY_PRICES_FILE, dtype={'ticker': str})
    prices_df['ticker'] = prices_df['ticker'].str.zfill(6)
    logger.info(f"Loaded {len(prices_df)} price records")
    
    # 수급 데이터 (선택)
    institutional_df = None
    if os.path.exists(INSTITUTIONAL_FILE):
        institutional_df = pd.read_csv(INSTITUTIONAL_FILE, dtype={'ticker': str})
        institutional_df['ticker'] = institutional_df['ticker'].str.zfill(6)
        logger.info(f"Loaded {len(institutional_df)} institutional records")
    else:
        logger.warning("Institutional data not found, proceeding without it")
    
    return prices_df, institutional_df


def main():
    """메인 실행 함수"""
    logger.info("=" * 50)
    logger.info("Starting Wave Transition Analysis V3")
    logger.info("=" * 50)
    
    import time
    start_time = time.time()
    
    # 데이터 로드
    prices_df, institutional_df = load_data()
    
    if prices_df.empty:
        logger.error("No price data available!")
        return
    
    # 분석기 초기화 및 실행
    analyzer = EnhancedWaveTransitionAnalyzerV3(prices_df, institutional_df)
    results = analyzer.analyze_all_stocks()
    
    if not results.empty:
        # 결과 저장
        results.to_csv(OUTPUT_FILE, index=False)
        logger.info(f"Saved {len(results)} results to {OUTPUT_FILE}")
        
        # 요약 출력
        logger.info("\n" + "=" * 50)
        logger.info("Analysis Summary:")
        logger.info(f"  - Total stocks analyzed: {len(results)}")
        logger.info(f"  - Average score: {results['final_investment_score'].mean():.1f}")
        
        # 등급별 분포
        grade_dist = results['investment_grade'].value_counts()
        logger.info(f"\n  - Grade distribution:")
        for grade, count in grade_dist.items():
            logger.info(f"      {grade}: {count}")
        
        # 상위 종목
        top_10 = results.head(10)[['ticker', 'name', 'final_investment_score', 'investment_grade', 'wave_stage']]
        logger.info(f"\n  - Top 10 Stocks:")
        for _, row in top_10.iterrows():
            logger.info(f"      {row['ticker']} {row['name']}: {row['final_investment_score']:.1f} ({row['investment_grade']})")
        
        logger.info(f"\n  - Elapsed time: {time.time() - start_time:.1f} seconds")
        logger.info("=" * 50)
    else:
        logger.error("No analysis results!")


if __name__ == "__main__":
    main()
