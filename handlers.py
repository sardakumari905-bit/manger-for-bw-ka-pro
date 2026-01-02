# handlers.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime
from config import *
from database import *
from jobs import execute_test_logic 

# --- MENU ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = load_data()
    uid = str(user.id)
    if uid not in db["users"]:
        db["users"][uid] = {"name": user.first_name, "strikes": 0, "last_date": "", "total_attendance": 0}
        save_data(db)

    if is_admin(user.id):
        caption = f"👑 **PRO ADMIN PANEL**"
        keyboard = [
            [InlineKeyboardButton("➕ Schedule Test", callback_data='add_link_flow'),
             InlineKeyboardButton("🏆 Set Topper", callback_data='topper_flow')],
            [InlineKeyboardButton("🚀 Launch Now", callback_data='menu_quick_start'),
             InlineKeyboardButton("📢 Broadcast", callback_data='broadcast_flow')],
            [InlineKeyboardButton("📊 Status", callback_data='status_check'),
             InlineKeyboardButton("🗑️ RESET", callback_data='reset_flow')]
        ]
    else:
        # Student Menu showing Today's Toppers
        today = datetime.now(IST).strftime("%d-%m-%Y")
        toppers = get_todays_toppers(today)
        t_text = "\n".join([f"{s}: {n}" for s,n in toppers.items()]) if toppers else "Result Coming Soon..."
        
        caption = f"🤖 **Student Panel**\n\n🏆 **TODAY'S TOPPERS:**\n{t_text}"
        keyboard = [[InlineKeyboardButton("👤 My Profile", callback_data='my_profile')]]
    
    if update.callback_query:
        await update.callback_query.message.edit_caption(caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_photo(photo=START_IMG, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))

# --- AUTO ATTENDANCE (Forward Listener) ---
async def handle_forwarded_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    uid = str(update.effective_user.id)
    db = load_data()
    today = str(datetime.now(IST).date())

    if uid not in db['users']:
        db['users'][uid] = {'name': update.effective_user.first_name, 'strikes': 0, 'last_date': '', 'total_attendance': 0}

    if db['users'][uid]['last_date'] != today:
        db['users'][uid]['last_date'] = today
        db['users'][uid]['total_attendance'] += 1
        save_data(db)
        await update.message.reply_text(f"✅ **Attendance Marked!**\n(Verified via Forward)")
    else:
        await update.message.reply_text("⚠️ Attendance already marked hai.")

# --- NEW TOPPER FLOW (Subject Wise) ---
async def start_set_topper(u, c):
    if u.callback_query: await u.callback_query.answer()
    await u.effective_message.reply_text("📚 **Subject ka naam likhein:**\n(Example: Chemistry, Hindi, Physics)")
    return ASK_TOPPER_SUBJECT

async def receive_topper_subject(u, c):
    c.user_data['top_sub'] = u.message.text
    await u.message.reply_text(f"🏆 **{u.message.text} ka Topper kaun hai?**\n(Naam likhein)")
    return ASK_TOPPER_NAME

async def receive_topper_name(u, c):
    today = datetime.now(IST).strftime("%d-%m-%Y")
    set_subject_topper(today, c.user_data['top_sub'], u.message.text)
    await u.message.reply_text(f"✅ Saved!\n📅 {today}\n📚 {c.user_data['top_sub']}: {u.message.text}")
    return ConversationHandler.END

# --- SCHEDULE FLOW ---
async def start_add_link(u, c):
    if u.callback_query: await u.callback_query.answer()
    await u.effective_message.reply_text("📅 **Date?** (DD-MM-YYYY)\n(e.g., 02-01-2026)")
    return ASK_DATE

async def receive_date(u, c):
    try:
        datetime.strptime(u.message.text, "%d-%m-%Y")
        c.user_data['date'] = u.message.text
        await u.message.reply_text("📝 **Topic Name?**")
        return ASK_TOPIC
    except: await u.message.reply_text("❌ Wrong Format! Use: 02-01-2026"); return ASK_DATE

async def receive_topic(u, c):
    c.user_data['topic'] = u.message.text
    await u.message.reply_text("🔗 **Quiz Link?**")
    return ASK_LINK

