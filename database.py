# database.py
import json
import os
import shutil
from config import DB_FILE, MAIN_GROUP_ID, OWNER_ID

DEFAULT_DATA = {
    "groups": [MAIN_GROUP_ID],
    "schedule": {}, 
    "users": {},        
    "auth_users": [], 
    "toppers": {} # Format: {"DATE": {"Chemistry": "Name", "Hindi": "Name"}}
}

def load_data():
    if not os.path.exists(DB_FILE): save_data(DEFAULT_DATA); return DEFAULT_DATA
    try:
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
            # Ensure keys exist
            if "toppers" not in data: data["toppers"] = {}
            if "groups" not in data: data["groups"] = [MAIN_GROUP_ID]
            return data
    except: return DEFAULT_DATA

def save_data(data):
    temp_file = f"{DB_FILE}.tmp"
    try:
        with open(temp_file, 'w') as f: json.dump(data, f, indent=4)
        shutil.move(temp_file, DB_FILE)
    except: pass

def is_admin(user_id):
    data = load_data()
    return user_id == OWNER_ID or user_id in data.get("auth_users", [])

# --- SCHEDULE & TOPPER FUNCTIONS ---
def add_test_to_schedule(date_str, topic, link, time_str):
    data = load_data()
    if date_str not in data["schedule"]: data["schedule"][date_str] = []
    data["schedule"][date_str].append({"day": topic, "link": link, "time": time_str, "sent": False})
    save_data(data)

def get_tests_by_date(date_str):
    return load_data()["schedule"].get(date_str, [])

def mark_test_sent(date_str, index):
    data = load_data()
    if date_str in data["schedule"]:
        data["schedule"][date_str][index]["sent"] = True
        save_data(data)

def set_subject_topper(date_str, subject, name):
    data = load_data()
    if date_str not in data["toppers"]: data["toppers"][date_str] = {}
    data["toppers"][date_str][subject] = name
    save_data(data)

def get_todays_toppers(date_str):
    return load_data()["toppers"].get(date_str, {})
