import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import load_data, save_data
from config import OWNER_ID
from datetime import datetime

# --- CORE LOGIC: ATTENDANCE FIRST -> PIN -> LINK ---
async def execute_test_logic(context, chat_id, test_data):
    
    # STEP 1: ATTENDANCE (00:00) - Sabse Pehle
    try:
        # Button: '🙋‍♂️ PRESENT SIR'
        btn = [[InlineKeyboardButton("🙋‍♂️ PRESENT SIR (Click Here)", callback_data='attendance_done')]]
        
        att_msg = (
            "🔔 **ATTENDANCE TIME** 🔔\n\n"
            f"📌 **Topic:** {test_data['day']}\n"
            "⏳ Test shuru hone me **2 Minute** bache hain.\n\n"
            "👇 **Test dene se pehle Button dabakar Haaziri lagayein!**\n"
            "_(Button nahi dabaya to System Absent manega)_"
        )
        await context.bot.send_message(chat_id=chat_id, text=att_msg, reply_markup=InlineKeyboardMarkup(btn))
    except Exception as e:
        print(f"Attendance Msg Failed for {chat_id}: {e}")

    # WAIT 1 MINUTE
    await asyncio.sleep(60)

    # STEP 2: PIN ALERT (00:01) - Warning
    try:
        alert = "🚨 **ALERT:** Test starts in 1 Minute!\n⚡ Get Ready!"
        msg = await context.bot.send_message(chat_id=chat_id, text=alert)
        try: 
            await context.bot.pin_chat_message(chat_id=chat_id, message_id=msg.message_id)
        except: 
            pass 
    except: pass

    # WAIT 1 MINUTE
    await asyncio.sleep(60)

    # STEP 3: SEND LINK (00:02) - Final
    try:
        link_msg = (
            "🚀 **TEST LIVE NOW** 🚀\n\n"
            f"📌 **Topic:** {test_data['day']}\n\n"
            f"👇 **Click Link to Start Quiz:**\n"
            f"{test_data['link']}\n\n"
            "_(Test finish karke wapas Group me aana)_"
        )
        await context.bot.send_message(chat_id=chat_id, text=link_msg)
    except: pass

# --- AUTOMATIC JOB ---
async def job_send_test(context):
    db = load_data()
    if not db["queue"]:
        await context.bot.send_message(OWNER_ID, "⚠️ **Alert:** Queue Empty! Link add karein.")
        return

    test_data = db["queue"].pop(0)
    save_data(db)
    
    # Sabhi groups me chalao
    for gid in db["groups"]:
        asyncio.create_task(execute_test_logic(context, gid, test_data))

    await context.bot.send_message(OWNER_ID, f"✅ Test Started: {test_data['day']}")

# --- NIGHT REPORT (9:30 PM) ---
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
            absent.append(f"{info['name']} (Missed: {info['strikes']})")
            
            # KICK LOGIC (3 Strikes)
            if info["strikes"] >= 3:
                kicked.append(info['name'])
                info["strikes"] = 0
                for gid in db["groups"]:
                    try:
                        await context.bot.ban_chat_member(gid, int(uid))
                        await context.bot.unban_chat_member(gid, int(uid))
                    except: pass
        else: pass
            
    # Reset Topper
    db["daily_stats"]["topper"] = "Pending..."
    save_data(db)
    
    report = "🌙 **NIGHT REPORT (9:30 PM)** 🌙\n\n"
    report += f"🏆 **AAJ KA TOPPER:** {topper_name} 🎉\n\n"
    
    if absent: report += "❌ **ABSENT STUDENTS:**\n" + "\n".join(absent) + "\n\n"
    else: report += "✅ **All Present!**\n\n"
    if kicked: report += "🚫 **BANNED (3 Strikes):**\n" + "\n".join(kicked)

    for gid in db["groups"]:
        try: await context.bot.send_message(gid, report)
        except: pass
