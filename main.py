import logging
from threading import Thread
from flask import Flask
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    ConversationHandler, MessageHandler, filters
)
import nest_asyncio
nest_asyncio.apply()

# --- LOCAL IMPORTS (Ye alag-alag line me hone chahiye) ---
from config import *
from handlers import * from jobs import job_check_schedule, job_nightly_report, job_morning_motivation
from datetime import time

# --- FLASK SERVER (Bot ko 24/7 chalane ke liye) ---
app_web = Flask('')

@app_web.route('/')
def home():
    return "Board Pro Bot is Running! 🟢"

def run_http():
    app_web.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_http)
    t.start()

# Logging setup
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- JOB QUEUE SETUP ---
async def post_init(app):
    # 1. Schedule Check (Har 60 second me check karega)
    app.job_queue.run_repeating(job_check_schedule, interval=60, first=10)
    
    # 2. Night Report (Raat 9:00 baje)
    app.job_queue.run_daily(job_nightly_report, time(hour=21, minute=0, tzinfo=IST)) 
    
    # 3. Morning Motivation (Subah 5:00 baje)
    app.job_queue.run_daily(job_morning_motivation, time(hour=5, minute=0, tzinfo=IST))
    
    print("✅ System Online: Jobs & Schedule Loaded!")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    keep_alive() # Server start
    
    # Bot Builder
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # 1. Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add_group", add_group))
    app.add_handler(CommandHandler("reset_all", reset_all_cmd))

    # 2. Auto Attendance (Forward Message Listener)
    app.add_handler(MessageHandler(filters.FORWARDED, handle_forwarded_result))

    # 3. Conversation: Schedule Test
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_link, pattern='^add_link_flow$')],
        states={
            ASK_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_date)],
            ASK_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_topic)],
            ASK_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_link)],
            ASK_TIME_SLOT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_time_slot)],
        }, fallbacks=[CommandHandler("cancel", cancel)]
    ))

    # 4. Conversation: Set Topper (Subject Wise)
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(start_set_topper, pattern='^topper_flow$')],
        states={
            ASK_TOPPER_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_topper_subject)],
            ASK_TOPPER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_topper_name)],
        }, fallbacks=[CommandHandler("cancel", cancel)]
    ))
    
    # 5. Conversation: Add Admin
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_admin_btn, pattern='^add_admin_flow$')],
        states={ASK_ADMIN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_admin_id_btn)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    ))
    
    # 6. Conversation: Broadcast
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(start_broadcast_btn, pattern='^broadcast_flow$')],
        states={ASK_BROADCAST_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_broadcast_btn)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    ))
    
    # 7. Button Handler (Sabse last me hona chahiye)
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🚀 Board Pro Bot is STARTING...")
    app.run_polling()
