#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
US Stock Analysis - Full Pipeline Update Script
Runs all analysis scripts in sequence
"""

import os
import sys
import subprocess
import time
import argparse
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Script execution order with descriptions and timeouts
SCRIPTS = [
    # Part 1: Data Collection
    ("create_us_daily_prices.py", "Price Data Collection", 600),
    ("analyze_volume.py", "Volume Analysis", 300),
    ("analyze_13f.py", "Institutional Holdings", 600),
    ("analyze_etf_flows.py", "ETF Fund Flows", 300),
    
    # Part 2: Analysis/Screening
    ("smart_money_screener_v2.py", "Smart Money Screening", 600),
    ("sector_heatmap.py", "Sector Heatmap", 300),
    ("options_flow.py", "Options Flow", 300),
    ("insider_tracker.py", "Insider Tracking", 300),
    ("portfolio_risk.py", "Portfolio Risk", 300),
    
    # Part 3: AI Analysis
    ("macro_analyzer.py", "Macro Analysis", 300),
    ("ai_summary_generator.py", "AI Summaries", 900),
    ("final_report_generator.py", "Final Report", 60),
    ("economic_calendar.py", "Economic Calendar", 300),
]

# Quick mode skips these scripts
AI_SCRIPTS = ["ai_summary_generator.py", "macro_analyzer.py"]


def run_script(script_name: str, description: str, timeout: int) -> bool:
    """Run a single script with timeout"""
    logger.info(f"\n{'='*60}")
    logger.info(f"Running: {description}")
    logger.info(f"Script: {script_name}")
    logger.info(f"Timeout: {timeout}s")
    logger.info('='*60)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            timeout=timeout,
            capture_output=True,
            text=True
        )
        
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            logger.info(f"SUCCESS: {description} ({elapsed:.1f}s)")
            if result.stdout:
                # Print last few lines of output
                lines = result.stdout.strip().split('\n')
                for line in lines[-5:]:
                    logger.info(f"  > {line}")
            return True
        else:
            logger.error(f"FAILED: {description}")
            if result.stderr:
                logger.error(f"Error: {result.stderr[:500]}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"TIMEOUT: {description} exceeded {timeout}s")
        return False
    except FileNotFoundError:
        logger.error(f"NOT FOUND: {script_name}")
        return False
    except Exception as e:
        logger.error(f"ERROR: {description} - {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='US Stock Analysis Pipeline')
    parser.add_argument('--quick', action='store_true', 
                       help='Quick mode: skip AI-heavy scripts')
    parser.add_argument('--skip', nargs='+', default=[], 
                       help='Scripts to skip')
    parser.add_argument('--only', nargs='+', default=[], 
                       help='Only run these scripts')
    parser.add_argument('--dir', default='.', 
                       help='Working directory')
    args = parser.parse_args()
    
    # Change to working directory
    if args.dir != '.':
        os.chdir(args.dir)
    
    logger.info(f"\n{'#'*60}")
    logger.info(f"US Stock Analysis Pipeline")
    logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Mode: {'Quick' if args.quick else 'Full'}")
    logger.info(f"{'#'*60}")
    
    start_time = time.time()
    results = []
    
    for script_name, description, timeout in SCRIPTS:
        # Skip logic
        if args.only and script_name not in args.only:
            continue
        
        if script_name in args.skip:
            logger.info(f"SKIPPED: {description}")
            results.append((script_name, description, 'skipped'))
            continue
        
        if args.quick and script_name in AI_SCRIPTS:
            logger.info(f"SKIPPED (quick mode): {description}")
            results.append((script_name, description, 'skipped'))
            continue
        
        # Check if script exists
        if not os.path.exists(script_name):
            logger.warning(f"Script not found: {script_name}")
            results.append((script_name, description, 'not found'))
            continue
        
        # Run script
        success = run_script(script_name, description, timeout)
        results.append((script_name, description, 'success' if success else 'failed'))
    
    # Summary
    total_time = time.time() - start_time
    
    logger.info(f"\n{'#'*60}")
    logger.info(f"Pipeline Complete")
    logger.info(f"Total Time: {total_time/60:.1f} minutes")
    logger.info(f"{'#'*60}")
    
    logger.info("\nResults Summary:")
    logger.info("-" * 50)
    
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    for script, desc, status in results:
        emoji = {"success": "ok", "failed": "FAIL", "skipped": "skip", "not found": "?"}
        logger.info(f"  [{emoji.get(status, '?'):4}] {desc}")
        
        if status == 'success':
            success_count += 1
        elif status == 'failed':
            failed_count += 1
        else:
            skipped_count += 1
    
    logger.info("-" * 50)
    logger.info(f"Success: {success_count} | Failed: {failed_count} | Skipped: {skipped_count}")
    
    # Return exit code based on failures
    sys.exit(1 if failed_count > 0 else 0)


if __name__ == "__main__":
    main()
