#!/usr/bin/env python3
"""CLI entry point for the Feishu email invoice downloader.

Usage:
    python run_downloader.py
    python run_downloader.py --output ~/发票存档 --days 7
"""
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="从飞书邮箱下载发票附件")
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="发票保存目录（默认: ./downloads）",
    )
    parser.add_argument(
        "--days", "-d",
        type=int,
        default=None,
        help="搜索最近 N 天的邮件（默认: 30，0 = 全部）",
    )
    args = parser.parse_args()

    try:
        from email_downloader.downloader import run
        run(output_dir=args.output, days_back=args.days)
    except KeyError as e:
        print(f"[错误] 缺少环境变量 {e}，请先复制 .env.example 为 .env 并填写配置。")
        sys.exit(1)
    except RuntimeError as e:
        print(f"[错误] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
