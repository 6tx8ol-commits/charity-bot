import os, sys, subprocess, threading

# على Replit لا نشغل البوتات — تعمل على Render
if os.environ.get('REPL_ID') or os.environ.get('REPLIT_CLUSTER') or os.environ.get('REPLIT_DB_URL'):
    print("⚠️ Replit بيئة — البوتان يعملان على Render.")
    sys.exit(0)

print("🚀 تشغيل البوتين على Render...")

def run_bot(path, name):
    print(f"▶️ تشغيل {name}...")
    proc = subprocess.Popen([sys.executable, "main.py"], cwd=path)
    proc.wait()
    print(f"⛔ {name} توقف (exit code {proc.returncode})")

t1 = threading.Thread(target=run_bot, args=("athar-bot", "بوت أثر"), daemon=True)
t2 = threading.Thread(target=run_bot, args=("telegram-bot", "بوت الأذكار"), daemon=True)

t1.start()
t2.start()

t1.join()
t2.join()
