#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dashboard/utils.py
대시보드 유틸리티 함수

주요 기능:
- 데이터 로딩 및 캐싱
- 차트 생성 헬퍼
- 포맷팅 함수
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# 상수
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANALYSIS_FILE = os.path.join(BASE_DIR, 'wave_transition_analysis_results.csv')
PRICES_FILE = os.path.join(BASE_DIR, 'daily_prices.csv')
INSTITUTIONAL_FILE = os.path.join(BASE_DIR, 'all_institutional_trend_data.csv')


def load_analysis_results() -> pd.DataFrame:
    """분석 결과를 로드합니다."""
    if not os.path.exists(ANALYSIS_FILE):
        return pd.DataFrame()
    
    df = pd.read_csv(ANALYSIS_FILE, dtype={'ticker': str})
    df['ticker'] = df['ticker'].str.zfill(6)
    return df


def load_price_data(ticker: Optional[str] = None) -> pd.DataFrame:
    """가격 데이터를 로드합니다."""
    if not os.path.exists(PRICES_FILE):
        return pd.DataFrame()
    
    df = pd.read_csv(PRICES_FILE, dtype={'ticker': str}, parse_dates=['date'])
    df['ticker'] = df['ticker'].str.zfill(6)
    
    if ticker:
        df = df[df['ticker'] == ticker.zfill(6)]
    
    return df.sort_values('date')


def format_number(value: float, decimals: int = 0) -> str:
    """숫자를 천 단위 콤마로 포맷합니다."""
    if pd.isna(value):
        return '-'
    
    if decimals == 0:
        return f"{int(value):,}"
    else:
        return f"{value:,.{decimals}f}"


def format_percent(value: float, decimals: int = 2) -> str:
    """숫자를 퍼센트로 포맷합니다."""
    if pd.isna(value):
        return '-'
    return f"{value * 100:.{decimals}f}%"


def get_color_by_score(score: float) -> str:
    """점수에 따른 색상을 반환합니다."""
    if score >= 80:
        return '#00C853'  # Green
    elif score >= 65:
        return '#64DD17'  # Light Green
    elif score >= 50:
        return '#FFC107'  # Yellow
    elif score >= 35:
        return '#FF9800'  # Orange
    else:
        return '#F44336'  # Red


def get_grade_color(grade: str) -> str:
    """등급에 따른 색상을 반환합니다."""
    grade_colors = {
        'S급 (즉시 매수)': '#00C853',
        'A급 (적극 매수)': '#64DD17',
        'B급 (매수 고려)': '#CDDC39',
        'C급 (중립)': '#FFC107',
        'D급 (매도 고려)': '#FF9800',
        'F급 (회피)': '#F44336'
    }
    return grade_colors.get(grade, '#9E9E9E')


def create_price_chart(
    df: pd.DataFrame,
    title: str = "주가 차트",
    show_ma: bool = True,
    show_volume: bool = True
) -> go.Figure:
    """
    캔들스틱 차트를 생성합니다.
    
    Args:
        df: OHLCV 데이터
        title: 차트 제목
        show_ma: 이동평균선 표시 여부
        show_volume: 거래량 표시 여부
    
    Returns:
        Plotly Figure
    """
    if df.empty:
        return go.Figure()
    
    # 서브플롯 설정
    row_heights = [0.7, 0.3] if show_volume else [1]
    rows = 2 if show_volume else 1
    
    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        row_heights=row_heights,
        vertical_spacing=0.05
    )
    
    # 캔들스틱
    fig.add_trace(
        go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='Price',
            increasing_line_color='#F44336',  # 한국식: 상승=빨강
            decreasing_line_color='#2196F3'   # 하락=파랑
        ),
        row=1, col=1
    )
    
    # 이동평균선
    if show_ma:
        colors = {'MA20': '#FFA726', 'MA50': '#42A5F5', 'MA200': '#9C27B0'}
        
        for ma_name, window in [('MA20', 20), ('MA50', 50), ('MA200', 200)]:
            if len(df) >= window:
                ma = df['close'].rolling(window=window).mean()
                fig.add_trace(
                    go.Scatter(
                        x=df['date'],
                        y=ma,
                        name=ma_name,
                        line=dict(color=colors[ma_name], width=1)
                    ),
                    row=1, col=1
                )
    
    # 거래량
    if show_volume:
        colors = ['#F44336' if c >= o else '#2196F3' 
                  for c, o in zip(df['close'], df['open'])]
        
        fig.add_trace(
            go.Bar(
                x=df['date'],
                y=df['volume'],
                name='Volume',
                marker_color=colors,
                opacity=0.7
            ),
            row=2, col=1
        )
    
    # 레이아웃
    fig.update_layout(
        title=title,
        template='plotly_dark',
        height=600,
        xaxis_rangeslider_visible=False,
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        )
    )
    
    fig.update_xaxes(
        rangebreaks=[
            dict(bounds=['sat', 'mon']),  # 주말 제외
        ]
    )
    
    return fig


