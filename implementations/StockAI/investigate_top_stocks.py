#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
investigate_top_stocks.py
상위 종목에 대한 AI 기반 심층 분석을 수행합니다.

주요 기능:
- DuckDuckGo를 통한 뉴스 검색
- Gemini Pro를 활용한 뉴스 분석
- 투자 의견 및 리포트 생성
"""

import os
import time
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import logging
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 상수 정의
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ANALYSIS_FILE = os.path.join(BASE_DIR, 'wave_transition_analysis_results.csv')


def search_stock_news(stock_name: str, ticker: str, max_results: int = 5) -> List[Dict]:
    """
    DuckDuckGo를 사용하여 종목 관련 뉴스를 검색합니다.
    
    Args:
        stock_name: 종목명
        ticker: 종목 코드
        max_results: 최대 결과 수
    
    Returns:
        뉴스 리스트 [{title, url, body}, ...]
    """
    try:
        from duckduckgo_search import DDGS
        
        # 검색 쿼리 구성
        query = f"{stock_name} 주식 뉴스"
        
        news_results = []
        
        with DDGS() as ddgs:
            results = ddgs.news(query, max_results=max_results)
            
            for result in results:
                news_results.append({
                    'title': result.get('title', ''),
                    'url': result.get('url', ''),
                    'body': result.get('body', ''),
                    'date': result.get('date', ''),
                    'source': result.get('source', '')
                })
        
        logger.info(f"Found {len(news_results)} news for {stock_name}")
        return news_results
        
    except ImportError:
        logger.warning("duckduckgo-search not installed. Install with: pip install duckduckgo-search")
        return []
    except Exception as e:
        logger.warning(f"News search failed for {stock_name}: {e}")
        return []


def analyze_with_gemini(stock_name: str, ticker: str, news: List[Dict], stock_data: Dict) -> str:
    """
    Gemini AI를 사용하여 종목을 분석합니다.
    
    Args:
        stock_name: 종목명
        ticker: 종목 코드
        news: 뉴스 리스트
        stock_data: 종목 분석 데이터
    
    Returns:
        AI 분석 결과 텍스트
    """
    api_key = os.getenv('GOOGLE_API_KEY')
    
    if not api_key:
        logger.warning("GOOGLE_API_KEY not set. Skipping AI analysis.")
        return "API 키가 설정되지 않아 AI 분석을 수행할 수 없습니다."
    
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        # 프롬프트 구성
        news_text = "\n".join([
            f"- {n['title']} ({n['source']}): {n['body'][:200]}..."
            for n in news[:5]
        ]) if news else "관련 뉴스 없음"
        
        prompt = f"""
당신은 전문 주식 애널리스트입니다. 아래 정보를 바탕으로 투자 분석을 수행해주세요.

## 종목 정보
- 종목명: {stock_name}
- 종목코드: {ticker}
- 현재가: {stock_data.get('current_price', 'N/A')}원
- 파동 단계: {stock_data.get('wave_stage', 'N/A')}
- 파동 점수: {stock_data.get('wave_score', 'N/A')}점
- 수급 단계: {stock_data.get('supply_demand_stage', 'N/A')}
- 종합 점수: {stock_data.get('final_investment_score', 'N/A')}점
- 투자 등급: {stock_data.get('investment_grade', 'N/A')}

## 기술적 지표
- RSI: {stock_data.get('rsi', 'N/A')}
- 52주 대비 위치: {stock_data.get('position_52w', 'N/A')}%
- 거래량 비율: {stock_data.get('volume_ratio', 'N/A')}x
- 20일 수익률: {float(stock_data.get('price_change_20d', 0)) * 100:.1f}%

## 최근 뉴스
{news_text}

## 요청사항
1. 종목의 현재 상황을 간단히 요약해주세요.
2. 기술적 분석 관점에서의 의견을 제시해주세요.
3. 뉴스 기반 리스크/기회 요인을 분석해주세요.
4. 최종 투자 의견 (매수/중립/매도)과 근거를 제시해주세요.

