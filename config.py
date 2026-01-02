import pytz
from datetime import date

# --- SETTINGS ---
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Apna Token Dalein
OWNER_ID = 1234567890              # Apni Admin ID Dalein
MAIN_GROUP_ID = -100123456789      # Group ID

DB_FILE = "rbse_final_db.json"
START_IMG = "https://i.postimg.cc/rmDPsqRC/Gemini-Generated-Image-5jbjnc5jbjnc5jbj.png"

# Global Constants
IST = pytz.timezone('Asia/Kolkata')
EXAM_DATE = date(2026, 2, 12)

# Conversation States (Yahan declare kiye taaki sab use kar sakein)
ASK_DATE, ASK_TOPIC, ASK_LINK, ASK_TIME_SLOT = range(4)
ASK_BROADCAST_MSG = 4
ASK_ADMIN_ID = 5
ASK_TOPPER_NAME = 6
