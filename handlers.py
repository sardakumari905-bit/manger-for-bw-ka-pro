from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from database import load_data, save_data, is_admin, update_time, get_queue_list, set_daily_topper
from config import OWNER_ID, START_IMG
from datetime import datetime, time
import pytz
from jobs import job_send_test, execute_test_logic

ASK_DAY, ASK_LINK = range(2)

# --- START MENU ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_admin(user.id):
        caption = f"👑 **Boss: {user.first_name}**"
        keyboard = [
            [InlineKeyboardButton("🚀 QUICK START", callback_data='menu_quick_start')],
            [InlineKeyboardButton("➕ Add Link", callback_data='add_link_flow'),
             InlineKeyboardButton("🏆 Leaderboard", callback_data='show_leaderboard')],
            [InlineKeyboardButton("📢 Broadcast", callback_data='help_broadcast'),
             InlineKeyboardButton("⏰ Set Timer", callback_data='menu_timer')],
            [InlineKeyboardButton("📊 Dashboard", callback_data='status_check')]
        ]
    else:
        caption = "🤖 **RBSE Manager Bot**\nDaily Quiz & Attendance System."
        keyboard = [[InlineKeyboardButton("🏆 Check Leaderboard", callback_data='show_leaderboard')],
                    [InlineKeyboardButton("👨‍💻 Contact Admin", url="https://t.me/RoyalKing_7X4")]]

    await update.message.reply_photo(photo=START_IMG, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))

# --- LEADERBOARD LOGIC (New) ---
async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_data()
    users = db["users"]
    
    # List banao: (Name, Total Attendance)
    ranking = []
    for uid, data in users.items():
        # Sirf students ko count karo (Admin ko nahi)
        if int(uid) != OWNER_ID:
            count = data.get("total_attendance", 0)
            ranking.append((data["name"], count))
            
    # Sort karo (Jiske jyada attendance wo upar)
    ranking.sort(key=lambda x: x[1], reverse=True)
    
    # Top 10 nikalo
    top_10 = ranking[:10]
    
    txt = "🏆 **LEADERBOARD (Most Active Students)** 🏆\n\n"
    if not top_10:
        txt += "Abhi data nahi hai. Test hone do!"
    else:
        for i, (name, score) in enumerate(top_10, 1):
            if i == 1: icon = "🥇"
            elif i == 2: icon = "🥈"
            elif i == 3: icon = "🥉"
            else: icon = f"{i}."
            txt += f"{icon} **{name}** - {score} Tests\n"
            
    # Button handler ya command se call ho sakta hai
    if update.callback_query:
        await update.callback_query.message.reply_text(txt)
    else:
        await update.message.reply_text(txt)

# --- ATTENDANCE MARKING (Updated to Count Total) ---
async def mark_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = str(query.from_user.id)
    today = str(datetime.now().date())
    db = load_data()
    
    # Initialize User
    if uid not in db["users"]: 
        db["users"][uid] = {"name": query.from_user.first_name, "strikes": 0, "last_date": "", "total_attendance": 0}
    
    # Ensure 'total_attendance' key exists (Purane users ke liye)
    if "total_attendance" not in db["users"][uid]:
        db["users"][uid]["total_attendance"] = 0

    if db["users"][uid]["last_date"] == today:
        await query.answer("Already Marked! ✅", show_alert=True)
    else:
        db["users"][uid]["last_date"] = today
        db["users"][uid]["name"] = query.from_user.first_name
        # Increment Count
        db["users"][uid]["total_attendance"] += 1
        save_data(db)
        
        # Show Score in Alert
        total = db["users"][uid]["total_attendance"]
        await query.answer(f"✅ Present Sir!\nTotal Attendance: {total}", show_alert=True)

# --- EXISTING COMMANDS & HANDLERS ---
async def handle_forwarded_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    text = update.message.text or update.message.caption or ""
    if "🏆" in text or "Quiz" in text or "Results" in text:
        try:
            lines = text.split('\n')
            winner_name = "Unknown"
            for line in lines:
                if "🥇" in line or "1." in line:
                    clean_line = line.replace("🥇", "").replace("1.", "").strip()
                    winner_name = clean_line.split("-")[0].strip().split("–")[0].strip()
                    break
            if winner_name != "Unknown":
                set_daily_topper(winner_name)
                await update.message.reply_text(f"✅ **Topper Detected:** {winner_name}")
            else: await update.message.reply_text("⚠️ Name not found.")
        except: pass

async def set_topper_cmd(u, c):
    if not is_admin(u.effective_user.id): return
    if not c.args: await u.message.reply_text("Usage: `/set_topper Name`"); return
    set_daily_topper(" ".join(c.args))
    await u.message.reply_text(f"🏆 Topper Set!")

