# database.py
import json
import os
import shutil
from config import DB_FILE, OWNER_ID, MAIN_GROUP_ID

DEFAULT_DATA = {
    "groups": [MAIN_GROUP_ID], # Default group pehle se added
    "schedule": {},    
    "users": {},       
    "auth_users": [], 
    "settings": {"time": "16:00"},
    "daily_stats": {"topper": "Pending..."}
}

def load_data():
    if not os.path.exists(DB_FILE):
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA
    try:
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
            # Integrity Checks (Data structure fix karne ke liye)
            if "schedule" not in data: data["schedule"] = {}
            if "users" not in data: data["users"] = {}
            if "auth_users" not in data: data["auth_users"] = []
            if "groups" not in data: data["groups"] = []
            if "daily_stats" not in data: data["daily_stats"] = {"topper": "Pending..."}
            
            # Auto-Add Main Group if missing
            if MAIN_GROUP_ID not in data["groups"]:
                data["groups"].append(MAIN_GROUP_ID)
                save_data(data) # Turant save karein
                
            return data
    except Exception as e:
        print(f"❌ Database Error: {e}")
        return DEFAULT_DATA

def save_data(data):
    # ATOMIC SAVE: Pehle temp file me likho, fir rename karo.
    # Isse file kabhi corrupt (0 bytes) nahi hogi.
    temp_file = f"{DB_FILE}.tmp"
    try:
        with open(temp_file, 'w') as f:
            json.dump(data, f, indent=4)
        shutil.move(temp_file, DB_FILE)
    except Exception as e:
        print(f"⚠️ Save Error: {e}")

def is_admin(user_id):
    data = load_data()
    return user_id == OWNER_ID or user_id in data.get("auth_users", [])

def update_time(new_time):
    data = load_data()
    data["settings"]["time"] = new_time
    save_data(data)

def add_test_to_schedule(date_str, topic, link):
    data = load_data()
    data["schedule"][date_str] = {"day": topic, "link": link}
    save_data(data)

def get_test_by_date(date_str):
    data = load_data()
    return data["schedule"].get(date_str, None)

def set_daily_topper(name):
    data = load_data()
    data["daily_stats"]["topper"] = name
    save_data(data)

def reset_bot_data():
    # Reset karte waqt bhi main group ko mat hatana
    reset_d = DEFAULT_DATA.copy()
    save_data(reset_d)
