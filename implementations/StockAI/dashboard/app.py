#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dashboard/app.py
StockAI Streamlit 대시보드

사용법:
    streamlit run dashboard/app.py
"""

import os
import sys

# 부모 디렉토리를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from dashboard.utils import (
    load_analysis_results,
    load_price_data,
    format_number,
    format_percent,
    get_color_by_score,
    get_grade_color,
    create_price_chart,
    create_score_gauge,
    create_wave_distribution_chart,
    create_grade_distribution_chart,
    create_sector_heatmap,
    get_top_stocks,
    get_summary_stats
)

# 페이지 설정
st.set_page_config(
    page_title="🥝 StockAI Dashboard",
    page_icon="🥝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #4CAF50;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .stock-grade-s { color: #00C853; font-weight: bold; }
    .stock-grade-a { color: #64DD17; font-weight: bold; }
    .stock-grade-b { color: #CDDC39; font-weight: bold; }
    .stock-grade-c { color: #FFC107; font-weight: bold; }
    .stock-grade-d { color: #FF9800; font-weight: bold; }
    .stock-grade-f { color: #F44336; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


def render_overview():
    """개요 페이지를 렌더링합니다."""
    st.markdown("## 📊 시장 개요")
    
    # 데이터 로드
    df = load_analysis_results()
    
    if df.empty:
        st.warning("분석 데이터가 없습니다. `python run_analysis.py`를 실행해주세요.")
        return
    
    # 요약 통계
    stats = get_summary_stats(df)
    
    # 메트릭 카드
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📈 분석 종목", f"{stats['total_stocks']:,}개")
    
    with col2:
        st.metric("⭐ 평균 점수", f"{stats['avg_score']:.1f}점")
    
    with col3:
        st.metric("🏆 S급 종목", f"{stats['s_grade_count']}개")
    
    with col4:
        st.metric("🥇 A급 종목", f"{stats['a_grade_count']}개")
    
    with col5:
        st.metric("📅 분석일", stats.get('analysis_date', 'N/A'))
    
    st.markdown("---")
    
    # 차트
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(
            create_grade_distribution_chart(df),
            use_container_width=True
        )
    
    with col2:
        st.plotly_chart(
            create_wave_distribution_chart(df),
            use_container_width=True
        )
    
    # 섹터 히트맵
    st.plotly_chart(
        create_sector_heatmap(df),
        use_container_width=True
    )


def render_top_picks():
    """상위 추천 종목 페이지를 렌더링합니다."""
    st.markdown("## 🏆 상위 추천 종목")
    
    df = load_analysis_results()
    
    if df.empty:
        st.warning("분석 데이터가 없습니다.")
        return
    
    # 필터
    col1, col2, col3 = st.columns(3)
    
    with col1:
        n_stocks = st.slider("표시 종목 수", 5, 50, 20)
    
    with col2:
        market_filter = st.multiselect(
            "시장 선택",
            options=df['market'].unique().tolist(),
            default=df['market'].unique().tolist()
        )
    
    with col3:
        min_score = st.slider("최소 점수", 0, 100, 60)
    
    # 필터링
    filtered_df = df[
        (df['market'].isin(market_filter)) &
        (df['final_investment_score'] >= min_score)
    ]
    
    top_stocks = get_top_stocks(filtered_df, n=n_stocks)
    
    if top_stocks.empty:
        st.info("조건에 맞는 종목이 없습니다.")
        return
    
    # 테이블 표시
    display_cols = [
        'ticker', 'name', 'current_price', 'final_investment_score',
        'investment_grade', 'wave_stage', 'supply_demand_stage',
        'rsi', 'volume_ratio', 'price_change_20d'
    ]
    
    available_cols = [c for c in display_cols if c in top_stocks.columns]
    display_df = top_stocks[available_cols].copy()
    
    # 컬럼명 한글화
    col_names = {
        'ticker': '종목코드',
        'name': '종목명',
        'current_price': '현재가',
        'final_investment_score': '종합점수',
        'investment_grade': '투자등급',
        'wave_stage': '파동단계',
        'supply_demand_stage': '수급단계',
        'rsi': 'RSI',
        'volume_ratio': '거래량비율',
        'price_change_20d': '20일수익률'
    }
    
    display_df = display_df.rename(columns=col_names)
    
    # 포맷팅
    if '현재가' in display_df.columns:
        display_df['현재가'] = display_df['현재가'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else '-')
    
    if '20일수익률' in display_df.columns:
        display_df['20일수익률'] = display_df['20일수익률'].apply(
            lambda x: f"{x*100:.1f}%" if pd.notna(x) else '-'
        )
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=600
    )


def render_stock_detail():
    """종목 상세 분석 페이지를 렌더링합니다."""
    st.markdown("## 🔍 종목 상세 분석")
    
    df = load_analysis_results()
    
    if df.empty:
        st.warning("분석 데이터가 없습니다.")
        return
    
    # 종목 선택
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 검색 가능한 종목 선택
        stock_options = df.apply(
            lambda x: f"{x['ticker']} - {x['name']}", axis=1
        ).tolist()
        
        selected = st.selectbox(
            "종목 선택",
            options=stock_options,
            index=0
        )
    
    if not selected:
        return
    
    ticker = selected.split(' - ')[0]
    stock_data = df[df['ticker'] == ticker].iloc[0]
    
    # 기본 정보
    st.markdown("### 📌 기본 정보")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("종목명", stock_data['name'])
    
    with col2:
        price = stock_data.get('current_price', 0)
        st.metric("현재가", f"{int(price):,}원" if pd.notna(price) else '-')
    
    with col3:
        score = stock_data.get('final_investment_score', 0)
        st.metric("종합 점수", f"{score:.1f}점")
    
    with col4:
        grade = stock_data.get('investment_grade', 'N/A')
        st.markdown(f"**투자 등급**")
        grade_color = get_grade_color(grade)
        st.markdown(f"<span style='color:{grade_color}; font-size:1.5rem; font-weight:bold;'>{grade}</span>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 분석 상세
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🌊 파동 분석")
        
        wave_score = stock_data.get('wave_score', 0)
        wave_stage = stock_data.get('wave_stage', 'N/A')
        
        st.plotly_chart(
            create_score_gauge(wave_score, "파동 점수"),
            use_container_width=True
        )
        
        st.info(f"**파동 단계**: {wave_stage}")
    
    with col2:
        st.markdown("### 💰 수급 분석")
        
        sd_score = stock_data.get('supply_demand_score', 0)
        sd_stage = stock_data.get('supply_demand_stage', 'N/A')
        
        st.plotly_chart(
            create_score_gauge(sd_score, "수급 점수"),
            use_container_width=True
        )
        
        st.info(f"**수급 단계**: {sd_stage}")
    
    # 기술적 지표
    st.markdown("### 📈 기술적 지표")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    indicators = [
        ('RSI', 'rsi', ''),
        ('거래량 비율', 'volume_ratio', 'x'),
        ('52주 위치', 'position_52w', '%'),
        ('5일 수익률', 'price_change_5d', '%'),
        ('20일 수익률', 'price_change_20d', '%')
    ]
    
    cols = [col1, col2, col3, col4, col5]
    
    for (name, key, suffix), col in zip(indicators, cols):
        with col:
            value = stock_data.get(key, 0)
            if pd.notna(value):
                if suffix == '%':
                    display_value = f"{value * 100:.1f}%"
                elif suffix == 'x':
                    display_value = f"{value:.2f}x"
                else:
                    display_value = f"{value:.1f}"
            else:
                display_value = '-'
            st.metric(name, display_value)
    
    # 가격 차트
    st.markdown("### 📊 가격 차트")
    
    price_df = load_price_data(ticker)
    
    if not price_df.empty:
        # 기간 선택
        period = st.radio(
            "기간 선택",
            options=['1개월', '3개월', '6개월', '1년'],
            horizontal=True,
            index=2
        )
        
        period_days = {'1개월': 30, '3개월': 90, '6개월': 180, '1년': 365}
        days = period_days[period]
        
        recent_df = price_df.tail(days)
        
        chart = create_price_chart(
            recent_df,
            title=f"{stock_data['name']} ({ticker})"
        )
        
        st.plotly_chart(chart, use_container_width=True)
    else:
        st.info("가격 데이터가 없습니다.")


def render_screener():
    """스크리너 페이지를 렌더링합니다."""
    st.markdown("## 🔎 종목 스크리너")
    
    df = load_analysis_results()
    
    if df.empty:
        st.warning("분석 데이터가 없습니다.")
        return
    
    # 필터 패널
    st.markdown("### 필터 조건")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**점수 필터**")
        score_range = st.slider(
            "종합 점수 범위",
            0, 100, (60, 100)
        )
        
        wave_stages = st.multiselect(
            "파동 단계",
            options=df['wave_stage'].unique().tolist(),
            default=[]
        )
    
    with col2:
        st.markdown("**기술적 필터**")
        rsi_range = st.slider(
            "RSI 범위",
            0, 100, (30, 70)
        )
        
        volume_min = st.number_input(
            "최소 거래량 비율",
            min_value=0.0,
            max_value=10.0,
            value=0.8,
            step=0.1
        )
    
    with col3:
        st.markdown("**등급 필터**")
        grade_filter = st.multiselect(
            "투자 등급",
            options=df['investment_grade'].unique().tolist(),
            default=['S급 (즉시 매수)', 'A급 (적극 매수)']
        )
        
        market_filter = st.multiselect(
            "시장",
            options=df['market'].unique().tolist(),
            default=df['market'].unique().tolist()
        )
    
    # 필터 적용
    filtered_df = df.copy()
    
    # 점수 필터
    filtered_df = filtered_df[
        (filtered_df['final_investment_score'] >= score_range[0]) &
        (filtered_df['final_investment_score'] <= score_range[1])
    ]
    
    # 파동 필터
    if wave_stages:
        filtered_df = filtered_df[filtered_df['wave_stage'].isin(wave_stages)]
    
    # RSI 필터
    if 'rsi' in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df['rsi'] >= rsi_range[0]) &
            (filtered_df['rsi'] <= rsi_range[1])
        ]
    
    # 거래량 필터
    if 'volume_ratio' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['volume_ratio'] >= volume_min]
    
    # 등급 필터
    if grade_filter:
        filtered_df = filtered_df[filtered_df['investment_grade'].isin(grade_filter)]
    
    # 시장 필터
    if market_filter:
        filtered_df = filtered_df[filtered_df['market'].isin(market_filter)]
    
    st.markdown("---")
    
    # 결과
    st.markdown(f"### 검색 결과: **{len(filtered_df)}**개 종목")
    
    if filtered_df.empty:
        st.info("조건에 맞는 종목이 없습니다.")
        return
    
    # 정렬
    sort_by = st.selectbox(
        "정렬 기준",
        options=['final_investment_score', 'wave_score', 'rsi', 'volume_ratio'],
        format_func=lambda x: {
            'final_investment_score': '종합 점수',
            'wave_score': '파동 점수',
            'rsi': 'RSI',
            'volume_ratio': '거래량 비율'
        }.get(x, x)
    )
    
    sorted_df = filtered_df.sort_values(sort_by, ascending=False)
    
    # 표시
    st.dataframe(
        sorted_df[[
            'ticker', 'name', 'current_price', 'final_investment_score',
            'investment_grade', 'wave_stage', 'rsi', 'volume_ratio'
        ]].head(50),
        use_container_width=True,
        hide_index=True,
        height=500
    )


def render_about():
    """소개 페이지를 렌더링합니다."""
    st.markdown("## ℹ️ StockAI 소개")
    
    st.markdown("""
    ### 🥝 StockAI: Intelligent Korean Stock Analysis System
    
    StockAI는 한국 주식 시장을 위한 **올인원 자동 분석 및 투자 지원 시스템**입니다.
    
    ---
    
    ### 🎯 주요 기능
    
    1. **자동화된 데이터 파이프라인**
       - 매일 장 마감 후 전 종목 데이터 수집 및 분석
       - 네이버 금융에서 실시간 데이터 크롤링
    
    2. **파동 전환 알고리즘**
       - 하락 추세에서 상승 추세로 전환되는 '변곡점' 포착
       - 4단계 파동 분류 시스템
    
    3. **AI 애널리스트**
       - Gemini Pro가 수집된 종목의 뉴스를 분석
       - 매수/매도 의견 제시
    
    4. **종합 투자 점수**
       - 기술적 분석 + 펀더멘털 + 수급을 결합한 종합 점수
       - S/A/B/C/D/F 6단계 투자 등급
    
    ---
    
    ### 🌊 파동 분석 방법론
    
    | 단계 | 점수 | 설명 |
    |------|------|------|
    | 2단계 중기 | 90점 | 강력한 상승 추세, 정배열, 거래량 급증 |
    | 2단계 초기 | 80점 | 상승 시작, 골든크로스 이후 |
    | 1→2단계 전환 | 70점 | 바닥 탈출 시도 |
    | 일반 상승 | 60점 | 기본적인 상승 흐름 |
    
    ---
    
    ### 📊 사용 방법
    
    ```bash
    # 1. 전체 분석 실행
    python run_analysis.py
    
    # 2. 대시보드 실행
    streamlit run dashboard/app.py
    ```
    
    ---
    
    > ⚠️ **면책 조항**: 본 시스템의 분석 결과는 투자 조언이 아닙니다. 
    > 투자 결정은 본인의 판단과 책임 하에 이루어져야 합니다.
    """)


def main():
    """메인 함수"""
    # 사이드바
    st.sidebar.markdown("# 🥝 StockAI")
    st.sidebar.markdown("---")
    
    # 메뉴
    menu_options = {
        '📊 시장 개요': render_overview,
        '🏆 상위 추천': render_top_picks,
        '🔍 종목 상세': render_stock_detail,
        '🔎 스크리너': render_screener,
        'ℹ️ 소개': render_about
    }
    
    selected_menu = st.sidebar.radio(
        "메뉴 선택",
        options=list(menu_options.keys())
    )
    
    st.sidebar.markdown("---")
    
    # 데이터 새로고침 버튼
    if st.sidebar.button("🔄 데이터 새로고침"):
        st.cache_data.clear()
        st.rerun()
    
    # 마지막 업데이트 시간
    df = load_analysis_results()
    if not df.empty and 'current_date' in df.columns:
        st.sidebar.markdown(f"📅 최근 분석: {df['current_date'].iloc[0]}")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("Made with ❤️ by StockAI")
    
    # 선택된 메뉴 렌더링
    menu_options[selected_menu]()


if __name__ == "__main__":
    main()
