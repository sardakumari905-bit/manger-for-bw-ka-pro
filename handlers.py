from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from database import load_data, save_data, is_admin, update_time, add_test_to_schedule, set_daily_topper, reset_bot_data
from config import OWNER_ID, START_IMG
from datetime import datetime, time
import pytz
from jobs import job_send_test

ASK_DATE, ASK_TOPIC, ASK_LINK = range(3)

# --- START MENU ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_admin(user.id):
        caption = f"👑 **Boss: {user.first_name}**"
        keyboard = [
            [InlineKeyboardButton("➕ Schedule Test", callback_data='add_link_flow')],
            [InlineKeyboardButton("⏰ Custom Time", callback_data='menu_timer'),
             InlineKeyboardButton("📊 Status", callback_data='status_check')],
             [InlineKeyboardButton("🗑️ RESET BOT", callback_data='reset_flow')]
        ]
    else:
        caption = "🤖 **RBSE Manager Bot**\nDaily Quiz & Attendance System."
        keyboard = [
            [InlineKeyboardButton("👤 My Profile", callback_data='my_profile')],
            [InlineKeyboardButton("🏆 Leaderboard", callback_data='show_leaderboard')]
        ]
    await update.message.reply_photo(photo=START_IMG, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))

# --- 🔥 SUPER FEATURE: AUTO-ATTENDANCE FROM FORWARD ---
async def handle_forwarded_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    
    text = update.message.text or update.message.caption or ""
    
    # Identify QuizBot Message
    if "🏆" in text or "Quiz" in text or "Results" in text:
        db = load_data()
        today = str(datetime.now().date())
        lines = text.split('\n')
        
        detected_names = []
        topper_name = "Unknown"
        saved_count = 0
        
        # Parse Names
        for line in lines:
            if "🥇" in line or "🥈" in line or "🥉" in line or (len(line) > 0 and line[0].isdigit() and "." in line):
                try:
                    # Clean Name
                    clean = line.replace("🥇", "").replace("🥈", "").replace("🥉", "")
                    if "." in clean: clean = clean.split(".", 1)[1]
                    if "-" in clean: name_part = clean.split("-")[0]
                    elif "–" in clean: name_part = clean.split("–")[0]
                    else: name_part = clean
                    
                    final_name = name_part.strip()
                    if final_name:
                        detected_names.append(final_name)
                        if topper_name == "Unknown": topper_name = final_name
                except: pass

        # Set Topper
        if topper_name != "Unknown": set_daily_topper(topper_name)

        # Mark Auto Attendance
        if detected_names:
            for uid, user_data in db["users"].items():
                # Match Name
                if user_data["name"] in detected_names:
                    # Mark if not already marked
                    if user_data["last_date"] != today:
                        user_data["last_date"] = today
                        user_data["total_attendance"] = user_data.get("total_attendance", 0) + 1
                        saved_count += 1
            
            save_data(db)
            
            msg = (
                f"✅ **LEADERBOARD PROCESSED!**\n\n"
                f"🏆 **Topper:** {topper_name}\n"
                f"👥 **Names Found:** {len(detected_names)}\n"
                f"💾 **Recovered Attendance:** {saved_count} Students\n"
                "(Ye wo bachhe hain jo button dabana bhool gaye the)"
            )
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("⚠️ Koi naam detect nahi hua.")

# --- COMMANDS ---
async def reset_all_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    reset_bot_data()
    await update.message.reply_text("☢️ **SYSTEM RESET SUCCESSFUL!**")

async def set_custom_time_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args: await update.message.reply_text("❌ Usage: `/custom_time 03:00`"); return
    try:
        h, m = map(int, context.args[0].split(":"))
        update_time(f"{h}:{m}")
        q = context.application.job_queue
        for job in q.jobs(): 
            if job.callback.__name__ == 'job_send_test': job.schedule_removal()
        q.run_daily(job_send_test, time(hour=h, minute=m, tzinfo=pytz.timezone('Asia/Kolkata')))
        await update.message.reply_text(f"✅ Timer Set: {h:02d}:{m:02d}")
    except: await update.message.reply_text("❌ Error. Format: HH:MM")

# --- ADD SCHEDULE CONVERSATION ---
async def start_add_link(u, c):
    if not is_admin(u.effective_user.id): return ConversationHandler.END
    await u.message.reply_text("📅 **Date?** (DD-MM-YYYY)\ne.g., `01-01-2026`"); return ASK_DATE

