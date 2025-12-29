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
        caption = f"👑 **Boss: {user.first_name}**\n👇 **Option Select Karein:**"
        keyboard = [
            [InlineKeyboardButton("➕ Schedule Test", callback_data='add_link_flow')],
            [InlineKeyboardButton("⏰ Set Time", callback_data='menu_timer'),
             InlineKeyboardButton("📢 Broadcast", callback_data='help_broadcast')],
            [InlineKeyboardButton("👮 Add Admin", callback_data='help_admin'),
             InlineKeyboardButton("📊 Status", callback_data='status_check')],
             [InlineKeyboardButton("🗑️ RESET BOT", callback_data='reset_flow')]
        ]
    else:
        caption = "🤖 **RBSE Manager Bot**\nDaily Quiz & Attendance System."
        keyboard = [
            [InlineKeyboardButton("👤 My Profile", callback_data='my_profile')],
            [InlineKeyboardButton("🏆 Leaderboard", callback_data='show_leaderboard')]
        ]
    
    # Check if called from button or command
    if update.callback_query:
        await update.callback_query.message.edit_caption(caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_photo(photo=START_IMG, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))

# --- 1. ADD TEST FLOW (BUTTON SUPPORTED) ---
async def start_add_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Agar button dabaya h to answer kero
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text("📅 **Date batayein?** (DD-MM-YYYY)\ne.g., `01-01-2026`")
    else:
        if not is_admin(update.effective_user.id): return ConversationHandler.END
        await update.message.reply_text("📅 **Date batayein?** (DD-MM-YYYY)\ne.g., `01-01-2026`")
    return ASK_DATE

async def receive_date(u, c):
    try:
        datetime.strptime(u.message.text, "%d-%m-%Y")
        c.user_data['date'] = u.message.text
        await u.message.reply_text("📝 **Topic ka naam?**\n(e.g. Physics Ch-1)")
        return ASK_TOPIC
    except:
        await u.message.reply_text("❌ Galat Date! Aise likhein: `01-01-2026`")
        return ASK_DATE

async def receive_topic(u, c):
    c.user_data['topic'] = u.message.text
    await u.message.reply_text("🔗 **Quiz Link paste karein:**")
    return ASK_LINK

async def receive_link(u, c):
    add_test_to_schedule(c.user_data['date'], c.user_data['topic'], u.message.text)
    await u.message.reply_text(f"✅ **Success!** Test Scheduled.\n📅 Date: {c.user_data['date']}")
    return ConversationHandler.END

async def cancel(u, c): 
    await u.message.reply_text("❌ Cancelled"); return ConversationHandler.END

# --- 2. TIMER MENU (BUTTONS WAPAS AA GYE) ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == 'menu_timer':
        # Yahan Buttons wapas daal diye
        btns = [
            [InlineKeyboardButton("🕓 4 PM", callback_data='time_16'),
             InlineKeyboardButton("🕔 5 PM", callback_data='time_17')],
            [InlineKeyboardButton("🕕 6 PM", callback_data='time_18'),
             InlineKeyboardButton("🕖 7 PM", callback_data='time_19')],
            [InlineKeyboardButton("🕗 8 PM", callback_data='time_20'),
             InlineKeyboardButton("🔙 Back", callback_data='back_home')]
        ]
        await query.message.edit_reply_markup(InlineKeyboardMarkup(btns))
        
    elif data.startswith('time_'):
        h = int(data.split('_')[1])
        update_time(f"{h}:00")
        # Job Update
        q = context.application.job_queue
        for job in q.jobs():
            if job.callback.__name__ == 'job_send_test': job.schedule_removal()
        q.run_daily(job_send_test, time(hour=h, minute=0, tzinfo=pytz.timezone('Asia/Kolkata')))
        await query.message.edit_caption(caption=f"✅ **Time Updated:** {h}:00 PM")
        
    elif data == 'help_broadcast': await query.message.reply_text("📝 **Broadcast:**\nLikhein: `/broadcast Hello Students`")
    elif data == 'help_admin': await query.message.reply_text("👮 **Add Admin:**\nLikhein: `/add_user 12345678`")
    elif data == 'status_check': db=load_data(); await query.message.reply_text(f"📊 Tests Scheduled: {len(db['schedule'])}")
    elif data == 'reset_flow': await query.message.reply_text("⚠️ **Confirm Reset?**\nType `/reset_all` to delete everything.")
    elif data == 'back_home': await start(query, context)
    
    # Student Buttons
    elif data == 'my_profile': await show_profile(query, context)
    elif data == 'show_leaderboard': await show_leaderboard(query, context)

