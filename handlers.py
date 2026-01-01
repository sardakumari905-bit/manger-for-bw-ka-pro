# handlers.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from database import load_data, save_data, is_admin, update_time, add_test_to_schedule, set_daily_topper, reset_bot_data
from config import OWNER_ID, START_IMG, MAIN_GROUP_ID
from datetime import datetime, time
import pytz
from jobs import job_send_test, execute_test_logic

# --- STATES ---
ASK_DATE, ASK_TOPIC, ASK_LINK = range(3)
ASK_BROADCAST_MSG = 3
ASK_ADMIN_ID = 4
ASK_CUSTOM_TIME = 5
ASK_TOPPER_NAME = 6

# --- MAIN MENU ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = load_data()
    uid = str(user.id)
    
    # User ko DB me add karein
    if uid not in db["users"]:
        db["users"][uid] = {"name": user.first_name, "strikes": 0, "last_date": "", "total_attendance": 0}
        save_data(db)

    if is_admin(user.id):
        caption = f"👑 **BOSS MENU: {user.first_name}**\n📍 **Main Group Connected:** ✅"
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

# --- BUTTON FLOWS (Same as before, simplified) ---
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
    except: await u.message.reply_text("❌ Galat Format! Aise likhein: `01-01-2026`"); return ASK_DATE

async def receive_topic(u, c):
    c.user_data['topic'] = u.message.text
    await u.message.reply_text("🔗 **Quiz Link Paste Karein:**")
    return ASK_LINK

async def receive_link(u, c):
    add_test_to_schedule(c.user_data['date'], c.user_data['topic'], u.message.text)
    await u.message.reply_text(f"✅ **Test Scheduled!**\n📅 {c.user_data['date']}\n📝 {c.user_data['topic']}")
    return ConversationHandler.END

async def start_set_topper(u, c):
    q = u.callback_query; await q.answer()
    await q.message.reply_text("🏆 **Topper ka Naam likhein:**")
    return ASK_TOPPER_NAME

async def receive_topper_name(u, c):
    set_daily_topper(u.message.text)
    await u.message.reply_text(f"✅ **Topper Updated:** {u.message.text}")
    return ConversationHandler.END

async def start_custom_time(u, c):
    q = u.callback_query; await q.answer()
    await q.message.reply_text("⏰ **Time (HH:MM)?** ex: `16:00`")
    return ASK_CUSTOM_TIME

async def receive_custom_time(u, c):
    try:
        h, m = map(int, u.message.text.split(":"))
        update_time(f"{h}:{m}")
        # Job Reschedule Logic Main.py restart pe handle hoga ya yahan dynamic reload karein
        await u.message.reply_text(f"✅ **Time Set:** {h:02d}:{m:02d}\n(Bot restart recommended for instant effect)")
    except: await u.message.reply_text("❌ Error! Example: `16:00`")
    return ConversationHandler.END

async def start_broadcast_btn(u, c):
    q = u.callback_query; await q.answer(); await q.message.reply_text("📢 **Message Likhein:**"); return ASK_BROADCAST_MSG
async def send_broadcast_btn(u, c):
    msg = u.message.text; db = load_data(); count=0
    for gid in db["groups"]:
        try: await c.bot.send_message(gid, f"📢 **ANNOUNCEMENT:**\n\n{msg}"); count+=1
        except: pass
    await u.message.reply_text(f"✅ Sent to {count} groups."); return ConversationHandler.END

async def start_add_admin_btn(u, c):
    q = u.callback_query; await q.answer(); await q.message.reply_text("👮 **New Admin ID:**"); return ASK_ADMIN_ID
async def receive_admin_id_btn(u, c):
    try:
        nid = int(u.message.text); db = load_data()
        if nid not in db["auth_users"]: db["auth_users"].append(nid); save_data(db)
        await u.message.reply_text(f"✅ Admin Added: {nid}")
    except: await u.message.reply_text("❌ Number only")
    return ConversationHandler.END

async def cancel(u, c): await u.message.reply_text("❌ Cancelled"); return ConversationHandler.END

# --- GENERAL BUTTON HANDLER ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == 'back_home': await start(query, context)
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
            await query.message.reply_text(f"🚀 **Launching {t['day']}!**")
            for gid in db["groups"]: context.application.create_task(execute_test_logic(context, gid, t))
    
    elif data == 'reset_flow': await query.message.reply_text("⚠️ **DANGER:** Type `/reset_all` to confirm.")
    elif data == 'status_check': 
        db=load_data()
        txt = f"📊 **STATUS**\nGroups: {len(db['groups'])}\nStudents: {len(db['users'])}\nMain Group Connected: {'Yes' if MAIN_GROUP_ID in db['groups'] else 'No'}"
        await query.message.reply_text(txt)