async def receive_date(u, c):
    try:
        datetime.strptime(u.message.text, "%d-%m-%Y")
        c.user_data['date'] = u.message.text
        await u.message.reply_text("📝 **Topic?**"); return ASK_TOPIC
    except: await u.message.reply_text("❌ Wrong Format!"); return ASK_DATE

async def receive_topic(u, c):
    c.user_data['topic'] = u.message.text
    await u.message.reply_text("🔗 **Quiz Link?**"); return ASK_LINK

async def receive_link(u, c):
    add_test_to_schedule(c.user_data['date'], c.user_data['topic'], u.message.text)
    await u.message.reply_text(f"✅ **SCHEDULED for {c.user_data['date']}!**"); return ConversationHandler.END

async def cancel(u, c): await u.message.reply_text("❌ Cancelled"); return ConversationHandler.END

# --- HELPERS ---
async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(user.id); db = load_data()
    if uid in db["users"]:
        d = db["users"][uid]
        txt = f"👤 **PROFILE**\nName: {d['name']}\nAttendance: {d.get('total_attendance', 0)}\nStrikes: {d['strikes']}/3"
    else: txt = "❌ No Data found."
    if update.callback_query: await update.callback_query.message.reply_text(txt)

async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_data()
    ranking = [(d["name"], d.get("total_attendance", 0)) for uid, d in db["users"].items() if int(uid) != OWNER_ID]
    ranking.sort(key=lambda x: x[1], reverse=True)
    txt = "🏆 **TOP 5**\n" + "\n".join([f"{i+1}. {n} ({s})" for i, (n,s) in enumerate(ranking[:5])])
    if update.callback_query: await update.callback_query.message.reply_text(txt)

async def set_topper_cmd(u, c):
    if is_admin(u.effective_user.id) and c.args: set_daily_topper(" ".join(c.args)); await u.message.reply_text("✅ Topper Set")

async def add_group(u, c):
    chat = u.effective_chat; db = load_data()
    if chat.type != "private" and chat.id not in db["groups"]:
        db["groups"].append(chat.id); save_data(db); await u.message.reply_text("✅ Connected")

async def add_user_cmd(u, c):
    if u.effective_user.id != OWNER_ID: return 
    if not c.args: await u.message.reply_text("ID daalo"); return
    try:
        nid = int(c.args[0]); db = load_data()
        if nid not in db["auth_users"]: db["auth_users"].append(nid); save_data(db)
        await u.message.reply_text(f"✅ Admin Added")
    except: pass

async def broadcast_cmd(u, c):
    if not is_admin(u.effective_user.id): return
    if not c.args: await u.message.reply_text("Msg likho"); return
    msg = " ".join(c.args); db = load_data()
    for gid in db["groups"]:
        try: await c.bot.send_message(gid, f"📢 **ANNOUNCEMENT:**\n\n{msg}")
        except: pass
    await u.message.reply_text("✅ Sent.")

# --- BUTTONS ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer(); data = query.data
    if data == 'add_link_flow': await query.message.reply_text("Type `/add_test`")
    elif data == 'reset_flow': await query.message.reply_text("Type `/reset_all` to confirm.")
    elif data == 'my_profile': await show_profile(query, context)
    elif data == 'show_leaderboard': await show_leaderboard(query, context)
    elif data == 'status_check': db = load_data(); await query.message.reply_text(f"📊 Scheduled: {len(db['schedule'])}")
    elif data == 'menu_timer': await query.message.reply_text("Use `/custom_time HH:MM`")

# --- ATTENDANCE MARK ---
async def mark_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; uid = str(query.from_user.id); today = str(datetime.now().date())
    db = load_data()
    if uid not in db["users"]: db["users"][uid] = {"name": query.from_user.first_name, "strikes": 0, "last_date": "", "total_attendance": 0}
    
    if db["users"][uid]["last_date"] == today:
        await query.answer("Already Marked! ✅", show_alert=True)
    else:
        db["users"][uid]["last_date"] = today
        db["users"][uid]["name"] = query.from_user.first_name
        db["users"][uid]["total_attendance"] = db["users"][uid].get("total_attendance", 0) + 1
        save_data(db)
        await query.answer("✅ Attendance Marked!", show_alert=True)
