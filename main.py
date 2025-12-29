import logging
import asyncio
import nest_asyncio
from datetime import time
import pytz
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    ConversationHandler, MessageHandler, filters, ContextTypes
)

nest_asyncio.apply()

from config import BOT_TOKEN
from database import load_data
from handlers import (
    start, add_group, reset_all_cmd, button_handler, mark_attendance,
    start_add_link, receive_date, receive_topic, receive_link, cancel, set_topper_cmd, add_user_cmd, broadcast_cmd,
    show_leaderboard, show_profile, handle_forwarded_result, ASK_DATE, ASK_TOPIC, ASK_LINK
)
from jobs import job_send_test, job_nightly_report, job_morning_motivation

app_web = Flask('')
@app_web.route('/')
def home(): return "Bot Live 🟢"
def run_http(): app_web.run(host='0.0.0.0', port=8080)
def keep_alive(): t = Thread(target=run_http); t.start()

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

async def post_init(app):
    await app.bot.set_my_commands([
        ("start", "Main Menu"),
        ("add_test", "Schedule"),
        ("broadcast", "Announcement"),
        ("profile", "My Report"),
        ("leaderboard", "Top Students")
    ])
    
    db = load_data()
    t_str = db["settings"].get("time", "18:00")
    h, m = map(int, t_str.split(":"))
    
    app.job_queue.run_daily(job_send_test, time(hour=h, minute=m, tzinfo=pytz.timezone('Asia/Kolkata')))
    app.job_queue.run_daily(job_nightly_report, time(hour=21, minute=30, tzinfo=pytz.timezone('Asia/Kolkata')))
    app.job_queue.run_daily(job_morning_motivation, time(hour=5, minute=0, tzinfo=pytz.timezone('Asia/Kolkata')))
    
    print("✅ Bot Started (v13.0 - Buttons Fixed)")

if __name__ == "__main__":
    keep_alive()
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add_group", add_group))
    app.add_handler(CommandHandler("reset_all", reset_all_cmd))
    app.add_handler(CommandHandler("profile", show_profile))
    app.add_handler(CommandHandler("leaderboard", show_leaderboard))
    app.add_handler(CommandHandler("set_topper", set_topper_cmd))
    app.add_handler(CommandHandler("add_user", add_user_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))

    # Forward Handler
    app.add_handler(MessageHandler(filters.FORWARDED & filters.TEXT, handle_forwarded_result))

    # Conversation Handler (ADD TEST)
    # Note: 'add_link_flow' pattern yahan add kiya hai taaki BUTTON kaam kare
    conv = ConversationHandler(
        entry_points=[
            CommandHandler("add_test", start_add_link),
            CallbackQueryHandler(start_add_link, pattern='^add_link_flow$')
        ],
        states={
            ASK_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_date)],
            ASK_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_topic)],
            ASK_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_link)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(conv)

    # General Button Handler
    app.add_handler(CallbackQueryHandler(button_handler, pattern='^menu_|time_|status_|show_|my_|reset_|help_|back_'))
    app.add_handler(CallbackQueryHandler(mark_attendance, pattern='attendance_done'))

    app.run_polling()
