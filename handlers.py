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
        caption = f"👑 **Boss: {user.first_name}**"
        keyboard = [
            [InlineKeyboardButton("➕ Schedule Test", callback_data='add_link_flow')],
            [InlineKeyboardButton("📢 Broadcast", callback_data='help_broadcast'),
             InlineKeyboardButton("⏰ Custom Time", callback_data='menu_timer')],
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
    await update.message.reply_photo(photo=START_IMG, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))

# --- 📢 BROADCAST & AUTH ---
async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args: await update.message.reply_text("❌ Msg likho: `/broadcast Hello`"); return
    msg = " ".join(context.args); db = load_data()
    sent = 0
    for gid in db["groups"]:
        try: await context.bot.send_message(gid, f"📢 **ANNOUNCEMENT:**\n\n{msg}"); sent+=1
        except: pass
    await update.message.reply_text(f"✅ Sent to {sent} groups.")

async def add_user_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return 
    if not context.args: await update.message.reply_text("❌ Usage: `/add_user 12345678`"); return
    try:
        nid = int(context.args[0]); db = load_data()
        if nid not in db["auth_users"]: db["auth_users"].append(nid); save_data(db)
        await update.message.reply_text(f"✅ Admin Added: {nid}")
    except: pass

# --- AUTO ATTENDANCE (Forward) ---
async def handle_forwarded_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    text = update.message.text or update.message.caption or ""
    
    # Logic to Detect Names from QuizBot
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
            await update.message.reply_text(f"✅ **Done!** Topper: {topper}, Auto-Attendance: {count}")

# --- OTHER COMMANDS ---
async def reset_all_cmd(u, c):
    if u.effective_user.id == OWNER_ID: reset_bot_data(); await u.message.reply_text("☢️ RESET DONE.")
async def set_custom_time_cmd(u, c):
    if is_admin(u.effective_user.id) and c.args:
        try:
            h,m = map(int, c.args[0].split(":")); update_time(f"{h}:{m}")
            q = c.application.job_queue; 
            for j in q.jobs(): 
                if j.callback.__name__=='job_send_test': j.schedule_removal()
            q.run_daily(job_send_test, time(hour=h, minute=m, tzinfo=pytz.timezone('Asia/Kolkata')))
            await u.message.reply_text(f"✅ Time Set: {h}:{m}")
        except: pass
async def set_topper_cmd(u, c): 
    if is_admin(u.effective_user.id) and c.args: set_daily_topper(" ".join(c.args)); await u.message.reply_text("✅ Set")
async def add_group(u, c):
    if u.effective_chat.type != "private": 
        db=load_data(); 
        if u.effective_chat.id not in db["groups"]: db["groups"].append(u.effective_chat.id); save_data(db); await u.message.reply_text("✅ Connected")

# --- CONVERSATION ---
async def start_add_link(u, c): 
    if not is_admin(u.effective_user.id): return ConversationHandler.END
    await u.message.reply_text("📅 Date (DD-MM-YYYY)?"); return ASK_DATE
async def receive_date(u, c): c.user_data['date']=u.message.text; await u.message.reply_text("📝 Topic?"); return ASK_TOPIC
async def receive_topic(u, c): c.user_data['topic']=u.message.text; await u.message.reply_text("🔗 Link?"); return ASK_LINK
async def receive_link(u, c): add_test_to_schedule(c.user_data['date'], c.user_data['topic'], u.message.text); await u.message.reply_text("✅ Scheduled"); return ConversationHandler.END
async def cancel(u, c): await u.message.reply_text("❌ Cancelled"); return ConversationHandler.END

# --- HELPERS ---
async def show_profile(u, c):
    db=load_data(); uid=str(u.effective_user.id)
    txt = f"👤 {db['users'][uid]['name']} | Att: {db['users'][uid].get('total_attendance',0)}" if uid in db['users'] else "❌ No Data"
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
    
async def button_handler(u, c):
    q=u.callback_query; await q.answer(); d=q.data
    if d=='add_link_flow': await q.message.reply_text("`/add_test`")
    elif d=='help_broadcast': await q.message.reply_text("`/broadcast Hello`")
    elif d=='help_admin': await q.message.reply_text("`/add_user 123456`")
    elif d=='menu_timer': await q.message.reply_text("`/custom_time 15:00`")
    elif d=='status_check': db=load_data(); await q.message.reply_text(f"📊 Scheduled: {len(db['schedule'])}")
    elif d=='my_profile': await show_profile(u, c)
    elif d=='show_leaderboard': await show_leaderboard(u, c)
    elif d=='reset_flow': await q.message.reply_text("Type `/reset_all`")
