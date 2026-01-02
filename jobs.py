import asyncio
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import IST, EXAM_DATE, OWNER_ID
from database import load_data, save_data, get_tests_by_date, mark_test_sent

# --- CORE TEST LOGIC (Called by Auto Schedule & Manual Buttons) ---
async def execute_test_logic(context, chat_id, test_data):
    # 1. Attendance
    try:
        btn = [[InlineKeyboardButton("🙋‍♂️ PRESENT SIR", callback_data='attendance_done')]]
        await context.bot.send_message(
            chat_id, 
            f"🔔 **ATTENDANCE: {test_data['day']}**\n⏳ Test starts in 2 mins!", 
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except: return # Agar bot group me nahi hai to error ignore kare

    await asyncio.sleep(60) # 1 Min Wait
    
    # 2. Alert
    try: await context.bot.send_message(chat_id, "🚨 **1 Minute Left!**")
    except: pass
    
    await asyncio.sleep(60) # 1 Min Wait

    # 3. Link
    try:
        await context.bot.send_message(
            chat_id, 
            f"🚀 **STARTED: {test_data['day']}**\n\n👇 **LINK:**\n{test_data['link']}\n\n_(All the best)_"
        )
    except: pass

# --- SCHEDULED JOBS ---
async def job_check_schedule(context):
    now = datetime.now(IST)
    today_str = now.strftime("%d-%m-%Y")
    current_time = now.strftime("%H:%M") 

    tests = get_tests_by_date(today_str)
    if not tests: return

    for index, test in enumerate(tests):
        if test['time'] == current_time and not test.get('sent'):
            mark_test_sent(today_str, index)
            db = load_data()
            
            # Fire logic for all groups
            for gid in db["groups"]:
                context.application.create_task(execute_test_logic(context, gid, test))
            
            try: await context.bot.send_message(OWNER_ID, f"✅ Auto-Launched: {test['day']}")
            except: pass

async def job_morning_motivation(context):
    db = load_data()
    today = datetime.now(IST).date()
    days_left = (EXAM_DATE - today).days
    msg = f"🌅 **GOOD MORNING!**\n⏳ **{days_left} Days Left** for Boards."
    for gid in db["groups"]:
        try: await context.bot.send_message(gid, msg)
        except: pass

async def job_nightly_report(context):
    db = load_data()
    today = str(datetime.now(IST).date())
    absent_list = []
    
    for uid, info in db["users"].items():
        if int(uid) == OWNER_ID or int(uid) in db["auth_users"]: continue
        if info.get("last_date") != today:
            info["strikes"] = info.get("strikes", 0) + 1
            absent_list.append(info['name'])
    save_data(db)

    report = f"🌙 **NIGHT REPORT**\n❌ Absent: {len(absent_list)}"
    for gid in db["groups"]:
        try: await context.bot.send_message(gid, report)
        except: pass
