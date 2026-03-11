"""
Simple script to start the Streamlit frontend
"""
import os
import subprocess
import sys

if __name__ == "__main__":
    print("🎨 Starting SmartRetail AI Dashboard...")
    print("📍 Dashboard will be available at: http://localhost:8501")
    print("\n" + "="*60 + "\n")
    
    subprocess.run([
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "frontend/dashboard.py"
    ])
