# jobs.py
import asyncio
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import load_data, save_data, get_test_by_date
from config import OWNER_ID, MAIN_GROUP_ID
from datetime import datetime, date

EXAM_DATE = date(2026, 2, 12)

MORNING_QUOTES = [
    "Utho, Jaago aur tab tak mat ruko jab tak lakshya na mil jaye!",
    "Aaj ka dard kal ki taqat banega.",
    "Board Exam pass hai, ab time waste mat karo.",
    "Consistency is the key to Success."
]

# --- 1. MORNING MOTIVATION ---
async def job_morning_motivation(context):
    db = load_data()
    quote = random.choice(MORNING_QUOTES)
    days_left = (EXAM_DATE - datetime.now().date()).days
    
    msg = (
        "🌅 **GOOD MORNING BW STUDENTS!** 🌅\n\n"
        f"⏳ **Board Exam Countdown:** {days_left} Days Left\n"
        "➖➖➖➖➖➖➖➖➖➖\n"
        f"💡 _'{quote}'_\n\n"
        "👉 **Reminder:** Aaj shaam 4 baje Test hai. Taiyar rehna!"
    )
    # Sabhi groups me bhejo (Incld. Main Group)
    for gid in db["groups"]:
        try: await context.bot.send_message(chat_id=gid, text=msg);
        except: pass

# --- TEST LOGIC ---
async def execute_test_logic(context, chat_id, test_data):
    # STEP 1: ATTENDANCE
    try:
        btn = [[InlineKeyboardButton("🙋‍♂️ PRESENT SIR", callback_data='attendance_done')]]
        att_msg = (
            "🔔 **ATTENDANCE CALL (BW)** 🔔\n\n"
            f"📅 **Date:** {datetime.now().strftime('%d-%m-%Y')}\n"
            f"📌 **Subject:** {test_data['day']}\n\n"
            "⏳ Test starts in **2 Minutes**.\n"
            "👇 **Button dabakar Haaziri Lagayein:**"
        )
        await context.bot.send_message(chat_id=chat_id, text=att_msg, reply_markup=InlineKeyboardMarkup(btn))
    except Exception as e:
        print(f"Error sending attendance to {chat_id}: {e}")
        return # Agar attendance msg hi nahi gaya to aage mat badho

    await asyncio.sleep(60)

    # STEP 2: PIN ALERT
    try:
        m = await context.bot.send_message(chat_id=chat_id, text="🚨 **ALERT:** \n 1 Minute Left!")
        try: await context.bot.pin_chat_message(chat_id=chat_id, message_id=m.message_id)
        except: pass
    except: pass

    await asyncio.sleep(60)

    # STEP 3: LINK
    try:
        t = (
            "🚀 **TEST STARTED** 🚀\n\n"
            f"📌 **Subject:** {test_data['day']}\n"
            f"👇 **Click Link below:**\n\n"
            f"{test_data['link']}\n\n"
            "_(Test dekar wapas aana)_"
        )
        await context.bot.send_message(chat_id=chat_id, text=t)
    except: pass

# --- 2. SCHEDULER JOB ---
async def job_send_test(context):
    db = load_data()
    today_str = datetime.now().strftime("%d-%m-%Y")
    test_data = get_test_by_date(today_str)
    
    if not test_data:
        return

    # Create task for each group so they run simultaneously (Fast)
    for gid in db["groups"]:
        context.application.create_task(execute_test_logic(context, gid, test_data))
    
    await context.bot.send_message(OWNER_ID, f"✅ Test Launched for {today_str}")

# --- 3. NIGHT REPORT ---
async def job_nightly_report(context):
    db = load_data()
    today_str = datetime.now().strftime("%d-%m-%Y")
    test_data = get_test_by_date(today_str)
    
    if not test_data: return

    today = str(datetime.now().date())
    absent = []
    topper = db.get("daily_stats", {}).get("topper", "Pending...")
    
    # Check absentees
    for uid, info in db["users"].items():
        if int(uid) == OWNER_ID or int(uid) in db["auth_users"]: continue
        
        if info["last_date"] != today:
            info["strikes"] += 1
            absent.append(f"{info['name']} ({info['strikes']})")
    
    save_data(db) # Save strikes

    report = f"🌙 **REPORT ({today_str})** 🌙\n\n🏆 **TOPPER:** {topper} 🎉\n\n"
    if absent: 
        report += "❌ **ABSENT (Names):**\n" + ", ".join(absent[:50]) # Max 50 names to avoid spam
        if len(absent) > 50: report += f"\n...and {len(absent)-50} more."
    else: 
        report += "✅ **Sab Present the!**"

    for gid in db["groups"]:
        try: await context.bot.send_message(gid, report);
        except: pass
