#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
notifier.py
StockAI 알림 시스템 (Telegram, Discord, Slack)

사용법:
    python notifier.py --test                    # 테스트 메시지 전송
    python notifier.py --notify                  # 새 추천 종목 알림
    python notifier.py --report                  # 일일 리포트 전송

환경 변수 (.env):
    TELEGRAM_BOT_TOKEN=your_bot_token
    TELEGRAM_CHAT_ID=your_chat_id
    DISCORD_WEBHOOK_URL=your_webhook_url
    SLACK_WEBHOOK_URL=your_webhook_url
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional

import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_FILE = os.path.join(BASE_DIR, 'wave_transition_analysis_results.csv')


class TelegramNotifier:
    """Telegram 알림 전송"""

    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def send_message(self, text: str, parse_mode: str = 'Markdown') -> bool:
        """메시지 전송"""
        if not self.is_configured():
            logger.warning("Telegram not configured")
            return False

        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }

            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                logger.info("Telegram message sent successfully")
                return True
            else:
                logger.error(f"Telegram error: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Telegram error: {e}")
            return False


class DiscordNotifier:
    """Discord Webhook 알림"""

    def __init__(self):
        self.webhook_url = os.getenv('DISCORD_WEBHOOK_URL')

    def is_configured(self) -> bool:
        return bool(self.webhook_url)

    def send_message(self, content: str, embeds: List[Dict] = None) -> bool:
        """메시지 전송"""
        if not self.is_configured():
            logger.warning("Discord not configured")
            return False

        try:
            payload = {'content': content}
            if embeds:
                payload['embeds'] = embeds

            resp = requests.post(self.webhook_url, json=payload, timeout=10)
            if resp.status_code in [200, 204]:
                logger.info("Discord message sent successfully")
                return True
            else:
                logger.error(f"Discord error: {resp.status_code}")
                return False
        except Exception as e:
            logger.error(f"Discord error: {e}")
            return False


class SlackNotifier:
    """Slack Webhook 알림"""

    def __init__(self):
        self.webhook_url = os.getenv('SLACK_WEBHOOK_URL')

    def is_configured(self) -> bool:
        return bool(self.webhook_url)

    def send_message(self, text: str, blocks: List[Dict] = None) -> bool:
        """메시지 전송"""
        if not self.is_configured():
            logger.warning("Slack not configured")
            return False

        try:
            payload = {'text': text}
            if blocks:
                payload['blocks'] = blocks

            resp = requests.post(self.webhook_url, json=payload, timeout=10)
            if resp.status_code == 200:
                logger.info("Slack message sent successfully")
                return True
            else:
                logger.error(f"Slack error: {resp.status_code}")
                return False
        except Exception as e:
            logger.error(f"Slack error: {e}")
            return False