async def receive_link(u, c):
    c.user_data['link'] = u.message.text
    await u.message.reply_text("⏰ **Time?** (HH:MM)\n(Railway Time, e.g. 14:00)")
    return ASK_TIME_SLOT

async def receive_time_slot(u, c):
    try:
        t_str = u.message.text.strip()
        datetime.strptime(t_str, "%H:%M")
        add_test_to_schedule(c.user_data['date'], c.user_data['topic'], c.user_data['link'], t_str)
        await u.message.reply_text("✅ **Test Scheduled!**")
        return ConversationHandler.END
    except: await u.message.reply_text("❌ Wrong Time! Use: 14:00"); return ASK_TIME_SLOT

# --- COMMON FUNCTIONS ---
async def start_broadcast_btn(u, c):
    if u.callback_query: await u.callback_query.answer()
    await u.effective_message.reply_text("📢 **Message bhejein:**")
    return ASK_BROADCAST_MSG

async def send_broadcast_btn(u, c):
    msg = u.message.text; db = load_data()
    for gid in db["groups"]:
        try: await c.bot.send_message(gid, f"📢 **NOTICE:**\n{msg}")
        except: pass
    await u.message.reply_text("✅ Sent."); return ConversationHandler.END

async def cancel(u, c): await u.message.reply_text("❌ Cancelled"); return ConversationHandler.END

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data == 'back_home': await start(update, context)
    
    elif data == 'menu_quick_start':
        db = load_data()
        today = datetime.now(IST).strftime("%d-%m-%Y")
        tests = db["schedule"].get(today, [])
        if not tests: await query.answer("No Tests Today", show_alert=True); return
        btns = []
        for i, t in enumerate(tests):
            btns.append([InlineKeyboardButton(f"🚀 Launch: {t['time']}", callback_data=f"fire_{today}_{i}")])
        btns.append([InlineKeyboardButton("🔙 Back", callback_data='back_home')])
        await query.message.edit_caption("Select Test:", reply_markup=InlineKeyboardMarkup(btns))

    elif data.startswith('fire_'):
        parts = data.split("_")
        date_str, idx = parts[1], int(parts[2])
        db = load_data()
        t = db["schedule"][date_str][idx]
        await query.answer("🚀 Launching...")
        for gid in db["groups"]: context.application.create_task(execute_test_logic(context, gid, t))

    elif data == 'attendance_done':
        uid=str(query.from_user.id); today=str(datetime.now(IST).date()); db=load_data()
        if uid not in db['users']: db['users'][uid]={'name':query.from_user.first_name,'last_date':'','total_attendance':0}
        
        if db['users'][uid]['last_date'] != today:
            db['users'][uid]['last_date'] = today
            db['users'][uid]['total_attendance'] += 1
            save_data(db)
            await query.answer("✅ Attendance Marked!", show_alert=True)
        else: await query.answer("⚠️ Already Marked Today!", show_alert=True)
        
    elif data == 'my_profile':
        uid = str(query.from_user.id); db = load_data()
        u_data = db["users"].get(uid, {"name": query.from_user.first_name, "total_attendance": 0, "strikes": 0})
        txt = f"👤 **{u_data['name']}**\n✅ Attendance: {u_data['total_attendance']}\n⚠️ Strikes: {u_data.get('strikes', 0)}"
        await query.answer(txt, show_alert=True)

    elif data == 'reset_flow': await query.answer("Type /reset_all to confirm", show_alert=True)
    elif data == 'status_check':
        db=load_data()
        await query.answer(f"Groups: {len(db['groups'])}\nStudents: {len(db['users'])}", show_alert=True)

async def add_group(u, c):
    db=load_data()
    chat_id = u.effective_chat.id
    if chat_id not in db["groups"]: 
        db["groups"].append(chat_id); save_data(db)
    await u.message.reply_text(f"✅ Group Added! ID: {chat_id}")

async def reset_all_cmd(u, c):
    if u.effective_user.id==OWNER_ID: 
        from database import reset_bot_data
        reset_bot_data()
        await u.message.reply_text("☢️ **ALL DATA RESET DONE!**")
