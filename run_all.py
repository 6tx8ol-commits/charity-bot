import os, sys, subprocess, threading, time

# على Replit لا نشغل البوتات — تعمل على Render
if os.environ.get('REPL_ID') or os.environ.get('REPLIT_CLUSTER') or os.environ.get('REPLIT_DB_URL'):
    print("⚠️ Replit بيئة — البوتان يعملان على Render.")
    sys.exit(0)

print("🚀 تشغيل البوتين على Render...")

def run_bot(path, name):
    while True:
        print(f"▶️ تشغيل {name}...")
        try:
            proc = subprocess.Popen([sys.executable, "main.py"], cwd=path)
            proc.wait()
            code = proc.returncode
        except Exception as e:
            code = -1
            print(f"❌ خطأ في تشغيل {name}: {e}")
        print(f"⛔ {name} توقف (exit {code}) — إعادة تشغيل خلال 5 ثوان...")
        time.sleep(5)

t1 = threading.Thread(target=run_bot, args=("athar-bot",   "بوت أثر"),     daemon=True)
t2 = threading.Thread(target=run_bot, args=("telegram-bot", "بوت الأذكار"), daemon=True)

t1.start()
t2.start()

t1.join()
t2.join()
