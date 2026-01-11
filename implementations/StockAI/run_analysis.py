#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_analysis.py
전체 분석 파이프라인을 실행하는 오케스트레이터

실행 순서:
1. 일별 시세 수집 (create_complete_daily_prices.py)
2. 기관/외국인 수급 분석 (all_institutional_trend_data.py)
3. 파동 분석 및 등급 산출 (analysis2.py)
4. AI 심층 분석 (investigate_top_stocks.py) - 선택

사용법:
    python run_analysis.py           # 전체 파이프라인 실행
    python run_analysis.py --quick   # 빠른 업데이트 (오늘 데이터만)
    python run_analysis.py --skip-ai # AI 분석 건너뛰기
"""

import os
import sys
import time
import subprocess
import argparse
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 상수 정의
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def run_script(script_name: str, args: list = None, timeout: int = 600) -> bool:
    """
    Python 스크립트를 실행합니다.
    
    Args:
        script_name: 스크립트 파일명
        args: 추가 인자 리스트
        timeout: 타임아웃 (초)
    
    Returns:
        성공 여부
    """
    script_path = os.path.join(BASE_DIR, script_name)
    
    if not os.path.exists(script_path):
        logger.error(f"Script not found: {script_path}")
        return False
    
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    
    logger.info(f"Running: {script_name}")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            timeout=timeout,
            capture_output=True,
            text=True,
            cwd=BASE_DIR
        )
        
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            logger.info(f"✅ {script_name} completed in {elapsed:.1f}s")
            return True
        else:
            logger.error(f"❌ {script_name} failed:")
            logger.error(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"❌ {script_name} timed out after {timeout}s")
        return False
    except Exception as e:
        logger.error(f"❌ {script_name} error: {e}")
        return False


def run_full_pipeline(quick_update: bool = False, skip_ai: bool = False, top_n: int = 10):
    """
    전체 분석 파이프라인을 실행합니다.
    
    Args:
        quick_update: 빠른 업데이트 모드 (오늘 데이터만)
        skip_ai: AI 분석 건너뛰기
        top_n: AI 분석할 상위 종목 수
    """
    logger.info("=" * 60)
    logger.info("🥝 StockAI Analysis Pipeline Started")
    logger.info(f"   Mode: {'Quick Update' if quick_update else 'Full Analysis'}")
    logger.info(f"   AI Analysis: {'Disabled' if skip_ai else 'Enabled'}")
    logger.info(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    total_start = time.time()
    results = {}
    
    # Step 1: 일별 시세 수집
    logger.info("\n📊 Step 1/4: Collecting Daily Prices...")
    price_args = ['--update'] if quick_update else ['--days', '365']
    results['prices'] = run_script('create_complete_daily_prices.py', price_args, timeout=1200)
    
    if not results['prices']:
        logger.error("Price collection failed. Aborting pipeline.")
        return results
    
    # Step 2: 기관/외국인 수급 분석
    logger.info("\n💰 Step 2/4: Analyzing Institutional Trends...")
    results['institutional'] = run_script('all_institutional_trend_data.py', timeout=900)
    
    # Step 3: 파동 분석
    logger.info("\n🌊 Step 3/4: Running Wave Analysis...")
    results['analysis'] = run_script('analysis2.py', timeout=300)
    
    if not results['analysis']:
        logger.error("Wave analysis failed. Skipping AI investigation.")
        skip_ai = True
    
    # Step 4: AI 심층 분석 (선택)
    if not skip_ai:
        logger.info("\n🤖 Step 4/4: AI Deep Investigation...")
        ai_args = ['--top', str(top_n)]
        results['ai'] = run_script('investigate_top_stocks.py', ai_args, timeout=600)
    else:
        logger.info("\n⏭️ Step 4/4: AI Analysis Skipped")
        results['ai'] = None
    
    # 요약
    total_elapsed = time.time() - total_start
    
    logger.info("\n" + "=" * 60)
    logger.info("📋 Pipeline Summary")
    logger.info("=" * 60)
    
    for step, success in results.items():
        if success is None:
            status = "⏭️ Skipped"
        elif success:
            status = "✅ Success"
        else:
            status = "❌ Failed"
        logger.info(f"   {step.capitalize()}: {status}")
    
    logger.info(f"\n   Total Time: {total_elapsed/60:.1f} minutes")
    logger.info("=" * 60)
    
    # 다음 단계 안내
    logger.info("\n🎯 Next Steps:")
    logger.info("   1. View results: python -c \"import pandas as pd; print(pd.read_csv('wave_transition_analysis_results.csv').head(20))\"")
    logger.info("   2. Launch dashboard: streamlit run dashboard/app.py")
    logger.info("   3. Check AI report: ls -la ai_analysis_report_*.md")
    
    return results


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description='StockAI Analysis Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_analysis.py               # Full analysis
  python run_analysis.py --quick       # Quick update (today only)
  python run_analysis.py --skip-ai     # Skip AI analysis
  python run_analysis.py --top 20      # Analyze top 20 stocks with AI
        """
    )
    
    parser.add_argument(
        '--quick', '-q',
        action='store_true',
        help='Quick update mode (collect only recent data)'
    )
    
    parser.add_argument(
        '--skip-ai', '-s',
        action='store_true',
        help='Skip AI deep investigation'
    )
    
    parser.add_argument(
        '--top', '-t',
        type=int,
        default=10,
        help='Number of top stocks for AI analysis (default: 10)'
    )
    
    args = parser.parse_args()
    
    try:
        results = run_full_pipeline(
            quick_update=args.quick,
            skip_ai=args.skip_ai,
            top_n=args.top
        )
        
        # 전체 성공 여부에 따른 종료 코드
        all_success = all(v is None or v for v in results.values())
        sys.exit(0 if all_success else 1)
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n❌ Pipeline error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