class StockNotifier:
    """통합 알림 시스템"""

    def __init__(self):
        self.telegram = TelegramNotifier()
        self.discord = DiscordNotifier()
        self.slack = SlackNotifier()

    def get_new_picks(self, grades: List[str] = None) -> pd.DataFrame:
        """새로운 추천 종목 가져오기"""
        if grades is None:
            grades = ['S급 (즉시 매수)', 'A급 (적극 매수)']

        if not os.path.exists(RESULTS_FILE):
            return pd.DataFrame()

        df = pd.read_csv(RESULTS_FILE, dtype={'ticker': str})
        df['ticker'] = df['ticker'].str.zfill(6)

        return df[df['investment_grade'].isin(grades)]

    def format_telegram_message(self, picks: pd.DataFrame) -> str:
        """Telegram 메시지 포맷"""
        today = datetime.now().strftime('%Y-%m-%d')

        msg = f"🥝 *StockAI 추천 종목*\n"
        msg += f"📅 {today}\n\n"

        for _, row in picks.head(10).iterrows():
            grade = row['investment_grade'].split(' ')[0]
            emoji = '🏆' if 'S' in grade else '🥇' if 'A' in grade else '📊'

            msg += f"{emoji} *{row['ticker']}* {row['name']}\n"
            msg += f"   점수: {row['final_investment_score']:.1f} | {grade}\n"
            msg += f"   가격: {int(row['current_price']):,}원\n\n"

        msg += f"총 {len(picks)}개 종목 추천\n"
        msg += f"#StockAI #주식분석"

        return msg

    def format_discord_embed(self, picks: pd.DataFrame) -> List[Dict]:
        """Discord Embed 포맷"""
        today = datetime.now().strftime('%Y-%m-%d')

        fields = []
        for _, row in picks.head(10).iterrows():
            grade = row['investment_grade'].split(' ')[0]
            fields.append({
                'name': f"{row['ticker']} {row['name']}",
                'value': f"점수: {row['final_investment_score']:.1f} | {grade}\n가격: {int(row['current_price']):,}원",
                'inline': True
            })

        embed = {
            'title': '🥝 StockAI 추천 종목',
            'description': f'분석일: {today}',
            'color': 0x4ade80,
            'fields': fields,
            'footer': {'text': f'총 {len(picks)}개 종목 추천'}
        }

        return [embed]

    def notify_new_picks(self):
        """새로운 추천 종목 알림"""
        picks = self.get_new_picks()

        if picks.empty:
            logger.info("No new picks to notify")
            return

        # Telegram
        if self.telegram.is_configured():
            msg = self.format_telegram_message(picks)
            self.telegram.send_message(msg)

        # Discord
        if self.discord.is_configured():
            embeds = self.format_discord_embed(picks)
            self.discord.send_message("🥝 새로운 추천 종목이 있습니다!", embeds)

        # Slack
        if self.slack.is_configured():
            msg = self.format_telegram_message(picks)  # 같은 포맷 재사용
            self.slack.send_message(msg.replace('*', '*'))

    def send_daily_report(self):
        """일일 리포트 전송"""
        from track_performance import PerformanceTracker

        tracker = PerformanceTracker()
        report = tracker.generate_report()

        if not report:
            logger.warning("No performance data for daily report")
            return

        today = datetime.now().strftime('%Y-%m-%d')

        msg = f"📊 *StockAI 일일 리포트*\n"
        msg += f"📅 {today}\n\n"

        msg += f"📈 *성과 요약*\n"
        msg += f"• 평균 수익률: {report['avg_return']:.2f}%\n"
        msg += f"• 승률: {report['win_rate']:.1f}%\n"
        msg += f"• 총 추천: {report['total_picks']}개\n\n"

        if report.get('best_pick'):
            bp = report['best_pick']
            msg += f"🏆 *최고 수익*: {bp['ticker']} {bp['name']} (+{bp['return_pct']:.1f}%)\n"

        if report.get('worst_pick'):
            wp = report['worst_pick']
            msg += f"📉 *최저 수익*: {wp['ticker']} {wp['name']} ({wp['return_pct']:.1f}%)\n"

        # Send to all configured channels
        if self.telegram.is_configured():
            self.telegram.send_message(msg)

        if self.discord.is_configured():
            self.discord.send_message(msg.replace('*', '**'))

        if self.slack.is_configured():
            self.slack.send_message(msg.replace('*', '*'))

    def send_test_message(self):
        """테스트 메시지 전송"""
        msg = "🥝 StockAI 알림 테스트\n\n이 메시지가 보이면 알림 설정이 완료된 것입니다!"

        sent = False

        if self.telegram.is_configured():
            if self.telegram.send_message(msg):
                sent = True
                print("✓ Telegram: 전송 성공")
            else:
                print("✗ Telegram: 전송 실패")
        else:
            print("- Telegram: 미설정")

        if self.discord.is_configured():
            if self.discord.send_message(msg):
                sent = True
                print("✓ Discord: 전송 성공")
            else:
                print("✗ Discord: 전송 실패")
        else:
            print("- Discord: 미설정")

        if self.slack.is_configured():
            if self.slack.send_message(msg):
                sent = True
                print("✓ Slack: 전송 성공")
            else:
                print("✗ Slack: 전송 실패")
        else:
            print("- Slack: 미설정")

        if not sent:
            print("\n알림 채널이 설정되지 않았습니다.")
            print(".env 파일에 다음 환경변수를 설정하세요:")
            print("  TELEGRAM_BOT_TOKEN=your_token")
            print("  TELEGRAM_CHAT_ID=your_chat_id")
            print("  DISCORD_WEBHOOK_URL=your_webhook_url")
            print("  SLACK_WEBHOOK_URL=your_webhook_url")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='StockAI Notifier')
    parser.add_argument('--test', action='store_true', help='Send test message')
    parser.add_argument('--notify', action='store_true', help='Notify new picks')
    parser.add_argument('--report', action='store_true', help='Send daily report')
    args = parser.parse_args()

    notifier = StockNotifier()

    if args.test:
        notifier.send_test_message()
    elif args.notify:
        notifier.notify_new_picks()
    elif args.report:
        notifier.send_daily_report()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
