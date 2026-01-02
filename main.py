import logging
from threading import Thread
from flask import Flask
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    ConversationHandler, MessageHandler, filters
)
import nest_asyncio
nest_asyncio.apply()

# Import from other files
from config import BOT_TOKEN, ASK_DATE, ASK_TOPIC, ASK_LINK, ASK_TIME_SLOT, IST
from handlers import * # Import all handlers
from jobs import job_check_schedule, job_nightly_report, job_morning_motivation
from datetime import time

# Flask Server
app_web = Flask('')
@app_web.route('/')
def home(): return "Bot Running 🟢"
def run_http(): app_web.run(host='0.0.0.0', port=8080)
def keep_alive(): t = Thread(target=run_http); t.start()

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

async def post_init(app):
    # Jobs Registration
    app.job_queue.run_repeating(job_check_schedule, interval=60, first=10)
    app.job_queue.run_daily(job_nightly_report, time(hour=21, minute=30, tzinfo=IST))
    app.job_queue.run_daily(job_morning_motivation, time(hour=5, minute=0, tzinfo=IST))
    print("✅ System Online!")

if __name__ == "__main__":
    keep_alive()
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # Handlers Registration
    app.add_handler(CommandHandler("start", start))
    
    # Schedule Conv
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_link, pattern='^add_link_flow$')],
        states={
            ASK_DATE: [MessageHandler(filters.TEXT, receive_date)],
            ASK_TOPIC: [MessageHandler(filters.TEXT, receive_topic)],
            ASK_LINK: [MessageHandler(filters.TEXT, receive_link)],
            ASK_TIME_SLOT: [MessageHandler(filters.TEXT, receive_time_slot)],
        }, fallbacks=[CommandHandler("cancel", cancel)]
    ))
    
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()
