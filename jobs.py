import asyncio
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import load_data, save_data, get_tests_by_date, mark_test_sent
from config import OWNER_ID
from datetime import datetime, date

EXAM_DATE = date(2026, 2, 12)

# --- MORNING MOTIVATION ---
async def job_morning_motivation(context):
    db = load_data()
    days = (EXAM_DATE - datetime.now().date()).days
    msg = f"🌅 **GOOD MORNING!**\n⏳ **{days} Days Left** for Boards.\nPadhai shuru karo!"
    for gid in db["groups"]:
        try: await context.bot.send_message(gid, msg)
        except: pass

# --- CORE TEST LOGIC ---
async def execute_test_logic(context, chat_id, test_data):
    # 1. Attendance
    try:
        btn = [[InlineKeyboardButton("🙋‍♂️ PRESENT SIR", callback_data='attendance_done')]]
        await context.bot.send_message(
            chat_id, 
            f"🔔 **ATTENDANCE: {test_data['day']}**\n⏳ Test starts in 2 mins!", 
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except: return

    await asyncio.sleep(60) # Wait 1 min
    
    # 2. Alert
    try: await context.bot.send_message(chat_id, "🚨 **1 Minute Left!**")
    except: pass
    
    await asyncio.sleep(60) # Wait 1 min

    # 3. Link
    try:
        await context.bot.send_message(
            chat_id, 
            f"🚀 **STARTED: {test_data['day']}**\n\n👇 **LINK:**\n{test_data['link']}\n\n_(All the best)_"
        )
    except: pass

# --- INTELLIGENT SCHEDULER (Runs every 60s) ---
async def job_check_schedule(context):
    now = datetime.now()
    today_str = now.strftime("%d-%m-%Y")
    current_time = now.strftime("%H:%M") # e.g., "16:00"

    tests = get_tests_by_date(today_str)
    
    if not tests: return

    # Check all tests for today
    for index, test in enumerate(tests):
        # Agar Time match hua aur abhi tak Send nahi hua
        if test['time'] == current_time and not test.get('sent'):
            
            # 1. Mark as sent immediately (to prevent double send)
            mark_test_sent(today_str, index)
            
            # 2. Fire execution
            db = load_data()
            for gid in db["groups"]:
                context.application.create_task(execute_test_logic(context, gid, test))
            
            await context.bot.send_message(OWNER_ID, f"✅ Auto-Launched: {test['day']} at {current_time}")

# --- NIGHT REPORT ---
async def job_nightly_report(context):
    db = load_data()
    today = str(datetime.now().date())
    absent = []
    
    for uid, info in db["users"].items():
        if int(uid) == OWNER_ID or int(uid) in db["auth_users"]: continue
        if info["last_date"] != today:
            info["strikes"] += 1
            absent.append(info['name'])
    save_data(db)

    report = f"🌙 **REPORT**\n❌ Absent: {len(absent)}"
    for gid in db["groups"]:
        try: await context.bot.send_message(gid, report)
        except: pass
