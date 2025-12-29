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
    start, add_group, set_custom_time_cmd, reset_all_cmd, button_handler, mark_attendance,
    start_add_link, receive_date, receive_topic, receive_link, cancel, set_topper_cmd, add_user_cmd, broadcast_cmd,
    show_leaderboard, show_profile, handle_forwarded_result, ASK_DATE, ASK_TOPIC, ASK_LINK
)
from jobs import job_send_test, job_nightly_report, job_morning_motivation

app_web = Flask('')
@app_web.route('/')
def home(): return "Final Bot Live 🟢"
def run_http(): app_web.run(host='0.0.0.0', port=8080)
def keep_alive(): t = Thread(target=run_http); t.start()

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

async def post_init(app):
    await app.bot.set_my_commands([
        ("start", "Menu"),
        ("add_test", "Schedule Quiz"),
        ("broadcast", "Announcement"),
        ("add_user", "Make Admin"),
        ("custom_time", "Set Time"),
        ("profile", "My Stats"),
        ("reset_all", "Factory Reset")
    ])
    
    db = load_data()
    t_str = db["settings"].get("time", "18:00")
    h, m = map(int, t_str.split(":"))
    
    # JOBS
    app.job_queue.run_daily(job_send_test, time(hour=h, minute=m, tzinfo=pytz.timezone('Asia/Kolkata')))
    app.job_queue.run_daily(job_nightly_report, time(hour=21, minute=30, tzinfo=pytz.timezone('Asia/Kolkata')))
    app.job_queue.run_daily(job_morning_motivation, time(hour=5, minute=0, tzinfo=pytz.timezone('Asia/Kolkata')))
    
    print("✅ Ultra Pro Bot (v12.0) Started!")

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

    # 🔥 Forward Handler (Auto Topper)
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

    # Callbacks
    app.add_handler(CallbackQueryHandler(button_handler, pattern='^menu_|add_link_|status_|show_|my_|reset_|help_'))
    app.add_handler(CallbackQueryHandler(mark_attendance, pattern='attendance_done'))

    app.run_polling()
