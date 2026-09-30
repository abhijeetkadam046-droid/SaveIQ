import sys
import io
import uvicorn

# Ensure UTF-8 output encoding on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

if __name__ == "__main__":
    print("=" * 60)
    print(" >>> Launching SaveIQ - AI Savings Goal Tracker <<< ")
    print(" Web Dashboard: http://127.0.0.1:8000")
    print(" Interactive API Docs: http://127.0.0.1:8000/docs")
    print("=" * 60)
    
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False
    )
