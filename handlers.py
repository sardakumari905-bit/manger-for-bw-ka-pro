from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from database import load_data, save_data, is_admin, update_time, add_test_to_schedule, set_daily_topper, reset_bot_data
from config import OWNER_ID, START_IMG
from datetime import datetime, time
import pytz
from jobs import job_send_test, execute_test_logic

# --- STATES ---
ASK_DATE, ASK_TOPIC, ASK_LINK = range(3)
ASK_BROADCAST_MSG = 3
ASK_ADMIN_ID = 4

# --- START MENU ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_admin(user.id):
        caption = f"👑 **Boss: {user.first_name}**\n👇 **COMPLETE CONTROL PANEL:**"
        keyboard = [
            [InlineKeyboardButton("🚀 QUICK START (Fire Now)", callback_data='menu_quick_start')],
            [InlineKeyboardButton("➕ Schedule Test", callback_data='add_link_flow'),
             InlineKeyboardButton("📢 Broadcast", callback_data='broadcast_flow')],
            [InlineKeyboardButton("⏰ Set Timer", callback_data='menu_timer'),
             InlineKeyboardButton("👮 Add Admin", callback_data='add_admin_flow')],
            [InlineKeyboardButton("📊 Status", callback_data='status_check'),
             InlineKeyboardButton("🗑️ RESET BOT", callback_data='reset_flow')]
        ]
    else:
        caption = "🤖 **RBSE Manager Bot**\nDaily Quiz & Attendance System."
        keyboard = [
            [InlineKeyboardButton("👤 My Profile", callback_data='my_profile')],
            [InlineKeyboardButton("🏆 Leaderboard", callback_data='show_leaderboard')]
        ]
    
    if update.callback_query:
        await update.callback_query.message.edit_caption(caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_photo(photo=START_IMG, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))

# --- 1. QUICK START (WAPAS AA GAYA) ---
async def quick_start_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    db = load_data()
    schedule = db.get("schedule", {})
    
    if not schedule:
        await query.answer("⚠️ Schedule Empty! Pehle test add karein.", show_alert=True)
        return

    btns = []
    # Dates ki list banao
    for date_str, data in schedule.items():
        btns.append([InlineKeyboardButton(f"🚀 Fire: {data['day']} ({date_str})", callback_data=f"fire_{date_str}")])
    
    btns.append([InlineKeyboardButton("🔙 Back", callback_data='back_home')])
    await query.message.edit_caption("👇 **Select Test to Launch IMMEDIATELY:**", reply_markup=InlineKeyboardMarkup(btns))

async def fire_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    date_str = query.data.split("_")[1]
    db = load_data()
    test_data = db["schedule"].get(date_str)
    
    if test_data:
        await query.message.reply_text(f"🚀 **Launching {test_data['day']} NOW!**\n(Check Groups)")
        for gid in db["groups"]:
            # Background task me test chalao
            context.application.create_task(execute_test_logic(context, gid, test_data))
    else:
        await query.answer("❌ Error: Test nahi mila.", show_alert=True)

# --- 2. BROADCAST (BUTTON WALA) ---
async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📢 **Broadcast Message likhein:**\n(Jo bhi likhoge wo sab group me jayega)")
    return ASK_BROADCAST_MSG

async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    db = load_data()
    count = 0
    for gid in db["groups"]:
        try:
            await context.bot.send_message(gid, f"📢 **ANNOUNCEMENT:**\n\n{msg}")
            count += 1
        except: pass
    await update.message.reply_text(f"✅ **Broadcast Sent!**\nTotal Groups: {count}")
    return ConversationHandler.END

# --- 3. ADD ADMIN (BUTTON WALA) ---
async def start_add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("👮 **New Admin ki Telegram ID bhejein:**\n(Number only, e.g., 12345678)")
    return ASK_ADMIN_ID