# --- STUDENT HELPERS ---
async def show_profile(u, c):
    q = u.callback_query; await q.answer()
    db = load_data(); uid = str(q.from_user.id)
    user = db["users"].get(uid, {"name": q.from_user.first_name, "total_attendance": 0})
    await q.message.reply_text(f"👤 **{user['name']}**\n✅ Attendance: {user['total_attendance']}")

async def show_leaderboard(u, c):
    q = u.callback_query; await q.answer()
    db = load_data()
    r = [(d.get('name', 'Unknown'), d.get('total_attendance',0)) for i,d in db['users'].items() if int(i)!=OWNER_ID]
    r.sort(key=lambda x:x[1], reverse=True)
    if not r: await q.message.reply_text("📭 Leaderboard Empty.")
    else:
        txt = "🏆 **TOP 10 STUDENTS**\n" + "\n".join([f"{i+1}. {n} ({s})" for i,(n,s) in enumerate(r[:10])])
        await q.message.reply_text(txt)

# --- ATTENDANCE & AUTO ACTIONS ---
async def mark_attendance(u, c):
    uid=str(u.callback_query.from_user.id)
    today=str(datetime.now().date())
    db=load_data()
    
    if uid not in db['users']:
        db['users'][uid] = {'name': u.callback_query.from_user.first_name, 'strikes': 0, 'last_date': '', 'total_attendance': 0}
    
    if db['users'][uid]['last_date'] != today:
        db['users'][uid]['last_date'] = today
        db['users'][uid]['total_attendance'] += 1
        save_data(db)
        await u.callback_query.answer(f"✅ Present Sir! (Day: {today})", show_alert=True)
    else:
        await u.callback_query.answer("⚠️ Aapki attendance lag chuki hai!", show_alert=True)

async def add_group(u, c):
    if u.effective_chat.type!="private":
        db=load_data()
        if u.effective_chat.id not in db["groups"]:
            db["groups"].append(u.effective_chat.id)
            save_data(db)
        await u.message.reply_text("✅ Group Connected!")

async def reset_all_cmd(u, c): 
    if u.effective_user.id==OWNER_ID: reset_bot_data(); await u.message.reply_text("☢️ **SYSTEM RESET SUCCESSFUL**")

# --- IMPROVED AUTO TOPPER/ATTENDANCE PARSER ---
async def handle_forwarded_result(u, c):
    if not is_admin(u.effective_user.id): return
    text = u.message.text or u.message.caption or ""
    
    # Common keywords in quiz results
    if "🏆" in text or "Quiz" in text or "board" in text.lower():
        db = load_data()
        today = str(datetime.now().date())
        lines = text.split('\n')
        detected_names = []
        topper = "Unknown"
        count = 0
        
        for line in lines:
            clean_name = None
            # Logic: "1. Name - Score" or "🥇 Name"
            if "🥇" in line:
                # Format: 🥇 Neeraj - 100%
                clean_name = line.split("🥇")[1].split("-")[0].strip()
            elif len(line) > 0 and line[0].isdigit() and "." in line:
                # Format: 1. Neeraj - 20 sec
                parts = line.split(".", 1)
                if len(parts) > 1:
                    clean_name = parts[1].split("-")[0].strip()
            
            if clean_name:
                detected_names.append(clean_name)
                if topper == "Unknown": topper = clean_name # First name is topper
        
        if topper != "Unknown":
            set_daily_topper(topper)
            
        # Match names with Database (Soft Match)
        if detected_names:
            for d_name in detected_names:
                for uid, user in db["users"].items():
                    # Check if DB name is inside Result name (or vice versa)
                    # Case insensitive check
                    u_name = user.get("name", "").lower()
                    r_name = d_name.lower()
                    
                    if (u_name in r_name or r_name in u_name) and len(u_name) > 2:
                        if user["last_date"] != today:
                            user["last_date"] = today
                            user["total_attendance"] += 1
                            count += 1
            save_data(db)
            await u.message.reply_text(f"✅ **Auto-Topper:** {topper}\n💾 **Auto-Attendance:** {count} Students matched.")
        else:
            await u.message.reply_text("⚠️ Result pattern recognize nahi hua. 'Set Topper' manual use karein.")