분석은 한국어로 작성하고, 간결하면서도 핵심을 담아주세요.
"""

        response = model.generate_content(prompt)
        
        if response.text:
            return response.text
        else:
            return "AI 응답을 생성할 수 없습니다."
            
    except ImportError:
        logger.warning("google-generativeai not installed. Install with: pip install google-generativeai")
        return "Gemini 라이브러리가 설치되지 않았습니다."
    except Exception as e:
        logger.error(f"Gemini analysis failed: {e}")
        return f"AI 분석 중 오류 발생: {str(e)}"


def generate_report(analyses: List[Dict], output_path: str):
    """
    분석 결과를 마크다운 리포트로 생성합니다.
    
    Args:
        analyses: 분석 결과 리스트
        output_path: 출력 파일 경로
    """
    report = f"""# 🥝 StockAI 투자 분석 리포트

**생성일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

"""
    
    for i, analysis in enumerate(analyses, 1):
        report += f"""
## {i}. {analysis['name']} ({analysis['ticker']})

### 기본 정보
| 항목 | 값 |
|------|-----|
| 현재가 | {analysis.get('current_price', 'N/A'):,}원 |
| 투자 등급 | {analysis.get('investment_grade', 'N/A')} |
| 종합 점수 | {analysis.get('final_investment_score', 'N/A')}점 |
| 파동 단계 | {analysis.get('wave_stage', 'N/A')} |

### AI 분석

{analysis.get('ai_analysis', '분석 없음')}

---

"""
    
    report += """
> 본 리포트는 AI에 의해 자동 생성되었으며, 투자 결정의 유일한 근거로 사용되어서는 안 됩니다.
> 투자의 책임은 투자자 본인에게 있습니다.
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"Report saved to {output_path}")


def investigate_top_stocks(top_n: int = 10, skip_ai: bool = False) -> List[Dict]:
    """
    상위 종목을 분석합니다.
    
    Args:
        top_n: 분석할 상위 종목 수
        skip_ai: AI 분석 건너뛰기 여부
    
    Returns:
        분석 결과 리스트
    """
    # 분석 결과 로드
    if not os.path.exists(ANALYSIS_FILE):
        logger.error(f"Analysis file not found: {ANALYSIS_FILE}")
        logger.info("Run 'python analysis2.py' first to generate analysis results.")
        return []
    
    df = pd.read_csv(ANALYSIS_FILE, dtype={'ticker': str})
    df['ticker'] = df['ticker'].str.zfill(6)
    
    # 상위 N개 추출
    top_stocks = df.head(top_n)
    logger.info(f"Investigating top {len(top_stocks)} stocks...")
    
    analyses = []
    
    for _, row in top_stocks.iterrows():
        ticker = row['ticker']
        name = row['name']
        
        logger.info(f"Analyzing {name} ({ticker})...")
        
        stock_data = row.to_dict()
        
        # 뉴스 검색
        news = search_stock_news(name, ticker)
        time.sleep(1)  # Rate limiting
        
        # AI 분석
        if skip_ai:
            ai_analysis = "AI 분석이 건너뛰어졌습니다."
        else:
            ai_analysis = analyze_with_gemini(name, ticker, news, stock_data)
            time.sleep(2)  # Rate limiting for API
        
        analysis = {
            **stock_data,
            'news': news,
            'ai_analysis': ai_analysis
        }
        
        analyses.append(analysis)
    
    return analyses


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Investigate top stocks with AI analysis')
    parser.add_argument('--top', type=int, default=10, help='Number of top stocks to analyze')
    parser.add_argument('--skip-ai', action='store_true', help='Skip AI analysis (news only)')
    parser.add_argument('--output', type=str, default=None, help='Output report path')
    args = parser.parse_args()
    
    logger.info("=" * 50)
    logger.info("Starting AI Stock Investigation")
    logger.info("=" * 50)
    
    start_time = time.time()
    
    # 분석 수행
    analyses = investigate_top_stocks(top_n=args.top, skip_ai=args.skip_ai)
    
    if analyses:
        # 리포트 생성
        output_path = args.output or os.path.join(
            BASE_DIR, 
            f"ai_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )
        generate_report(analyses, output_path)
        
        # 요약 출력
        logger.info("\n" + "=" * 50)
        logger.info("Investigation Summary:")
        logger.info(f"  - Stocks analyzed: {len(analyses)}")
        logger.info(f"  - Report saved: {output_path}")
        logger.info(f"  - Elapsed time: {time.time() - start_time:.1f} seconds")
        logger.info("=" * 50)
    else:
        logger.error("No analyses completed!")


if __name__ == "__main__":
    main()
