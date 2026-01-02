# jobs.py
import asyncio
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import IST, EXAM_DATE, OWNER_ID
from database import load_data, save_data, get_tests_by_date, mark_test_sent, get_todays_toppers

# --- TEST EXECUTION LOGIC ---
async def execute_test_logic(context, chat_id, test_data):
    # 1. Attendance Button
    try:
        btn = [[InlineKeyboardButton("🙋‍♂️ PRESENT SIR", callback_data='attendance_done')]]
        await context.bot.send_message(
            chat_id, 
            f"🔔 **ATTENDANCE: {test_data['day']}**\n⏳ Test starts in 2 mins!\nAttendance mark karo jaldi!", 
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except: return

    await asyncio.sleep(60) # 1 Min Wait
    try: await context.bot.send_message(chat_id, "🚨 **1 Minute Left!**\nGet Ready.")
    except: pass
    
    await asyncio.sleep(60) # 1 Min Wait

    # 3. Send Link
    try:
        await context.bot.send_message(
            chat_id, 
            f"🚀 **TEST STARTED: {test_data['day']}**\n\n👇 **LINK:**\n{test_data['link']}\n\n_(Best of luck)_"
        )
    except: pass

# --- AUTO SCHEDULE CHECKER ---
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

# --- NIGHT REPORT (PRO VERSION) ---
async def job_nightly_report(context):
    db = load_data()
    now = datetime.now(IST)
    today_str = now.strftime("%d-%m-%Y")
    
    # 1. Get Toppers List
    toppers_dict = get_todays_toppers(today_str)
    topper_text = ""
    if toppers_dict:
        for subj, name in toppers_dict.items():
            topper_text += f"• **{subj}:** {name}\n"
    else:
        topper_text = "• _Result Pending..._\n"

    # 2. Calculate Absentees & Strikes
    absent_list = []
    kicked_list = []
    
    for uid, info in db["users"].items():
        if int(uid) == OWNER_ID or int(uid) in db["auth_users"]: continue
        
        # Check Attendance
        if info.get("last_date") != today_str:
            # Absent Logic
            info["strikes"] = info.get("strikes", 0) + 1
            absent_list.append(f"{info['name']} (Stk: {info['strikes']})")
            
            # Kick Logic (3 Strikes)
            if info["strikes"] >= 3:
                kicked_list.append(info['name'])
                info["strikes"] = 0 # Reset after kick
                for gid in db["groups"]:
                    try: 
                        await context.bot.ban_chat_member(gid, int(uid))
                        await context.bot.unban_chat_member(gid, int(uid))
                    except: pass
    
    save_data(db)

    # 3. Create Final Message
    report = (
        f"🌙 **NIGHT REPORT ({today_str})**\n\n"
        f"🏆 **AAJ KE TOPPERS:**\n{topper_text}\n"
        f"❌ **ABSENT STUDENTS (+1 Strike):**\n"
        f"{', '.join(absent_list) if absent_list else 'None (Sab Present the!)'}\n\n"
    )
    
    if kicked_list:
        report += f"🚫 **KICKED (3 Strikes):**\n{', '.join(kicked_list)}"

    # Send to all groups
    for gid in db["groups"]:
        try: await context.bot.send_message(gid, report)
        except: pass

# --- MORNING MOTIVATION ---
async def job_morning_motivation(context):
    db = load_data()
    today = datetime.now(IST).date()
    days_left = (EXAM_DATE - today).days
    msg = f"🌅 **GOOD MORNING!**\n⏳ **{days_left} Days Left** for Boards.\nUtho aur Padhai shuru karo!"
    for gid in db["groups"]:
        try: await context.bot.send_message(gid, msg)
        except: pass
