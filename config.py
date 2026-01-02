# config.py
import pytz
from datetime import date

# --- ADMIN SETTINGS ---
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  
OWNER_ID = 1234567890              
MAIN_GROUP_ID = -100123456789      

DB_FILE = "board_pro_db.json"
START_IMG = "https://i.postimg.cc/rmDPsqRC/Gemini-Generated-Image-5jbjnc5jbjnc5jbj.png"

# --- CONSTANTS ---
IST = pytz.timezone('Asia/Kolkata')
EXAM_DATE = date(2026, 2, 12) # Board Exam Date

# --- STATES ---
# Schedule Flow
ASK_DATE, ASK_TOPIC, ASK_LINK, ASK_TIME_SLOT = range(4)
# Broadcast Flow
ASK_BROADCAST_MSG = 4
# Admin Flow
ASK_ADMIN_ID = 5
# Topper Flow (New)
ASK_TOPPER_SUBJECT, ASK_TOPPER_NAME = 6, 7
