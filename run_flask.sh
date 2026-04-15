#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate 2>/dev/null || true
echo ""
echo " Starting AeroAnalytics..."
echo " Opening http://localhost:5000"
echo ""
python flask_app/server.py
