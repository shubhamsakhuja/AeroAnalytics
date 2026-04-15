# AeroAnalytics — Deployment Guide
# ==================================
# Deploy to AWS EC2 (Ubuntu, Gunicorn, systemd)
# Estimated time: 45 minutes | Free for 12 months (t2.micro)

# ═══════════════════════════════════════════════════════════════
# PHASE 1 — PUSH CODE TO GITHUB (10 minutes)
# ═══════════════════════════════════════════════════════════════

# 1A. Create a GitHub account at github.com (free)

# 1B. Create a new repository
#     github.com → New repository
#     Name: aeroanalytics
#     Visibility: Public
#     Do NOT add README (you already have one)
#     Click: Create repository

# 1C. Push your project from your Windows machine
#     Open PowerShell in your ai_data_analyst folder:

git init
git add .
git commit -m "Initial commit — AeroAnalytics v1.0"
git branch -M main
git remote add origin https://github.com/shubhamsakhuja/aeroanalytics.git
git push -u origin main

#     ✅ Code is now on GitHub
#     Portfolio link: github.com/shubhamsakhuja/aeroanalytics


# ═══════════════════════════════════════════════════════════════
# PHASE 2 — AWS ACCOUNT SETUP (5 minutes)
# ═══════════════════════════════════════════════════════════════

# 2A. Create AWS account at aws.amazon.com
#     Add a credit card (required, won't charge within free tier)

# 2B. Enable Claude Haiku on AWS Bedrock
#     AWS Console → Search "Bedrock" → Open
#     Left menu → Model access → Manage model access
#     Find "Claude Haiku 4.5" → tick it → Save changes
#     Wait 1–2 minutes (auto-approved)

# 2C. Make sure region is ap-southeast-2 (Sydney)
#     Check top-right corner of AWS Console
#     Change if needed — all steps below use ap-southeast-2


# ═══════════════════════════════════════════════════════════════
# PHASE 3 — LAUNCH EC2 INSTANCE (10 minutes)
# ═══════════════════════════════════════════════════════════════

# 3A. Go to EC2
#     AWS Console → Search "EC2" → Launch instance

# 3B. Configure the instance
#     Name:              aeroanalytics-server
#     OS:                Ubuntu Server 22.04 LTS (Free tier eligible)
#     Instance type:     t2.micro (Free tier eligible)
#     Key pair:          Create new → Name: aeroanalytics-key → RSA → .pem
#                        ⚠️  Save the .pem file — you cannot download it again
#                        Recommended save path: D:\AWS Keys\aeroanalytics-key.pem

# 3C. Network settings → Edit
#     Allow SSH from: Anywhere (0.0.0.0/0)
#     ✅ Allow HTTP traffic from the internet
#     Add rule → Custom TCP → Port 5000 → Source: 0.0.0.0/0

# 3D. Storage: keep default (8 GB)

# 3E. Click Launch instance
#     Wait ~2 minutes until status shows ✅ Running


# ═══════════════════════════════════════════════════════════════
# PHASE 4 — CREATE IAM ROLE FOR BEDROCK (5 minutes)
# ═══════════════════════════════════════════════════════════════
# This lets EC2 call Bedrock without storing AWS keys in your code

# 4A. AWS Console → Search "IAM" → Roles → Create role
#     Trusted entity: AWS service
#     Use case: EC2
#     Click Next

# 4B. Add permissions
#     Search: AmazonBedrockFullAccess → tick it
#     Click Next

# 4C. Name the role
#     Role name: aeroanalytics-bedrock-role
#     Click Create role

# 4D. Attach role to your EC2 instance
#     EC2 → Instances → click aeroanalytics-server
#     Actions → Security → Modify IAM role
#     Select: aeroanalytics-bedrock-role
#     Click Update IAM role

#     ✅ Server can now call Bedrock — no AWS keys needed in .env


# ═══════════════════════════════════════════════════════════════
# PHASE 5 — GET A PERMANENT IP ADDRESS (3 minutes)
# ═══════════════════════════════════════════════════════════════

# 5A. EC2 → Elastic IPs (left sidebar) → Allocate Elastic IP address
#     Keep defaults → Allocate

# 5B. Tick the new IP → Actions → Associate Elastic IP address
#     Instance: select aeroanalytics-server
#     Click Associate

#     ✅ Your server now has a permanent IP that never changes
#     Note it down: YOUR_ELASTIC_IP


# ═══════════════════════════════════════════════════════════════
# PHASE 6 — CONNECT AND SET UP SERVER (15 minutes)
# ═══════════════════════════════════════════════════════════════

# 6A. Fix key file permissions (Windows PowerShell)
icacls "D:\AWS Keys\aeroanalytics-key.pem" /inheritance:r /grant:r "$($env:USERNAME):(R)"

# 6B. SSH into your server (replace with your actual Elastic IP)
ssh -i "D:\AWS Keys\aeroanalytics-key.pem" ubuntu@YOUR_ELASTIC_IP
#     Type "yes" when asked about fingerprint
#     You are now inside the server ✅

# 6C. Update the server
sudo apt update && sudo apt upgrade -y

# 6D. Install Python and Git
sudo apt install python3-pip python3-venv git -y

# 6E. Clone your code
git clone https://github.com/shubhamsakhuja/aeroanalytics.git
cd aeroanalytics

# 6F. Create virtual environment and install packages
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# 6G. Generate the airline database
python3 airline_db_generator.py
#     Should say: DB size: ~4.3 MB

