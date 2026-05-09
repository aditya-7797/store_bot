#!/usr/bin/env python
"""
Backend startup script - ensures correct working directory and starts uvicorn.
Run this from anywhere: python run_backend.py
"""
import os
import sys
import subprocess

# Get the project root (parent of backend/)
project_root = os.path.dirname(os.path.abspath(__file__))

# Change to project root
os.chdir(project_root)
print(f"Working directory: {os.getcwd()}")

# Add to path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Start uvicorn with reload
import uvicorn

print("Starting FastAPI backend on http://0.0.0.0:8000")
print("Reload enabled - server will restart on code changes\n")

uvicorn.run(
    "backend.main:app",
    host="0.0.0.0",
    port=8000,
    reload=True,
    reload_dirs=["backend", "agents", "graph", "tools"]
)
