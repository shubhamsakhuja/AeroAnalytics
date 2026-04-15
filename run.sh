#!/bin/bash
# Mac / Linux launcher
cd "$(dirname "$0")"
source venv/bin/activate 2>/dev/null || true
streamlit run app/main.py
