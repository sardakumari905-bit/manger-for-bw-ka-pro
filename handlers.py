from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from database import load_data, save_data, is_admin, update_time, add_test_to_schedule, set_daily_topper, reset_bot_data
from config import OWNER_ID, START_IMG
from datetime import datetime, time
import pytz
from jobs import job_send_test, execute_test_logic

# --- STATES (Saare Features ke liye) ---
ASK_DATE, ASK_TOPIC, ASK_LINK = range(3)
ASK_BROADCAST_MSG = 3
ASK_ADMIN_ID = 4
ASK_CUSTOM_TIME = 5
ASK_TOPPER_NAME = 6  # <--- New for Button Flow

# --- MAIN MENU (Admin vs Student) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # Ensure user in DB
    db = load_data()
    uid = str(user.id)
    if uid not in db["users"]:
        db["users"][uid] = {"name": user.first_name, "strikes": 0, "last_date": "", "total_attendance": 0}
        save_data(db)

    if is_admin(user.id):
        caption = f"👑 **BOSS MENU: {user.first_name}**\n👇 **Jo karna hai select karein:**"
        keyboard = [
            [InlineKeyboardButton("➕ Schedule Test", callback_data='add_link_flow'),
             InlineKeyboardButton("🚀 Quick Fire", callback_data='menu_quick_start')],
            
            [InlineKeyboardButton("📢 Broadcast", callback_data='broadcast_flow'),
             InlineKeyboardButton("🏆 Set Topper", callback_data='topper_flow')],
            
            [InlineKeyboardButton("⏰ Set Time", callback_data='time_flow'),
             InlineKeyboardButton("👮 Add Admin", callback_data='add_admin_flow')],
            
            [InlineKeyboardButton("📊 Status", callback_data='status_check'),
             InlineKeyboardButton("🗑️ RESET BOT", callback_data='reset_flow')]
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

# --- 1. SCHEDULE TEST FLOW ---
async def start_add_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query: await update.callback_query.answer()
    await update.effective_message.reply_text("📅 **Date batayein?** (DD-MM-YYYY)\ne.g., `01-01-2026`")
    return ASK_DATE

async def receive_date(u, c):
    try:
        datetime.strptime(u.message.text, "%d-%m-%Y")
        c.user_data['date'] = u.message.text
        await u.message.reply_text("📝 **Topic/Subject Name?**")
        return ASK_TOPIC
    except: await u.message.reply_text("❌ Galat Format! Aise likhein: `01-01-2026`"); return ASK_DATE

async def receive_topic(u, c):
    c.user_data['topic'] = u.message.text
    await u.message.reply_text("🔗 **Quiz Link Paste Karein:**")
    return ASK_LINK

async def receive_link(u, c):
    add_test_to_schedule(c.user_data['date'], c.user_data['topic'], u.message.text)
    await u.message.reply_text(f"✅ **Test Scheduled!**\n📅 {c.user_data['date']}\n📝 {c.user_data['topic']}")
    return ConversationHandler.END

# --- 2. SET TOPPER FLOW (NEW BUTTON) ---
async def start_set_topper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    await q.message.reply_text("🏆 **Topper ka Naam likhein:**")
    return ASK_TOPPER_NAME

async def receive_topper_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    set_daily_topper(name)
    await update.message.reply_text(f"✅ **Topper Updated:** {name}")
    return ConversationHandler.END

# --- 3. CUSTOM TIME FLOW ---
async def start_custom_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    await q.message.reply_text("⏰ **Test Time batayein?** (HH:MM)\nExample: `16:00` (4 PM)")
    return ASK_CUSTOM_TIME

async def receive_custom_time(u, c):
    try:
        h, m = map(int, u.message.text.split(":"))
        update_time(f"{h}:{m}")
        q = c.application.job_queue
        for j in q.jobs(): 
            if j.callback.__name__ == 'job_send_test': j.schedule_removal()
        q.run_daily(job_send_test, time(hour=h, minute=m, tzinfo=pytz.timezone('Asia/Kolkata')))
        await u.message.reply_text(f"✅ **New Time Set:** {h:02d}:{m:02d}")
    except: await u.message.reply_text("❌ Error! Example: `16:00`")
    return ConversationHandler.END

# --- 4. BROADCAST FLOW ---
async def start_broadcast_btn(u, c):
    q = u.callback_query; await q.answer(); await q.message.reply_text("📢 **Message Likhein (Sabko jayega):**"); return ASK_BROADCAST_MSG
async def send_broadcast_btn(u, c):
    msg = u.message.text; db = load_data(); count=0
    for gid in db["groups"]:
        try: await c.bot.send_message(gid, f"📢 **ANNOUNCEMENT:**\n\n{msg}"); count+=1
        except: pass
    await u.message.reply_text(f"✅ Sent to {count} groups."); return ConversationHandler.END

# --- 5. ADD ADMIN FLOW ---
async def start_add_admin_btn(u, c):
    q = u.callback_query; await q.answer(); await q.message.reply_text("👮 **New Admin ki ID bhejein:**"); return ASK_ADMIN_ID
async def receive_admin_id_btn(u, c):
    try:
        nid = int(u.message.text); db = load_data()
        if nid not in db["auth_users"]: db["auth_users"].append(nid); save_data(db)
        await u.message.reply_text(f"✅ Admin Added: {nid}")
    except: await u.message.reply_text("❌ Invalid ID (Number only)")
    return ConversationHandler.END

async def cancel(u, c): await u.message.reply_text("❌ Cancelled"); return ConversationHandler.END

# --- GENERAL BUTTON HANDLER ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == 'back_home': await start(query, context)
    
    # Quick Start
    elif data == 'menu_quick_start':
        db = load_data(); sch = db.get("schedule", {})
        if not sch: await query.message.reply_text("⚠️ Schedule Empty! Pehle Test add karein.")
        else:
            btns = [[InlineKeyboardButton(f"🚀 Fire: {d['day']}", callback_data=f"fire_{k}")] for k,d in sch.items()]
            btns.append([InlineKeyboardButton("🔙 Back", callback_data='back_home')])
            await query.message.edit_caption("👇 **Select Test to Start NOW:**", reply_markup=InlineKeyboardMarkup(btns))
            
    elif data.startswith('fire_'):
        dt = data.split("_")[1]; db = load_data(); t=db["schedule"].get(dt)
        if t: 
            await query.message.reply_text(f"🚀 **Launching {t['day']}!**")
            for gid in db["groups"]: context.application.create_task(execute_test_logic(context, gid, t))
    
    # Reset
    elif data == 'reset_flow': await query.message.reply_text("⚠️ **DANGER:** Sab delete ho jayega.\nType `/reset_all` to confirm.")
    
    # Status
    elif data == 'status_check': 
        db=load_data()
        txt = f"📊 **SYSTEM STATUS**\nConnected Groups: {len(db['groups'])}\nScheduled Tests: {len(db['schedule'])}\nTotal Students: {len(db['users'])}"
        await query.message.reply_text(txt)

# --- STUDENT HELPERS ---
async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    db = load_data(); uid = str(query.from_user.id)
    u = db["users"].get(uid, {"name": query.from_user.first_name, "total_attendance": 0, "strikes": 0})
    txt = f"👤 **PROFILE:** {u.get('name')}\n📊 Attendance: {u.get('total_attendance',0)}\n⚠️ Strikes: {u.get('strikes',0)}/3"
    await query.message.reply_text(txt)

async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    db = load_data()
    r = [(d.get('name', 'Unknown'), d.get('total_attendance',0)) for i,d in db['users'].items() if int(i)!=OWNER_ID]
    r.sort(key=lambda x:x[1], reverse=True)
    if not r: await query.message.reply_text("📭 Leaderboard Empty.")
    else:
        txt = "🏆 **TOP STUDENTS**\n" + "\n".join([f"{i+1}. {n} ({s})" for i,(n,s) in enumerate(r[:10])])
        await query.message.reply_text(txt)

# --- ATTENDANCE & AUTO ACTIONS ---
async def mark_attendance(u, c):
    uid=str(u.callback_query.from_user.id); today=str(datetime.now().date()); db=load_data()
    if uid not in db['users']: db['users'][uid]={'name':u.callback_query.from_user.first_name,'strikes':0,'last_date':'','total_attendance':0}
    if db['users'][uid]['last_date']!=today: 
        db['users'][uid]['last_date']=today; db['users'][uid]['total_attendance']+=1; save_data(db)
        await u.callback_query.answer("✅ Attendance Marked!", show_alert=True)
    else: await u.callback_query.answer("Already Present! ✅", show_alert=True)

async def add_group(u, c):
    if u.effective_chat.type!="private": db=load_data(); db["groups"].append(u.effective_chat.id) if u.effective_chat.id not in db["groups"] else None; save_data(db); await u.message.reply_text("✅ Group Connected!")

async def reset_all_cmd(u, c): 
    if u.effective_user.id==OWNER_ID: reset_bot_data(); await u.message.reply_text("☢️ **SYSTEM RESET SUCCESSFUL**")

async def handle_forwarded_result(u, c):
    if not is_admin(u.effective_user.id): return
    text = u.message.text or u.message.caption or ""
    if "🏆" in text or "Quiz" in text:
        db=load_data(); today=str(datetime.now().date()); lines=text.split('\n'); detected=[]; topper="Unknown"; count=0
        for line in lines:
            if "🥇" in line or "1." in line or (len(line)>0 and line[0].isdigit() and "." in line):
                try:
                    clean = line.replace("🥇","").split("-")[0].strip()
                    if "." in clean: clean=clean.split(".",1)[1].strip()
                    if clean: detected.append(clean); 
                    if topper=="Unknown": topper=clean
                except: pass
        if topper!="Unknown": set_daily_topper(topper)
        if detected:
            for uid, user in db["users"].items():
                if user.get("name") in detected and user["last_date"]!=today:
                    user["last_date"]=today; user["total_attendance"]+=1; count+=1
            save_data(db)
            await u.message.reply_text(f"✅ **Auto-Topper:** {topper}\n💾 **Auto-Attendance:** {count} Saved")
