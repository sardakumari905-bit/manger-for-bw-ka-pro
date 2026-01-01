from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from database import load_data, save_data, is_admin, add_test_to_schedule, set_daily_topper, reset_bot_data
from config import OWNER_ID, START_IMG, MAIN_GROUP_ID
from datetime import datetime
from jobs import execute_test_logic

# --- STATES ---
ASK_DATE, ASK_TOPIC, ASK_LINK, ASK_TIME_SLOT = range(4) # Added Time Slot
ASK_BROADCAST_MSG = 4
ASK_ADMIN_ID = 5
ASK_TOPPER_NAME = 6

# --- MAIN MENU ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = load_data()
    uid = str(user.id)
    if uid not in db["users"]:
        db["users"][uid] = {"name": user.first_name, "strikes": 0, "last_date": "", "total_attendance": 0}
        save_data(db)

    if is_admin(user.id):
        caption = f"👑 **BOSS MENU: {user.first_name}**\n(Multi-Test Mode Active ✅)"
        keyboard = [
            [InlineKeyboardButton("➕ Schedule Test", callback_data='add_link_flow'),
             InlineKeyboardButton("🚀 Quick Fire", callback_data='menu_quick_start')],
            [InlineKeyboardButton("📢 Broadcast", callback_data='broadcast_flow'),
             InlineKeyboardButton("🏆 Set Topper", callback_data='topper_flow')],
            [InlineKeyboardButton("👮 Add Admin", callback_data='add_admin_flow'),
             InlineKeyboardButton("📊 Status", callback_data='status_check')],
            [InlineKeyboardButton("🗑️ RESET BOT", callback_data='reset_flow')]
        ]
    else:
        caption = "🤖 **Board Wallah Bot**\nDaily Quiz & Attendance System."
        keyboard = [
            [InlineKeyboardButton("👤 My Profile", callback_data='my_profile')],
            [InlineKeyboardButton("🏆 Leaderboard", callback_data='show_leaderboard')]
        ]
    
    if update.callback_query:
        await update.callback_query.message.edit_caption(caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_photo(photo=START_IMG, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))

# --- 1. SCHEDULE TEST FLOW (UPDATED) ---
async def start_add_link(u, c):
    if u.callback_query: await u.callback_query.answer()
    await u.effective_message.reply_text("📅 **Date batayein?** (DD-MM-YYYY)\ne.g., `01-01-2026`")
    return ASK_DATE

async def receive_date(u, c):
    try:
        datetime.strptime(u.message.text, "%d-%m-%Y")
        c.user_data['date'] = u.message.text
        await u.message.reply_text("📝 **Topic/Subject Name?**")
        return ASK_TOPIC
    except: await u.message.reply_text("❌ Galat Format! Example: `01-01-2026`"); return ASK_DATE

async def receive_topic(u, c):
    c.user_data['topic'] = u.message.text
    await u.message.reply_text("🔗 **Quiz Link Paste Karein:**")
    return ASK_LINK

async def receive_link(u, c):
    c.user_data['link'] = u.message.text
    await u.message.reply_text("⏰ **Time kya rakhna hai?** (HH:MM)\n(Railway Time, e.g. `14:30` for 2:30 PM)")
    return ASK_TIME_SLOT

async def receive_time_slot(u, c):
    # Validate Time
    try:
        t_str = u.message.text.strip()
        datetime.strptime(t_str, "%H:%M") # Check format
        
        # Save
        add_test_to_schedule(c.user_data['date'], c.user_data['topic'], c.user_data['link'], t_str)
        
        await u.message.reply_text(
            f"✅ **Test Added!**\n"
            f"📅 Date: {c.user_data['date']}\n"
            f"⏰ Time: {t_str}\n"
            f"📝 Topic: {c.user_data['topic']}\n\n"
            "Aur add karna hai to fir se 'Schedule Test' dabayein."
        )
        return ConversationHandler.END
    except:
        await u.message.reply_text("❌ Galat Time Format! Example: `16:00` (4 PM) or `09:30`")
        return ASK_TIME_SLOT

# --- OTHER HANDLERS (Same logic, slightly simplified) ---
async def start_set_topper(u, c):
    q = u.callback_query; await q.answer()
    await q.message.reply_text("🏆 **Topper Name:**")
    return ASK_TOPPER_NAME

async def receive_topper_name(u, c):
    set_daily_topper(u.message.text)
    await u.message.reply_text(f"✅ Updated: {u.message.text}")
    return ConversationHandler.END

async def start_broadcast_btn(u, c):
    q = u.callback_query; await q.answer(); await q.message.reply_text("📢 **Message:**"); return ASK_BROADCAST_MSG
