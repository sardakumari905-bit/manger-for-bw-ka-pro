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
        caption = f"👑 **Boss: {user.first_name}**\n\n👇 **Control Panel:**"
        keyboard = [
            [InlineKeyboardButton("🚀 QUICK START (Testing)", callback_data='menu_quick_start')],
            [InlineKeyboardButton("➕ Add Link", callback_data='add_link_flow'),
             InlineKeyboardButton("📢 Broadcast", callback_data='help_broadcast')],
            [InlineKeyboardButton("⏰ Set Timer", callback_data='menu_timer'),
             InlineKeyboardButton("📊 Dashboard", callback_data='status_check')]
        ]
    else:
        caption = "🤖 **RBSE Manager Bot**\nDaily Quiz & Attendance System."
        keyboard = [[InlineKeyboardButton("👨‍💻 Contact Admin", url="https://t.me/RoyalKing_7X4")]]

    await update.message.reply_photo(photo=START_IMG, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))

# --- NEW COMMAND: ADD ADMIN (Ye miss ho gaya tha) ---
async def add_user_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return # Sirf Owner kar sakta hai
    
    if not context.args:
        await update.message.reply_text("❌ Usage: `/add_user 12345678` (ID daalein)")
        return
    
    try:
        new_id = int(context.args[0])
        db = load_data()
        if new_id not in db["auth_users"]:
            db["auth_users"].append(new_id)
            save_data(db)
            await update.message.reply_text(f"✅ **New Admin Added:** {new_id}\n(Ab ye bhi bot control kar sakta hai)")
        else:
            await update.message.reply_text("ℹ️ Ye ID pehle se Admin hai.")
    except:
        await update.message.reply_text("❌ Kripya valid Number ID daalein.")

# --- AUTO DETECT TOPPER ---
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
                await update.message.reply_text(f"✅ **Auto-Detected Topper:** {winner_name}\n(Saved for Night Report)")
            else:
                await update.message.reply_text("⚠️ Name detect nahi hua. `/set_topper` use karein.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

# --- OTHER COMMANDS ---
async def set_topper_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args: await update.message.reply_text("❌ Usage: `/set_topper Name`"); return
    name = " ".join(context.args)
    set_daily_topper(name)
    await update.message.reply_text(f"🏆 Topper Set: {name}")

async def add_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private": return
    db = load_data()
    if chat.id not in db["groups"]:
        db["groups"].append(chat.id)
        save_data(db)
        await update.message.reply_text(f"✅ **Connected:** {chat.title}")
        await context.bot.send_message(OWNER_ID, f"📢 New Group: {chat.title}")

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args: await update.message.reply_text("❌ Msg likho"); return
    msg = " ".join(context.args)
    db = load_data()
    for gid in db["groups"]:
        try: await context.bot.send_message(gid, f"📢 **ANNOUNCEMENT:**\n\n{msg}")
        except: pass
    await update.message.reply_text(f"✅ Broadcast Sent.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    db = load_data()
    topper = db.get("daily_stats", {}).get("topper", "None")
    txt = f"📊 **STATUS**\nGroups: {len(db['groups'])}\nQueue: {len(db['queue'])}\nTime: {db['settings']['time']}\nTopper: {topper}\nAdmins: {len(db['auth_users'])+1}"
    await update.message.reply_text(txt)

# --- BUTTON HANDLER ---
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
            await query.message.reply_text(f"⏳ **Starting {test['day']}...**\n(Sequence: Attendance -> Pin -> Link)")
            db = load_data()
            for gid in db["groups"]:
                context.application.create_task(execute_test_logic(context, gid, test))
                
    elif data == 'back_home': await start(query, context)
    elif data == 'status_check': await status(query, context)
    elif data == 'add_link_flow': await query.message.reply_text("Likhein: `/add_link`")
    elif data == 'help_broadcast': await query.message.reply_text("Likhein: `/broadcast Message`")

# --- ATTENDANCE ---
async def mark_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = str(query.from_user.id)
    today = str(datetime.now().date())
    db = load_data()
    if uid not in db["users"]: db["users"][uid] = {"name": query.from_user.first_name, "strikes": 0, "last_date": ""}
    
    if db["users"][uid]["last_date"] == today:
        await query.answer("Already Marked! ✅", show_alert=True)
    else:
        db["users"][uid]["last_date"] = today
        db["users"][uid]["name"] = query.from_user.first_name
        save_data(db)
        await query.answer("✅ Attendance Marked!", show_alert=True)

# --- CONVERSATION ---
async def start_add_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return ConversationHandler.END
    await update.message.reply_text("📝 **Topic Name?**")
    return ASK_DAY

async def receive_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['day'] = update.message.text
    await update.message.reply_text("🔗 **QuizBot Link?**")
    return ASK_LINK

async def receive_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = update.message.text
    day = context.user_data['day']
    db = load_data()
    db["queue"].append({"day": day, "link": link})
    save_data(db)
    await update.message.reply_text(f"✅ **Saved!** {day}")
    return ConversationHandler.END

async def cancel(u, c): await u.message.reply_text("❌ Cancelled"); return ConversationHandler.END
