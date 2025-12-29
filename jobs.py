import asyncio
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import load_data, save_data, get_test_by_date
from config import OWNER_ID
from datetime import datetime, date

# --- EXAM DATE SETTING ---
EXAM_DATE = date(2026, 3, 1) # Board Exam Date

MORNING_QUOTES = [
    "Waqt kam hai, jitna dam hai laga do!",
    "Aaj ka mushkil sawal, kal ka aasaan jawab banega.",
    "Exam pass hai, sona kam aur padhna jyada shuru karo.",
    "Success ki chabi: Consistency + Hard Work.",
    "Bina thake, bina ruke, bas chalna hai."
]

# --- 1. MORNING MOTIVATION ---
async def job_morning_motivation(context):
    db = load_data()
    quote = random.choice(MORNING_QUOTES)
    days_left = (EXAM_DATE - datetime.now().date()).days
    
    msg = (
        "🌅 **GOOD MORNING STUDENTS!** 🌅\n\n"
        f"⏳ **Countdown:** {days_left} Days Left for Exam\n"
        "➖➖➖➖➖➖➖➖➖➖\n"
        f"💡 _'{quote}'_\n\n"
        "👉 **Note:** Check karein aaj test hai ya nahi!"
    )
    for gid in db["groups"]:
        try: await context.bot.send_message(chat_id=gid, text=msg);
        except: pass

# --- TEST SEQUENCE LOGIC ---
async def execute_test_logic(context, chat_id, test_data):
    # STEP 1: ATTENDANCE (00:00)
    try:
        btn = [[InlineKeyboardButton("🙋‍♂️ PRESENT SIR", callback_data='attendance_done')]]
        att_msg = (
            "🔔 **ATTENDANCE CALL** 🔔\n\n"
            f"📅 **Date:** {datetime.now().strftime('%d-%m-%Y')}\n"
            f"📌 **Topic:** {test_data['day']}\n\n"
            "⏳ Test starts in **2 Minutes**.\n"
            "👇 **Haaziri Lagayein (Click Button):**"
        )
        await context.bot.send_message(chat_id=chat_id, text=att_msg, reply_markup=InlineKeyboardMarkup(btn))
    except: pass

    await asyncio.sleep(60)

    # STEP 2: PIN ALERT (00:01)
    try:
        m = await context.bot.send_message(chat_id=chat_id, text="🚨 **ALERT:**\n          1 Minute Left!")
        try: await context.bot.pin_chat_message(chat_id=chat_id, message_id=m.message_id)
        except: pass
    except: pass

    await asyncio.sleep(60)

    # STEP 3: SEND LINK (00:02)
    try:
        t = (
            "🚀 **TEST STARTED** 🚀\n\n"
            f"📌 **Topic:** {test_data['day']}\n"
            f"👇 **Click Link below:**\n\n"
            f"{test_data['link']}\n\n"
            "_(Quiz dekar wapas aana)_"
        )
        await context.bot.send_message(chat_id=chat_id, text=t)
    except: pass

# --- 2. SCHEDULER JOB ---
async def job_send_test(context):
    db = load_data()
    # Check Today's Schedule
    today_str = datetime.now().strftime("%d-%m-%Y")
    test_data = get_test_by_date(today_str)
    
    if not test_data:
        # No test today
        await context.bot.send_message(OWNER_ID, f"ℹ️ Aaj ({today_str}) koi Test set nahi hai.")
        return

    # Execute Test
    for gid in db["groups"]:
        asyncio.create_task(execute_test_logic(context, gid, test_data))

    await context.bot.send_message(OWNER_ID, f"✅ Test Launched: {test_data['day']}")

# --- 3. NIGHT REPORT ---
async def job_nightly_report(context):
    db = load_data()
    today_str = datetime.now().strftime("%d-%m-%Y")
    test_data = get_test_by_date(today_str)
    
    # Agar aaj test nahi tha, to report mat banao
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
