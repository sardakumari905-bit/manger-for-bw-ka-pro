# main.py
import logging
from threading import Thread
from flask import Flask
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    ConversationHandler, MessageHandler, filters
)
import nest_asyncio
nest_asyncio.apply()

# --- LOCAL IMPORTS (FIXED HERE) ---
from config import *
from handlers import * from jobs import job_check_schedule, job_nightly_report, job_morning_motivation
from datetime import time

# --- FLASK SERVER (Keep Alive) ---
app_web = Flask('')
@app_web.route('/')
def home(): return "Board Pro Bot Running 🟢"
def run_http(): app_web.run(host='0.0.0.0', port=8080)
def keep_alive(): t = Thread(target=run_http); t.start()

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

async def post_init(app):
    # 1. Schedule Check (Every 60s)
    app.job_queue.run_repeating(job_check_schedule, interval=60, first=10)
    
    # 2. Night Report (9:00 PM IST)
    # Note: IST timezone config.py se aa raha hai
    app.job_queue.run_daily(job_nightly_report, time(hour=21, minute=0, tzinfo=IST)) 
    
    # 3. Morning Motivation (5:00 AM IST)
    app.job_queue.run_daily(job_morning_motivation, time(hour=5, minute=0, tzinfo=IST))
    
    print("✅ System Online: Jobs & Schedule Loaded!")

if __name__ == "__main__":
    keep_alive()
    
    # Build Application
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # --- COMMAND HANDLERS ---
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add_group", add_group))
    app.add_handler(CommandHandler("reset_all", reset_all_cmd))

    # --- MESSAGE HANDLERS ---
    # Auto Attendance via Forwarded Messages
    app.add_handler(MessageHandler(filters.FORWARDED, handle_forwarded_result))

    # --- CONVERSATION: SCHEDULE TEST ---
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_link, pattern='^add_link_flow$')],
        states={
            ASK_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_date)],
            ASK_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_topic)],
            ASK_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_link)],
            ASK_TIME_SLOT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_time_slot)],
        }, fallbacks=[CommandHandler("cancel", cancel)]
    ))

    # --- CONVERSATION: SET TOPPER (Subject Wise) ---
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(start_set_topper, pattern='^topper_flow$')],
        states={
            ASK_TOPPER_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_topper_subject)],
            ASK_TOPPER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_topper_name)],
        }, fallbacks=[CommandHandler("cancel", cancel)]
    ))
    
    # --- CONVERSATION: ADD ADMIN ---
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_admin_btn, pattern='^add_admin_flow$')],
        states={ASK_ADMIN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_admin_id_btn)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    ))
    
    # --- CONVERSATION: BROADCAST ---
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(start_broadcast_btn, pattern='^broadcast_flow$')],
        states={ASK_BROADCAST_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_broadcast_btn)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    ))
    
    # --- BUTTON HANDLER (Must be last) ---
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🚀 Board Pro Bot is STARTING...")
    app.run_polling()