def create_score_gauge(score: float, title: str = "종합 점수") -> go.Figure:
    """점수 게이지 차트를 생성합니다."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': get_color_by_score(score)},
            'steps': [
                {'range': [0, 35], 'color': '#FFEBEE'},
                {'range': [35, 50], 'color': '#FFF3E0'},
                {'range': [50, 65], 'color': '#FFFDE7'},
                {'range': [65, 80], 'color': '#F1F8E9'},
                {'range': [80, 100], 'color': '#E8F5E9'}
            ],
            'threshold': {
                'line': {'color': 'red', 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    
    fig.update_layout(
        template='plotly_dark',
        height=300
    )
    
    return fig


def create_wave_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """파동 단계 분포 차트를 생성합니다."""
    if df.empty or 'wave_stage' not in df.columns:
        return go.Figure()
    
    stage_counts = df['wave_stage'].value_counts()
    
    fig = go.Figure(data=[
        go.Pie(
            labels=stage_counts.index,
            values=stage_counts.values,
            hole=0.4,
            marker_colors=px.colors.qualitative.Set2
        )
    ])
    
    fig.update_layout(
        title="파동 단계 분포",
        template='plotly_dark',
        height=400
    )
    
    return fig


def create_grade_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """투자 등급 분포 차트를 생성합니다."""
    if df.empty or 'investment_grade' not in df.columns:
        return go.Figure()
    
    grade_order = [
        'S급 (즉시 매수)', 'A급 (적극 매수)', 'B급 (매수 고려)',
        'C급 (중립)', 'D급 (매도 고려)', 'F급 (회피)'
    ]
    
    grade_counts = df['investment_grade'].value_counts()
    
    # 순서대로 정렬
    ordered_grades = []
    ordered_counts = []
    ordered_colors = []
    
    for grade in grade_order:
        if grade in grade_counts.index:
            ordered_grades.append(grade)
            ordered_counts.append(grade_counts[grade])
            ordered_colors.append(get_grade_color(grade))
    
    fig = go.Figure(data=[
        go.Bar(
            x=ordered_grades,
            y=ordered_counts,
            marker_color=ordered_colors
        )
    ])
    
    fig.update_layout(
        title="투자 등급 분포",
        template='plotly_dark',
        height=400,
        xaxis_title="등급",
        yaxis_title="종목 수"
    )
    
    return fig


def create_sector_heatmap(df: pd.DataFrame) -> go.Figure:
    """섹터별 히트맵을 생성합니다."""
    if df.empty or 'market' not in df.columns:
        return go.Figure()
    
    # 시장별 평균 점수
    market_scores = df.groupby('market')['final_investment_score'].agg(['mean', 'count'])
    market_scores = market_scores.sort_values('mean', ascending=False)
    
    fig = go.Figure(data=[
        go.Bar(
            x=market_scores.index,
            y=market_scores['mean'],
            text=market_scores['count'].apply(lambda x: f'{int(x)}종목'),
            textposition='auto',
            marker_color=[get_color_by_score(s) for s in market_scores['mean']]
        )
    ])
    
    fig.update_layout(
        title="시장별 평균 점수",
        template='plotly_dark',
        height=300,
        xaxis_title="시장",
        yaxis_title="평균 점수"
    )
    
    return fig


def get_top_stocks(df: pd.DataFrame, n: int = 10, ascending: bool = False) -> pd.DataFrame:
    """상위/하위 종목을 반환합니다."""
    if df.empty:
        return pd.DataFrame()
    
    sorted_df = df.sort_values('final_investment_score', ascending=ascending)
    return sorted_df.head(n)


def get_summary_stats(df: pd.DataFrame) -> Dict:
    """요약 통계를 반환합니다."""
    if df.empty:
        return {}
    
    return {
        'total_stocks': len(df),
        'avg_score': df['final_investment_score'].mean(),
        'max_score': df['final_investment_score'].max(),
        'min_score': df['final_investment_score'].min(),
        's_grade_count': len(df[df['investment_grade'] == 'S급 (즉시 매수)']),
        'a_grade_count': len(df[df['investment_grade'] == 'A급 (적극 매수)']),
        'analysis_date': df['current_date'].iloc[0] if 'current_date' in df.columns else 'N/A'
    }
