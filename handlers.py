from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime
from config import *
from database import *
from jobs import execute_test_logic 

# --- START / MENU ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = load_data()
    uid = str(user.id)
    
    if uid not in db["users"]:
        db["users"][uid] = {"name": user.first_name, "strikes": 0, "last_date": "", "total_attendance": 0}
        save_data(db)

    if is_admin(user.id):
        caption = f"👑 **ADMIN MENU**"
        keyboard = [
            [InlineKeyboardButton("➕ Schedule", callback_data='add_link_flow'),
             InlineKeyboardButton("🚀 Quick Fire", callback_data='menu_quick_start')],
            [InlineKeyboardButton("📢 Broadcast", callback_data='broadcast_flow'),
             InlineKeyboardButton("📊 Status", callback_data='status_check')],
            [InlineKeyboardButton("🗑️ RESET", callback_data='reset_flow')]
        ]
    else:
        caption = "🤖 **Student Menu**"
        keyboard = [[InlineKeyboardButton("👤 My Profile", callback_data='my_profile')]]
    
    if update.callback_query:
        await update.callback_query.message.edit_caption(caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_photo(photo=START_IMG, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))

# --- FLOWS ---
async def start_add_link(u, c):
    if u.callback_query: await u.callback_query.answer()
    await u.effective_message.reply_text("📅 Date? (DD-MM-YYYY)")
    return ASK_DATE

async def receive_date(u, c):
    try:
        datetime.strptime(u.message.text, "%d-%m-%Y")
        c.user_data['date'] = u.message.text
        await u.message.reply_text("📝 Topic?")
        return ASK_TOPIC
    except: await u.message.reply_text("❌ Example: 02-01-2026"); return ASK_DATE

async def receive_topic(u, c):
    c.user_data['topic'] = u.message.text
    await u.message.reply_text("🔗 Link?")
    return ASK_LINK

async def receive_link(u, c):
    c.user_data['link'] = u.message.text
    await u.message.reply_text("⏰ Time? (HH:MM) Railway Format")
    return ASK_TIME_SLOT

async def receive_time_slot(u, c):
    try:
        t_str = u.message.text.strip()
        datetime.strptime(t_str, "%H:%M")
        add_test_to_schedule(c.user_data['date'], c.user_data['topic'], c.user_data['link'], t_str)
        await u.message.reply_text("✅ Scheduled!")
        return ConversationHandler.END
    except: await u.message.reply_text("❌ Example: 14:30"); return ASK_TIME_SLOT

async def cancel(u, c): await u.message.reply_text("❌ Cancelled"); return ConversationHandler.END

# --- BUTTONS ---
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
            await query.answer("✅ Marked!", show_alert=True)
        else: await query.answer("⚠️ Already Done!", show_alert=True)

# (Add Broadcast & other simple handlers here as per previous code logic)
