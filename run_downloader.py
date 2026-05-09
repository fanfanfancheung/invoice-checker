#!/usr/bin/env python3
"""CLI entry point for the Feishu email invoice downloader.

One-shot usage:
    python run_downloader.py
    python run_downloader.py --output ~/发票存档

Scheduled daemon (every day at 12:00):
    python run_downloader.py --schedule
    python run_downloader.py --schedule --time 09:30
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
        "--schedule", "-s",
        action="store_true",
        help="以定时守护进程模式运行，每天自动执行一次",
    )
    parser.add_argument(
        "--time", "-t",
        default="12:00",
        help="定时执行时间，格式 HH:MM（默认: 12:00，仅 --schedule 模式有效）",
    )
    args = parser.parse_args()

    try:
        if args.schedule:
            _run_scheduled(args.output, args.time)
        else:
            from email_downloader.downloader import run
            run(output_dir=args.output)
    except KeyboardInterrupt:
        print("\n已停止。")
    except RuntimeError as e:
        print(f"[错误] {e}")
        sys.exit(1)


def _run_scheduled(output_dir: str | None, run_time: str) -> None:
    import schedule
    import time
    from email_downloader.downloader import run

    def job():
        try:
            run(output_dir=output_dir)
        except Exception as e:
            print(f"[错误] 本次执行失败: {e}")

    # Run once immediately on startup, then on schedule
    print(f"定时模式启动，每天 {run_time} 执行一次。首次立即运行…\n")
    job()

    schedule.every().day.at(run_time).do(job)

    print(f"\n等待下次执行（每天 {run_time}）。按 Ctrl+C 停止。")
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
