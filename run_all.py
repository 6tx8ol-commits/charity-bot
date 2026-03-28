import subprocess
import sys
import os
import signal
import time
import logging

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("run_all")

BOTS = [
    {"name": "اثر",   "cwd": "athar-bot",    "script": "main.py"},
    {"name": "اذكار", "cwd": "telegram-bot",  "script": "main.py"},
]

processes = []


def start_bot(bot: dict) -> subprocess.Popen:
    logger.info(f"🚀 تشغيل بوت [{bot['name']}]...")
    p = subprocess.Popen(
        [sys.executable, "-u", bot["script"]],
        cwd=bot["cwd"],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    return p


def cleanup(sig=None, frame=None):
    logger.info("⛔ إيقاف البوتين...")
    for p in processes:
        try:
            p.terminate()
        except Exception:
            pass
    time.sleep(2)
    for p in processes:
        try:
            p.kill()
        except Exception:
            pass
    sys.exit(0)


signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)


def main():
    global processes
    processes = [start_bot(b) for b in BOTS]

    logger.info("✅ البوتين يعملان الآن")

    while True:
        time.sleep(10)
        for i, (bot, proc) in enumerate(zip(BOTS, processes)):
            ret = proc.poll()
            if ret is not None:
                logger.warning(f"⚠️ بوت [{bot['name']}] وقف (exit={ret})، جاري إعادة التشغيل...")
                time.sleep(3)
                processes[i] = start_bot(bot)


if __name__ == "__main__":
    main()
