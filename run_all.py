import os, sys, subprocess, threading, time, signal

if os.environ.get('REPL_ID') or os.environ.get('REPLIT_CLUSTER') or os.environ.get('REPLIT_DB_URL'):
    print("⚠️ Replit بيئة — البوتان يعملان على Render.")
    sys.exit(0)

print("🚀 تشغيل البوتات الثلاثة على Render...")

_procs = []
_lock  = threading.Lock()
_stop  = threading.Event()

def cleanup(sig=None, frame=None):
    print("🛑 إيقاف البوتين...")
    _stop.set()
    with _lock:
        for p in _procs:
            try:
                p.terminate()
            except Exception:
                pass
    time.sleep(3)
    with _lock:
        for p in _procs:
            try:
                p.kill()
            except Exception:
                pass
    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT,  cleanup)

def run_bot(path, name, startup_delay=0):
    if startup_delay:
        print(f"⏳ انتظار {startup_delay}ث قبل تشغيل {name}...")
        time.sleep(startup_delay)
    while not _stop.is_set():
        print(f"▶️ تشغيل {name}...")
        try:
            proc = subprocess.Popen([sys.executable, "main.py"], cwd=path)
            with _lock:
                _procs.append(proc)
            proc.wait()
            with _lock:
                if proc in _procs:
                    _procs.remove(proc)
            code = proc.returncode
        except Exception as e:
            code = -1
            print(f"❌ خطأ في {name}: {e}")
        if _stop.is_set():
            break
        print(f"⛔ {name} توقف (exit {code}) — إعادة تشغيل خلال 35 ثانية...")
        time.sleep(35)

t1 = threading.Thread(target=run_bot, args=("athar-bot",    "بوت أثر",     0),  daemon=True)
t2 = threading.Thread(target=run_bot, args=("telegram-bot", "بوت الأذكار", 5),  daemon=True)
t3 = threading.Thread(target=run_bot, args=("khayyal-bot",  "بوت خَيال",  10),  daemon=True)

t1.start()
t2.start()
t3.start()

t1.join()
t2.join()
t3.join()