# 6H. Create .env file on the server
nano .env
#     Paste this (no AWS keys needed — IAM role handles auth):

LLM_PROVIDER=bedrock
AWS_DEFAULT_REGION=ap-southeast-2
BEDROCK_MODEL_ID=au.anthropic.claude-haiku-4-5-20251001-v1:0
APP_ENV=prod
APP_USERNAME=admin
APP_PASSWORD=aero2025

#     Press Ctrl+X → Y → Enter to save


# ═══════════════════════════════════════════════════════════════
# PHASE 7 — RUN AS A SERVICE (always-on, auto-restart)
# ═══════════════════════════════════════════════════════════════

# 7A. Create systemd service file
sudo nano /etc/systemd/system/aeroanalytics.service

#     Paste this exactly:

[Unit]
Description=AeroAnalytics AI Data Analyst
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/aeroanalytics
Environment="PATH=/home/ubuntu/aeroanalytics/venv/bin"
ExecStart=/home/ubuntu/aeroanalytics/venv/bin/gunicorn flask_app.server:app --bind 0.0.0.0:5000 --workers 2 --timeout 120
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target

#     Ctrl+X → Y → Enter to save

# 7B. Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable aeroanalytics
sudo systemctl start aeroanalytics

# 7C. Verify it's running
sudo systemctl status aeroanalytics
#     Should show: Active: active (running) ✅


# ═══════════════════════════════════════════════════════════════
# PHASE 8 — TEST YOUR LIVE APP
# ═══════════════════════════════════════════════════════════════

# Open in your browser:
http://YOUR_ELASTIC_IP:5000

# Login with:
#   Username: admin
#   Password: aero2025

# ✅ AeroAnalytics is now live on the internet!


# ═══════════════════════════════════════════════════════════════
# UPDATING THE APP (after making code changes)
# ═══════════════════════════════════════════════════════════════

# On your local Windows machine — push changes:
git add .
git commit -m "Your update message"
git push

# On the EC2 server — pull and restart:
cd ~/aeroanalytics
git pull
sudo systemctl restart aeroanalytics

# Verify:
sudo systemctl status aeroanalytics


# ═══════════════════════════════════════════════════════════════
# EVERYDAY SERVER COMMANDS
# ═══════════════════════════════════════════════════════════════

# Check app status
sudo systemctl status aeroanalytics

# View live logs (useful for debugging)
sudo journalctl -u aeroanalytics -f

# Restart app
sudo systemctl restart aeroanalytics

# Stop app
sudo systemctl stop aeroanalytics

# Start app
sudo systemctl start aeroanalytics


# ═══════════════════════════════════════════════════════════════
# TROUBLESHOOTING
# ═══════════════════════════════════════════════════════════════

# App not loading in browser?
#   1. Check security group has port 5000 open (Phase 3C)
#   2. Check the service is running: sudo systemctl status aeroanalytics
#   3. Check logs: sudo journalctl -u aeroanalytics -n 50

# Bedrock authentication error?
#   Make sure the IAM role is attached to your EC2 instance (Phase 4D)
#   The role must have AmazonBedrockFullAccess policy

# LangGraph import error?
#   pip install langgraph langchain-core inside the venv
#   OR: pip install -r requirements.txt again

# Database not found?
#   Run: python3 airline_db_generator.py
#   Make sure you're in the /home/ubuntu/aeroanalytics directory

# Out of disk space?
#   df -h   (check disk usage)
#   sudo apt autoremove -y   (clean unused packages)

# Wrong model ID error?
#   Check your region prefix:
#   ap-southeast-2 (Sydney)  → BEDROCK_MODEL_ID=au.anthropic.claude-haiku-4-5-20251001-v1:0
#   us-east-1                → BEDROCK_MODEL_ID=us.anthropic.claude-haiku-4-5-20251001-v1:0
#   eu-west-1                → BEDROCK_MODEL_ID=eu.anthropic.claude-haiku-4-5-20251001-v1:0


# ═══════════════════════════════════════════════════════════════
# COST BREAKDOWN (AWS Free Tier)
# ═══════════════════════════════════════════════════════════════
#
# EC2 t2.micro:      FREE for 12 months (750 hrs/month)
# Elastic IP:        FREE while attached to running instance
# Bedrock (Haiku):   ~$0.25 per 1M input tokens — very cheap
#                    ~100 queries/day ≈ $1–3/month
# Data transfer:     ~$0.10/month
#
# TOTAL YEAR 1:      ~$1–3/month (Bedrock usage only)
# TOTAL YEAR 2+:     ~$8–10/month (EC2 + Bedrock)
#
# To save money:
#   Stop the EC2 instance when not demoing:
#   EC2 Console → Instance → Instance state → Stop
#   Elastic IP stays assigned, restart when needed


# ═══════════════════════════════════════════════════════════════
# WHAT TO SAY IN INTERVIEWS
# ═══════════════════════════════════════════════════════════════
#
# "AeroAnalytics is deployed end-to-end on AWS:
#  - Flask app runs on EC2 t2.micro (Ubuntu) in ap-southeast-2
#  - LangGraph orchestrates 4 AI agents, each calling Claude Haiku 4.5 on Bedrock
#  - IAM role attached to EC2 handles authentication — no hardcoded keys
#  - Gunicorn serves the app, systemd auto-restarts on crash
#  - Permanent Elastic IP for consistent access
#  - PROD mode requires username/password login
#  Full source code on GitHub, live demo available on request."