async def receive_admin_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        new_id = int(update.message.text)
        db = load_data()
        if new_id not in db["auth_users"]:
            db["auth_users"].append(new_id)
            save_data(db)
            await update.message.reply_text(f"✅ **Success!** {new_id} is now an Admin.")
        else:
            await update.message.reply_text("ℹ️ Ye pehle se Admin hai.")
    except:
        await update.message.reply_text("❌ Invalid ID. Number bhejein.")
    return ConversationHandler.END

# --- 4. SCHEDULE TEST FLOW ---
async def start_add_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query: await update.callback_query.answer()
    await update.effective_message.reply_text("📅 **Date batayein?** (DD-MM-YYYY)\ne.g., `01-01-2026`")
    return ASK_DATE

async def receive_date(u, c):
    try:
        datetime.strptime(u.message.text, "%d-%m-%Y")
        c.user_data['date'] = u.message.text
        await u.message.reply_text("📝 **Topic Name?**")
        return ASK_TOPIC
    except: await u.message.reply_text("❌ Wrong Format!"); return ASK_DATE

async def receive_topic(u, c):
    c.user_data['topic'] = u.message.text
    await u.message.reply_text("🔗 **Quiz Link?**")
    return ASK_LINK

async def receive_link(u, c):
    add_test_to_schedule(c.user_data['date'], c.user_data['topic'], u.message.text)
    await u.message.reply_text(f"✅ **Scheduled!** Date: {c.user_data['date']}")
    return ConversationHandler.END

async def cancel(u, c): await u.message.reply_text("❌ Cancelled"); return ConversationHandler.END

# --- 5. BUTTON HANDLER (MAIN HUB) ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    # Navigation
    if data == 'back_home': await start(query, context)
    
    # Quick Start
    elif data == 'menu_quick_start': await quick_start_menu(update, context)
    elif data.startswith('fire_'): await fire_test(update, context)
    
    # Timer Menu
    elif data == 'menu_timer':
        btns = [
            [InlineKeyboardButton("🕓 4 PM", callback_data='time_16'), InlineKeyboardButton("🕔 5 PM", callback_data='time_17')],
            [InlineKeyboardButton("🕕 6 PM", callback_data='time_18'), InlineKeyboardButton("🕖 7 PM", callback_data='time_19')],
            [InlineKeyboardButton("🕗 8 PM", callback_data='time_20'), InlineKeyboardButton("🔙 Back", callback_data='back_home')]
        ]
        await query.message.edit_reply_markup(InlineKeyboardMarkup(btns))
        
    elif data.startswith('time_'):
        h = int(data.split('_')[1])
        update_time(f"{h}:00")
        q = context.application.job_queue
        for job in q.jobs(): 
            if job.callback.__name__ == 'job_send_test': job.schedule_removal()
        q.run_daily(job_send_test, time(hour=h, minute=0, tzinfo=pytz.timezone('Asia/Kolkata')))
        await query.message.edit_caption(f"✅ **Time Set:** {h}:00 PM", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data='back_home')]]))

    # Reset
    elif data == 'reset_flow': await query.message.reply_text("⚠️ **Reset Confirm?**\nType `/reset_all` to proceed.")
    
    # Status
    elif data == 'status_check':
        db = load_data()
        await query.message.reply_text(f"📊 **Status:**\nGroups: {len(db['groups'])}\nTests Scheduled: {len(db['schedule'])}")

    # Student Features
    elif data == 'my_profile': await show_profile(query, context)
    elif data == 'show_leaderboard': await show_leaderboard(query, context)

# --- HELPERS (Profile, Leaderboard, Attendance) ---
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

# --- OTHER COMMANDS ---
async def add_group(u, c):
    if u.effective_chat.type!="private": db=load_data(); db["groups"].append(u.effective_chat.id) if u.effective_chat.id not in db["groups"] else None; save_data(db); await u.message.reply_text("✅ Connected")
async def reset_all_cmd(u, c): 
    if u.effective_user.id==OWNER_ID: reset_bot_data(); await u.message.reply_text("☢️ Reset Done")
async def handle_forwarded_result(u, c):
    # (Auto Topper Logic same as before - Shortened here for brevity but fully working in previous version)
    pass # Use previous code for this function