async def add_group(u, c):
    chat = u.effective_chat
    if chat.type == "private": return
    db = load_data()
    if chat.id not in db["groups"]:
        db["groups"].append(chat.id); save_data(db)
        await u.message.reply_text(f"✅ Connected: {chat.title}")
        await c.bot.send_message(OWNER_ID, f"📢 Group: {chat.title}")

async def add_user_cmd(u, c):
    if u.effective_user.id != OWNER_ID: return 
    if not c.args: await u.message.reply_text("ID daalo"); return
    try:
        nid = int(c.args[0])
        db = load_data()
        if nid not in db["auth_users"]: db["auth_users"].append(nid); save_data(db)
        await u.message.reply_text(f"✅ Admin Added: {nid}")
    except: pass

async def broadcast_cmd(u, c):
    if not is_admin(u.effective_user.id): return
    if not c.args: await u.message.reply_text("Msg likho"); return
    msg = " ".join(c.args); db = load_data()
    for gid in db["groups"]:
        try: await c.bot.send_message(gid, f"📢 **ANNOUNCEMENT:**\n\n{msg}")
        except: pass
    await u.message.reply_text("✅ Sent.")

async def status(u, c):
    if not is_admin(u.effective_user.id): return
    db = load_data()
    topper = db.get("daily_stats", {}).get("topper", "None")
    txt = f"📊 **STATUS**\nGroups: {len(db['groups'])}\nQueue: {len(db['queue'])}\nTime: {db['settings']['time']}\nTopper: {topper}"
    await u.message.reply_text(txt)

# --- BUTTONS ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == 'menu_timer':
        btns = [
            [InlineKeyboardButton("🕓 4 PM", callback_data='time_16'),
             InlineKeyboardButton("🕔 5 PM", callback_data='time_17')],
            [InlineKeyboardButton("🕕 6 PM", callback_data='time_18'),
             InlineKeyboardButton("🕖 7 PM", callback_data='time_19')],
            [InlineKeyboardButton("🕗 8 PM", callback_data='time_20'),
             InlineKeyboardButton("🕘 9 PM", callback_data='time_21')],
            [InlineKeyboardButton("🔙 Back", callback_data='back_home')]
        ]
        await query.message.edit_reply_markup(InlineKeyboardMarkup(btns))
        
    elif data.startswith('time_'):
        h = int(data.split('_')[1])
        update_time(f"{h}:00")
        q = context.application.job_queue
        for job in q.jobs():
            if job.callback.__name__ == 'job_send_test': job.schedule_removal()
        q.run_daily(job_send_test, time(hour=h, minute=0, tzinfo=pytz.timezone('Asia/Kolkata')))
        await query.message.edit_caption(caption=f"✅ **Time Set:** {h}:00 PM")
        
    elif data == 'menu_quick_start':
        queue = get_queue_list()
        if not queue: await query.message.reply_text("⚠️ Queue Empty!"); return
        btns = []
        for i, item in enumerate(queue):
            btns.append([InlineKeyboardButton(f"🚀 Fire: {item['day']}", callback_data=f"fire_{i}")])
        await query.message.reply_text("👇 **Select Test:**", reply_markup=InlineKeyboardMarkup(btns))
        
    elif data.startswith('fire_'):
        index = int(data.split('_')[1])
        queue = get_queue_list()
        if index < len(queue):
            test = queue[index]
            await query.message.reply_text(f"⏳ **Starting {test['day']}...**")
            db = load_data()
            for gid in db["groups"]: context.application.create_task(execute_test_logic(context, gid, test))

    elif data == 'show_leaderboard': await show_leaderboard(query, context)
    elif data == 'back_home': await start(query, context)
    elif data == 'status_check': await status(query, context)
    elif data == 'add_link_flow': await query.message.reply_text("Likhein: `/add_link`")
    elif data == 'help_broadcast': await query.message.reply_text("Likhein: `/broadcast Message`")

# --- CONVERSATION ---
async def start_add_link(u, c):
    if not is_admin(u.effective_user.id): return ConversationHandler.END
    await u.message.reply_text("📝 **Topic?**"); return ASK_DAY

async def receive_day(u, c):
    c.user_data['day'] = u.message.text; await u.message.reply_text("🔗 **Link?**"); return ASK_LINK

async def receive_link(u, c):
    db = load_data(); db["queue"].append({"day": c.user_data['day'], "link": u.message.text}); save_data(db)
    await u.message.reply_text("✅ Saved!"); return ConversationHandler.END

async def cancel(u, c): await u.message.reply_text("❌ Cancelled"); return ConversationHandler.END
