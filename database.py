import json
import os
from config import DB_FILE, OWNER_ID

# आपकी Group ID यहाँ डिफ़ॉल्ट में डाल दी है
DEFAULT_DATA = {
    "groups": [-1002308402459], 
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
            # यह पक्का करता है कि आपकी ID हमेशा लिस्ट में रहे
            if "groups" not in data: 
                data["groups"] = [-1002308402459]
            elif -1002308402459 not in data["groups"]:
                data["groups"].append(-1002308402459)
            return data
    except:
        return DEFAULT_DATA

def save_data(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

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
    save_data(DEFAULT_DATA)
