# database.py
import json
import os
import shutil
from config import DB_FILE, OWNER_ID, MAIN_GROUP_ID

DEFAULT_DATA = {
    "groups": [MAIN_GROUP_ID],
    "schedule": {}, 
    "users": {},        
    "auth_users": [], 
    "daily_stats": {"topper": "Pending..."}
}

def load_data():
    if not os.path.exists(DB_FILE):
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA
    try:
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
            # Ensure basic structure exists
            if "groups" not in data: data["groups"] = [MAIN_GROUP_ID]
            if "schedule" not in data: data["schedule"] = {}
            if "auth_users" not in data: data["auth_users"] = []
            return data
    except:
        return DEFAULT_DATA

def save_data(data):
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

def add_test_to_schedule(date_str, topic, link, time_str):
    data = load_data()
    if date_str not in data["schedule"]:
        data["schedule"][date_str] = []
    
    new_test = {"day": topic, "link": link, "time": time_str, "sent": False}
    data["schedule"][date_str].append(new_test)
    save_data(data)

def get_tests_by_date(date_str):
    data = load_data()
    return data["schedule"].get(date_str, [])

def mark_test_sent(date_str, index):
    data = load_data()
    if date_str in data["schedule"] and len(data["schedule"][date_str]) > index:
        data["schedule"][date_str][index]["sent"] = True
        save_data(data)

def set_daily_topper(name):
    data = load_data()
    data["daily_stats"]["topper"] = name
    save_data(data)

def reset_bot_data():
    save_data(DEFAULT_DATA)
