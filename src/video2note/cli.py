# src/video2note/cli.py

import argparse
import sys

from video2note.config_manager.loader import load_config
from video2note.core.runner import Runner
from video2note.utils.logger import setup_logging


def main():
    parser = argparse.ArgumentParser(prog="video2note")
    parser.add_argument("--config", "-c", type=str, help="path to config yaml", default=None)
    parser.add_argument("--mode", type=str,
                        choices=["full", "download-only", "transcribe-only", "summarize-only", "sync-only"],
                        default="full")
    args = parser.parse_args()

    config = load_config(args.config)
    setup_logging(config.app.log_level)

    runner = Runner(config)
    try:
        if args.mode == "download-only":
            runner.run_download_only()
        elif args.mode == "transcribe-only":
            runner.run_transcribe_only()
        elif args.mode == "summarize-only":
            runner.run_summarize_only()
        elif args.mode == "sync-only":
            runner.run_sync_only()
        else:
            runner.run_full()
    except Exception as e:
        # 你可以引入 traceback / logger 打印更详细错误
        print(f"[Error] {e}", file=sys.stderr)
        sys.exit(1)