# --- OTHER COMMANDS (Same as before) ---
async def reset_all_cmd(u, c):
    if u.effective_user.id == OWNER_ID: reset_bot_data(); await u.message.reply_text("☢️ **BOT RESET DONE.**")

async def broadcast_cmd(u, c):
    if is_admin(u.effective_user.id) and c.args:
        msg = " ".join(c.args); db = load_data(); sent=0
        for gid in db["groups"]:
            try: await c.bot.send_message(gid, f"📢 **NOTICE:**\n\n{msg}"); sent+=1
            except: pass
        await u.message.reply_text(f"✅ Sent to {sent} groups.")
    else: await u.message.reply_text("❌ Message empty.")

async def add_user_cmd(u, c):
    if u.effective_user.id == OWNER_ID and c.args:
        try:
            nid = int(c.args[0]); db = load_data()
            if nid not in db["auth_users"]: db["auth_users"].append(nid); save_data(db)
            await u.message.reply_text("✅ Admin Added")
        except: pass

async def set_topper_cmd(u, c):
    if is_admin(u.effective_user.id) and c.args: set_daily_topper(" ".join(c.args)); await u.message.reply_text("✅ Set")

async def add_group(u, c):
    if u.effective_chat.type!="private":
        db=load_data(); 
        if u.effective_chat.id not in db["groups"]: db["groups"].append(u.effective_chat.id); save_data(db); await u.message.reply_text("✅ Connected")

# --- AUTO ATTENDANCE & HELPERS ---
async def handle_forwarded_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    text = update.message.text or update.message.caption or ""
    if "🏆" in text or "Quiz" in text or "Results" in text:
        db = load_data(); today = str(datetime.now().date()); lines = text.split('\n')
        detected = []; topper = "Unknown"; count = 0
        for line in lines:
            if "🥇" in line or "1." in line or (len(line)>0 and line[0].isdigit() and "." in line):
                try:
                    clean = line.replace("🥇","").replace("1.","").split("-")[0].split("–")[0].strip()
                    if "." in clean: clean = clean.split(".",1)[1].strip()
                    if clean: detected.append(clean); 
                    if topper=="Unknown": topper=clean
                except: pass
        if topper != "Unknown": set_daily_topper(topper)
        if detected:
            for uid, u in db["users"].items():
                if u["name"] in detected and u["last_date"] != today:
                    u["last_date"] = today; u["total_attendance"] = u.get("total_attendance",0)+1; count+=1
            save_data(db)
            await update.message.reply_text(f"✅ **Done!** Topper: {topper}\n💾 Auto-Attendance: {count}")

async def show_profile(u, c):
    db=load_data(); uid=str(u.effective_user.id)
    txt = f"👤 {db['users'][uid]['name']} | Att: {db['users'][uid].get('total_attendance',0)}" if uid in db['users'] else "❌ No Record"
    if u.callback_query: await u.callback_query.message.reply_text(txt)

async def show_leaderboard(u, c):
    db=load_data(); r=[(d['name'],d.get('total_attendance',0)) for i,d in db['users'].items() if int(i)!=OWNER_ID]; r.sort(key=lambda x:x[1],reverse=True)
    txt="🏆 TOP 5:\n"+"\n".join([f"{i+1}. {n} ({s})" for i,(n,s) in enumerate(r[:5])])
    if u.callback_query: await u.callback_query.message.reply_text(txt)

async def mark_attendance(u, c):
    uid=str(u.callback_query.from_user.id); today=str(datetime.now().date()); db=load_data()
    if uid not in db['users']: db['users'][uid]={'name':u.callback_query.from_user.first_name,'strikes':0,'last_date':'','total_attendance':0}
    if db['users'][uid]['last_date']!=today: db['users'][uid]['last_date']=today; db['users'][uid]['total_attendance']+=1; save_data(db); await u.callback_query.answer("✅ Marked!", show_alert=True)
    else: await u.callback_query.answer("✅ Already Marked", show_alert=True)
