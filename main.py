import logging
import asyncio
import nest_asyncio # <--- IMPORT THIS
from datetime import time
import pytz
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    ConversationHandler, MessageHandler, filters, ContextTypes
)

# Fix for Render Loop Issues (Button Jam Fix)
nest_asyncio.apply() # <--- JAADUI LINE (Ye jaruri h)

from config import BOT_TOKEN
from database import load_data
from handlers import (
    start, add_group, set_custom_time_cmd, reset_all_cmd, button_handler, mark_attendance,
    start_add_link, receive_date, receive_topic, receive_link, cancel, set_topper_cmd, add_user_cmd, broadcast_cmd,
    show_leaderboard, show_profile, handle_forwarded_result, ASK_DATE, ASK_TOPIC, ASK_LINK
)
from jobs import job_send_test, job_nightly_report, job_morning_motivation

# --- FLASK SERVER (Keep Alive) ---
app_web = Flask('')
@app_web.route('/')
def home(): return "Bot is Running Smoothly 🟢"
def run_http(): app_web.run(host='0.0.0.0', port=8080)
def keep_alive(): t = Thread(target=run_http); t.start()

# --- LOGGING (Error dekhne ke liye) ---
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- ERROR HANDLER (Agar bot fasega to batayega) ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    # Agar user ne kuch click kiya aur error aaya, to usko batao
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(f"⚠️ **Error:** Bot ko kuch dikkat aayi hai.\nError: `{context.error}`")
        except: pass

async def post_init(app):
    await app.bot.set_my_commands([
        ("start", "Main Menu"),
        ("add_test", "Schedule Quiz"),
        ("broadcast", "Announcement"),
        ("add_user", "Make Admin"),
        ("profile", "My Report"),
        ("leaderboard", "Toppers List"),
        ("status", "System Status")
    ])
    
    db = load_data()
    t_str = db["settings"].get("time", "18:00")
    h, m = map(int, t_str.split(":"))
    
    # JOBS
    app.job_queue.run_daily(job_send_test, time(hour=h, minute=m, tzinfo=pytz.timezone('Asia/Kolkata')))
    app.job_queue.run_daily(job_nightly_report, time(hour=21, minute=30, tzinfo=pytz.timezone('Asia/Kolkata')))
    app.job_queue.run_daily(job_morning_motivation, time(hour=5, minute=0, tzinfo=pytz.timezone('Asia/Kolkata')))
    
    print("✅ Ultra Pro Bot (Fixed Version) Started!")

if __name__ == "__main__":
    keep_alive()
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add_group", add_group))
    app.add_handler(CommandHandler("custom_time", set_custom_time_cmd))
    app.add_handler(CommandHandler("reset_all", reset_all_cmd))
    app.add_handler(CommandHandler("profile", show_profile))
    app.add_handler(CommandHandler("leaderboard", show_leaderboard))
    app.add_handler(CommandHandler("set_topper", set_topper_cmd))
    app.add_handler(CommandHandler("add_user", add_user_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))

    # Forward Handler
    app.add_handler(MessageHandler(filters.FORWARDED & filters.TEXT, handle_forwarded_result))

    # Conversation Handler
    conv = ConversationHandler(
        entry_points=[CommandHandler("add_test", start_add_link)],
        states={
            ASK_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_date)],
            ASK_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_topic)],
            ASK_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_link)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(conv)

    # Callbacks (Buttons)
    app.add_handler(CallbackQueryHandler(button_handler, pattern='^menu_|add_link_|status_|show_|my_|reset_|help_'))
    app.add_handler(CallbackQueryHandler(mark_attendance, pattern='attendance_done'))

    # Error Handler Register
    app.add_error_handler(error_handler)

    app.run_polling()
