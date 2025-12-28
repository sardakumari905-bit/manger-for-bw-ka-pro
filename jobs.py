import asyncio
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import load_data, save_data
from config import OWNER_ID
from datetime import datetime, date

# --- EXAM DATE SETTING ---
EXAM_DATE = date(2026, 2, 12) # Yahan Exam ki date dalein (Year, Month, Date)

# --- MOTIVATIONAL QUOTES ---
MORNING_QUOTES = [
    "Mehnat itni khamoshi se karo ki safalta shor macha de.",
    "Sapne wo nahi jo sote waqt dikhte hain, sapne wo hain jo sone nahi dete.",
    "Jo paani se nahata hai wo libaas badalta hai, jo pasine se nahata hai wo itihaas badalta hai.",
    "Aaj ka dard kal ki taqat banega.",
    "Exam pass hai, ab rukna mana hai!"
]

# --- MORNING JOB (Countdown + Motivation) ---
async def job_morning_motivation(context):
    db = load_data()
    quote = random.choice(MORNING_QUOTES)
    
    # Calculate Days Left
    today = datetime.now().date()
    days_left = (EXAM_DATE - today).days
    
    msg = (
        "🌅 **GOOD MORNING STUDENTS!** 🌅\n\n"
        f"⏳ **RBSE BOARD EXAM:** {days_left} Days Left\n"
        "➖➖➖➖➖➖➖➖➖➖\n"
        f"💡 _'{quote}'_\n\n"
        "👉 **Aaj ka Test:** Sham ko hoga.\n"
        "Taiyaar rehna!"
    )
    
    for gid in db["groups"]:
        try:
            await context.bot.send_message(chat_id=gid, text=msg)
        except: pass

# --- EXECUTE TEST LOGIC ---
async def execute_test_logic(context, chat_id, test_data):
    # STEP 1: ATTENDANCE
    try:
        btn = [[InlineKeyboardButton("🙋‍♂️ PRESENT SIR (Click Here)", callback_data='attendance_done')]]
        att_msg = (
            "🔔 **ATTENDANCE TIME** 🔔\n\n"
            f"📌 **Topic:** {test_data['day']}\n"
            "⏳ Test starts in **2 Minutes**.\n\n"
            "👇 **Button dabakar Haaziri lagayein!**"
        )
        await context.bot.send_message(chat_id=chat_id, text=att_msg, reply_markup=InlineKeyboardMarkup(btn))
    except: pass

    await asyncio.sleep(60)

    # STEP 2: PIN ALERT
    try:
        alert = "🚨 **ALERT:** Test starts in 1 Minute!\n⚡ Get Ready!"
        msg = await context.bot.send_message(chat_id=chat_id, text=alert)
        try: await context.bot.pin_chat_message(chat_id=chat_id, message_id=msg.message_id)
        except: pass 
    except: pass

    await asyncio.sleep(60)

    # STEP 3: SEND LINK
    try:
        link_msg = (
            "🚀 **TEST LIVE NOW** 🚀\n\n"
            f"📌 **Topic:** {test_data['day']}\n\n"
            f"👇 **Click Link to Start Quiz:**\n"
            f"{test_data['link']}\n\n"
            "_(Good Luck!)_"
        )
        await context.bot.send_message(chat_id=chat_id, text=link_msg)
    except: pass

# --- AUTO JOB ---
async def job_send_test(context):
    db = load_data()
    if not db["queue"]:
        await context.bot.send_message(OWNER_ID, "⚠️ Queue Empty!")
        return
    test_data = db["queue"].pop(0)
    save_data(db)
    for gid in db["groups"]:
        asyncio.create_task(execute_test_logic(context, gid, test_data))
    await context.bot.send_message(OWNER_ID, f"✅ Test Started: {test_data['day']}")

# --- NIGHT REPORT ---
async def job_nightly_report(context):
    db = load_data()
    today = str(datetime.now().date())
    absent = []
    kicked = []
    topper_name = db.get("daily_stats", {}).get("topper", "Pending...")
    
    for uid, info in db["users"].items():
        if int(uid) == OWNER_ID or int(uid) in db["auth_users"]: continue
        
        if info["last_date"] != today:
            info["strikes"] += 1
            absent.append(f"{info['name']} (Miss: {info['strikes']})")
            if info["strikes"] >= 3:
                kicked.append(info['name'])
                info["strikes"] = 0
                for gid in db["groups"]:
                    try:
                        await context.bot.ban_chat_member(gid, int(uid))
                        await context.bot.unban_chat_member(gid, int(uid))
                    except: pass
        else: pass
            
    db["daily_stats"]["topper"] = "Pending..."
    save_data(db)
    
    report = "🌙 **NIGHT REPORT (9:30 PM)** 🌙\n\n"
    report += f"🏆 **TOPPER:** {topper_name} 🎉\n\n"
    if absent: report += "❌ **ABSENT:**\n" + "\n".join(absent) + "\n\n"
    else: report += "✅ **All Present!**\n\n"
    if kicked: report += "🚫 **BANNED:**\n" + "\n".join(kicked)

    for gid in db["groups"]:
        try: await context.bot.send_message(gid, report)
        except: pass
