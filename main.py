import logging
import asyncio
from datetime import time
import pytz
from threading import Thread
from flask import Flask
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters

from config import BOT_TOKEN
from database import load_data
from handlers import (
    start, add_group, status, broadcast_cmd, button_handler, mark_attendance,
    start_add_link, receive_day, receive_link, cancel, set_topper_cmd, add_user_cmd, 
    handle_forwarded_result, show_leaderboard, ASK_DAY, ASK_LINK
)
from jobs import job_send_test, job_nightly_report, job_morning_motivation # <--- Added job

app_web = Flask('')
@app_web.route('/')
def home(): return "Final Bot Live 🟢"
def run_http(): app_web.run(host='0.0.0.0', port=8080)
def keep_alive(): t = Thread(target=run_http); t.start()

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

async def post_init(app):
    await app.bot.set_my_commands([
        ("start", "Menu"),
        ("leaderboard", "Top Students"),
        ("add_group", "Connect"),
        ("broadcast", "Announcement"),
        ("add_link", "Add Quiz"),
        ("status", "Reports")
    ])
    
    db = load_data()
    t = db["settings"]["time"].split(":")
    
    # 1. Daily Test Job
    app.job_queue.run_daily(job_send_test, time(hour=int(t[0]), minute=int(t[1]), tzinfo=pytz.timezone('Asia/Kolkata')))
    
    # 2. Nightly Report (9:30 PM)
    app.job_queue.run_daily(job_nightly_report, time(hour=21, minute=30, tzinfo=pytz.timezone('Asia/Kolkata')))
    
    # 3. Morning Motivation (5:00 AM) <--- NEW
    app.job_queue.run_daily(job_morning_motivation, time(hour=5, minute=0, tzinfo=pytz.timezone('Asia/Kolkata')))
    
    print("✅ Ultra Pro Bot (v7.0) Started!")

if __name__ == "__main__":
    keep_alive()
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add_group", add_group))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("set_topper", set_topper_cmd))
    app.add_handler(CommandHandler("add_user", add_user_cmd))
    app.add_handler(CommandHandler("leaderboard", show_leaderboard)) # <--- Command
    
    app.add_handler(MessageHandler(filters.FORWARDED & filters.TEXT, handle_forwarded_result))

    conv = ConversationHandler(
        entry_points=[CommandHandler("add_link", start_add_link)],
        states={
            ASK_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_day)],
            ASK_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_link)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(conv)

    app.add_handler(CallbackQueryHandler(button_handler, pattern='^menu_|time_|add_link_|status_|help_|fire_|back_|show_'))
    app.add_handler(CallbackQueryHandler(mark_attendance, pattern='attendance_done'))

    app.run_polling()