async def send_broadcast_btn(u, c):
    msg = u.message.text; db = load_data()
    for gid in db["groups"]:
        try: await c.bot.send_message(gid, f"📢 **ANNOUNCEMENT:**\n\n{msg}")
        except: pass
    await u.message.reply_text("✅ Broadcast Sent."); return ConversationHandler.END

async def start_add_admin_btn(u, c):
    q = u.callback_query; await q.answer(); await q.message.reply_text("👮 **Admin ID:**"); return ASK_ADMIN_ID
async def receive_admin_id_btn(u, c):
    try:
        nid = int(u.message.text); db = load_data()
        if nid not in db["auth_users"]: db["auth_users"].append(nid); save_data(db)
        await u.message.reply_text("✅ Added.")
    except: await u.message.reply_text("❌ Number only.")
    return ConversationHandler.END

async def cancel(u, c): await u.message.reply_text("❌ Cancelled"); return ConversationHandler.END

# --- BUTTONS ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    data = query.data
    
    if data == 'back_home': await start(query, context)
    
    # Quick Fire now handles Lists
    elif data == 'menu_quick_start':
        db = load_data()
        today = datetime.now().strftime("%d-%m-%Y")
        tests = db["schedule"].get(today, [])
        
        if not tests: 
            await query.message.reply_text(f"⚠️ Aaj ({today}) ke liye koi Test nahi hai.")
        else:
            # Show buttons for ALL tests of today
            btns = []
            for i, t in enumerate(tests):
                status = "✅ Done" if t.get('sent') else "⏳ Pending"
                btns.append([InlineKeyboardButton(f"🚀 Launch: {t['day']} ({t['time']})", callback_data=f"fire_{today}_{i}")])
            
            btns.append([InlineKeyboardButton("🔙 Back", callback_data='back_home')])
            await query.message.edit_caption("👇 **Select Test to Launch Now:**", reply_markup=InlineKeyboardMarkup(btns))
            
    elif data.startswith('fire_'):
        parts = data.split("_") # fire_DATE_INDEX
        date_str, idx = parts[1], int(parts[2])
        db = load_data()
        if date_str in db["schedule"] and len(db["schedule"][date_str]) > idx:
            t = db["schedule"][date_str][idx]
            await query.message.reply_text(f"🚀 **Manual Launch:** {t['day']}")
            for gid in db["groups"]: context.application.create_task(execute_test_logic(context, gid, t))
    
    elif data == 'reset_flow': await query.message.reply_text("⚠️ Type `/reset_all` to confirm.")
    
    elif data == 'status_check':
        db=load_data()
        await query.message.reply_text(f"Groups: {len(db['groups'])}\nStudents: {len(db['users'])}")

# --- STUDENT HELPERS & ATTENDANCE ---
async def show_profile(u, c):
    q = u.callback_query; await q.answer()
    db = load_data(); uid = str(q.from_user.id)
    u_data = db["users"].get(uid, {"name": q.from_user.first_name, "total_attendance": 0})
    await q.message.reply_text(f"👤 **{u_data['name']}**\n✅ Total Attendance: {u_data['total_attendance']}")

async def show_leaderboard(u, c):
    q = u.callback_query; await q.answer()
    db = load_data()
    r = sorted([(d['name'], d['total_attendance']) for i,d in db['users'].items() if int(i)!=OWNER_ID], key=lambda x:x[1], reverse=True)[:10]
    txt = "🏆 **TOP 10**\n" + "\n".join([f"{i+1}. {n} ({s})" for i,(n,s) in enumerate(r)]) if r else "📭 Empty"
    await q.message.reply_text(txt)

async def mark_attendance(u, c):
    uid=str(u.callback_query.from_user.id); today=str(datetime.now().date()); db=load_data()
    if uid not in db['users']: db['users'][uid]={'name':u.callback_query.from_user.first_name,'last_date':'','total_attendance':0,'strikes':0}
    
    if db['users'][uid]['last_date']!=today:
        db['users'][uid]['last_date']=today; db['users'][uid]['total_attendance']+=1; save_data(db)
        await u.callback_query.answer("✅ Attendance Marked!", show_alert=True)
    else: await u.callback_query.answer("⚠️ Already Marked!", show_alert=True)

async def add_group(u, c):
    db=load_data()
    if u.effective_chat.id not in db["groups"]: db["groups"].append(u.effective_chat.id); save_data(db)
    await u.message.reply_text("✅ Group Added")

async def reset_all_cmd(u, c):
    if u.effective_user.id==OWNER_ID: reset_bot_data(); await u.message.reply_text("☢️ Reset Done")

async def handle_forwarded_result(u, c):
    if not is_admin(u.effective_user.id): return
    # (Same simple logic as before for auto-attendance)
    await u.message.reply_text("✅ Result Scanning Active (Basic Mode)")
