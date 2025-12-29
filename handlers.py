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
        caption = f"👑 **Boss: {user.first_name}**\n👇 **HYBRID CONTROL PANEL:**"
        keyboard = [
            [InlineKeyboardButton("🚀 QUICK START", callback_data='menu_quick_start')],
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

# --- 1. DIRECT TEXT COMMANDS (Jo aap maang rahe the) ---

async def broadcast_text_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("❌ Usage: `/broadcast Hello Students`")
        return
    
    msg = " ".join(context.args)
    db = load_data()
    count = 0
    for gid in db["groups"]:
        try:
            await context.bot.send_message(gid, f"📢 **ANNOUNCEMENT:**\n\n{msg}")
            count += 1
        except: pass
    await update.message.reply_text(f"✅ **Sent via Command!** Group Count: {count}")

async def add_user_text_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    if not context.args:
        await update.message.reply_text("❌ Usage: `/add_user 12345678`")
        return
    try:
        nid = int(context.args[0])
        db = load_data()
        if nid not in db["auth_users"]:
            db["auth_users"].append(nid)
            save_data(db)
            await update.message.reply_text(f"✅ **Admin Added:** {nid}")
    except: pass

async def custom_time_text_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args: await update.message.reply_text("❌ Usage: `/custom_time 15:00`"); return
    try:
        h, m = map(int, context.args[0].split(":"))
        update_time(f"{h}:{m}")
        q = context.application.job_queue
        for job in q.jobs(): 
            if job.callback.__name__ == 'job_send_test': job.schedule_removal()
        q.run_daily(job_send_test, time(hour=h, minute=0, tzinfo=pytz.timezone('Asia/Kolkata')))
        await update.message.reply_text(f"✅ Time Set: {h}:{m}")
    except: pass

async def reset_all_text_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == OWNER_ID:
        reset_bot_data()
        await update.message.reply_text("☢️ **RESET DONE (via Command)**")

# --- 2. BUTTON FLOWS (Conversations for Menu) ---

# Broadcast Button Logic
async def start_broadcast_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📢 **Message type karein:**")
    return ASK_BROADCAST_MSG

async def send_broadcast_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    db = load_data()
    count = 0
    for gid in db["groups"]:
        try: await context.bot.send_message(gid, f"📢 **ANNOUNCEMENT:**\n\n{msg}"); count += 1
        except: pass
    await update.message.reply_text(f"✅ Broadcast Sent to {count} groups.")
    return ConversationHandler.END

# Add Admin Button Logic
async def start_add_admin_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("👮 **User ID bhejein:**")
    return ASK_ADMIN_ID

async def receive_admin_id_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        nid = int(update.message.text)
        db = load_data()
        if nid not in db["auth_users"]: db["auth_users"].append(nid); save_data(db)
        await update.message.reply_text(f"✅ Admin Added: {nid}")
    except: await update.message.reply_text("❌ Invalid ID")
    return ConversationHandler.END

# Schedule Test Logic (Works for BOTH Command & Button)
async def start_add_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query: await update.callback_query.answer()
    await update.effective_message.reply_text("📅 **Date?** (DD-MM-YYYY)\ne.g., `01-01-2026`")
    return ASK_DATE

async def receive_date(u, c):
    try:
        datetime.strptime(u.message.text, "%d-%m-%Y")
        c.user_data['date'] = u.message.text
        await u.message.reply_text("📝 **Topic?**")
        return ASK_TOPIC
    except: await u.message.reply_text("❌ Wrong Format!"); return ASK_DATE

async def receive_topic(u, c):
    c.user_data['topic'] = u.message.text
    await u.message.reply_text("🔗 **Link?**")
    return ASK_LINK

async def receive_link(u, c):
    add_test_to_schedule(c.user_data['date'], c.user_data['topic'], u.message.text)
    await u.message.reply_text(f"✅ **Scheduled!** {c.user_data['date']}")
    return ConversationHandler.END

async def cancel(u, c): await u.message.reply_text("❌ Cancelled"); return ConversationHandler.END

# --- 3. GENERAL BUTTON HANDLER ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == 'back_home': await start(query, context)
    
    # Quick Start
    elif data == 'menu_quick_start':
        db = load_data(); sch = db.get("schedule", {})
        if not sch: await query.message.reply_text("⚠️ Schedule Empty!")
        else:
            btns = [[InlineKeyboardButton(f"🚀 Fire: {d['day']}", callback_data=f"fire_{k}")] for k,d in sch.items()]
            btns.append([InlineKeyboardButton("🔙 Back", callback_data='back_home')])
            await query.message.edit_caption("👇 **Select Test:**", reply_markup=InlineKeyboardMarkup(btns))
            
    elif data.startswith('fire_'):
        dt = data.split("_")[1]; db = load_data(); t=db["schedule"].get(dt)
        if t: 
            await query.message.reply_text(f"🚀 **Firing {t['day']}!**")
            for gid in db["groups"]: context.application.create_task(execute_test_logic(context, gid, t))
            
    # Timer
    elif data == 'menu_timer':
        btns = [
            [InlineKeyboardButton("🕓 4 PM", callback_data='time_16'), InlineKeyboardButton("🕕 6 PM", callback_data='time_18')],
            [InlineKeyboardButton("🕗 8 PM", callback_data='time_20'), InlineKeyboardButton("🔙 Back", callback_data='back_home')]
        ]
        await query.message.edit_reply_markup(InlineKeyboardMarkup(btns))
    elif data.startswith('time_'):
        h = int(data.split('_')[1]); update_time(f"{h}:00")
        q = context.application.job_queue
        for j in q.jobs(): 
            if j.callback.__name__ == 'job_send_test': j.schedule_removal()
        q.run_daily(job_send_test, time(hour=h, minute=0, tzinfo=pytz.timezone('Asia/Kolkata')))
        await query.message.edit_caption(f"✅ Time: {h}:00 PM", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data='back_home')]]))

    # Reset
    elif data == 'reset_flow': await query.message.reply_text("⚠️ Type `/reset_all` to confirm.")
    
    # Status
    elif data == 'status_check': db=load_data(); await query.message.reply_text(f"📊 Scheduled: {len(db['schedule'])}")
    elif data == 'my_profile': await show_profile(query, context)
    elif data == 'show_leaderboard': await show_leaderboard(query, context)

# --- HELPERS ---
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

async def add_group(u, c):
    if u.effective_chat.type!="private": db=load_data(); db["groups"].append(u.effective_chat.id) if u.effective_chat.id not in db["groups"] else None; save_data(db); await u.message.reply_text("✅ Connected")

async def set_topper_cmd(u, c):
    if is_admin(u.effective_user.id) and c.args: set_daily_topper(" ".join(c.args)); await u.message.reply_text("✅ Set")

async def handle_forwarded_result(u, c):
    # Auto Topper Logic (Same as before)
    # ... (Keeping logic same) ...
    pass
