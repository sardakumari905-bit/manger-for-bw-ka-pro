import asyncio
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import load_data, save_data, get_test_by_date
from config import OWNER_ID
from datetime import datetime, date

# --- EXAM DATE (Change this if needed) ---
EXAM_DATE = date(2026, 2, 12)

MORNING_QUOTES = [
    "Utho, Jaago aur tab tak mat ruko jab tak lakshya na mil jaye!",
    "Aaj ka dard kal ki taqat banega.",
    "Sapne wo nahi jo neend me aate hain, sapne wo hain jo neend uda dete hain.",
    "Board Exam pass hai, ab time waste mat karo.",
    "Consistency is the key to Success."
]

# --- 1. MORNING MOTIVATION (5:00 AM) ---
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
    for gid in db["groups"]:
        try: await context.bot.send_message(chat_id=gid, text=msg);
        except: pass

# --- TEST LOGIC (4:00 PM) ---
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
    except: pass

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
        # Aaj test nahi hai
        return

    for gid in db["groups"]:
        asyncio.create_task(execute_test_logic(context, gid, test_data))
    
    await context.bot.send_message(OWNER_ID, f"✅ Test Launched for {today_str}: {test_data['day']}")

# --- 3. NIGHT REPORT (9:30 PM) ---
async def job_nightly_report(context):
    db = load_data()
    today_str = datetime.now().strftime("%d-%m-%Y")
    test_data = get_test_by_date(today_str)
    
    if not test_data: return

    today = str(datetime.now().date())
    absent, kicked = [], []
    topper = db.get("daily_stats", {}).get("topper", "Pending...")
    
    for uid, info in db["users"].items():
        if int(uid) == OWNER_ID or int(uid) in db["auth_users"]: continue
        
        if info["last_date"] != today:
            info["strikes"] += 1
            absent.append(f"{info['name']} ({info['strikes']})")
            if info["strikes"] >= 3:
                kicked.append(info['name'])
                info["strikes"] = 0
                for gid in db["groups"]:
                    try: 
                        await context.bot.ban_chat_member(gid, int(uid))
                        await context.bot.unban_chat_member(gid, int(uid))
                    except: pass
    
    save_data(db)
    report = f"🌙 **REPORT ({today_str})** 🌙\n\n🏆 **TOPPER:** {topper} 🎉\n\n"
    if absent: report += "❌ **ABSENT:**\n" + ", ".join(absent) + "\n\n"
    if kicked: report += "🚫 **BANNED:**\n" + ", ".join(kicked)
    else: report += "✅ **Sab Present the!**"

    for gid in db["groups"]:
        try: await context.bot.send_message(gid, report);
        except: pass
