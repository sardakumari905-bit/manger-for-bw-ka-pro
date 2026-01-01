import logging
import pytz
from threading import Thread
from flask import Flask
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    ConversationHandler, MessageHandler, filters
)
from datetime import time
import nest_asyncio
nest_asyncio.apply()

from config import BOT_TOKEN
from database import load_data
from handlers import (
    start, add_group, reset_all_cmd, button_handler, mark_attendance,
    start_add_link, receive_date, receive_topic, receive_link, receive_time_slot, cancel, 
    start_broadcast_btn, send_broadcast_btn, 
    start_add_admin_btn, receive_admin_id_btn,
    start_set_topper, receive_topper_name,
    show_leaderboard, show_profile, handle_forwarded_result, 
    ASK_DATE, ASK_TOPIC, ASK_LINK, ASK_TIME_SLOT, ASK_BROADCAST_MSG, ASK_ADMIN_ID, ASK_TOPPER_NAME
)
from jobs import job_check_schedule, job_nightly_report, job_morning_motivation

app_web = Flask('')
@app_web.route('/')
def home(): return "Board Wallah Live 🟢"
def run_http(): app_web.run(host='0.0.0.0', port=8080)
def keep_alive(): t = Thread(target=run_http); t.start()

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

async def post_init(app):
    await app.bot.set_my_commands([("start", "Control Panel")])
    tz = pytz.timezone('Asia/Kolkata')

    # 1. Check Schedule EVERY MINUTE (Yeh multi-test ke liye zaroori hai)
    app.job_queue.run_repeating(job_check_schedule, interval=60, first=10)

    # 2. Fixed Jobs
    app.job_queue.run_daily(job_nightly_report, time(hour=21, minute=30, tzinfo=tz))
    app.job_queue.run_daily(job_morning_motivation, time(hour=5, minute=0, tzinfo=tz))
    
    print("✅ System Online: Multi-Test Scheduler Ready!")

if __name__ == "__main__":
    keep_alive()
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add_group", add_group))
    app.add_handler(CommandHandler("reset_all", reset_all_cmd))
    app.add_handler(MessageHandler(filters.FORWARDED & filters.TEXT, handle_forwarded_result))

    # Schedule Flow (Updated with Time Slot)
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_link, pattern='^add_link_flow$')],
        states={
            ASK_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_date)],
            ASK_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_topic)],
            ASK_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_link)],
            ASK_TIME_SLOT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_time_slot)], # New Step
        }, fallbacks=[CommandHandler("cancel", cancel)]
    ))

    # Other Flows
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(start_broadcast_btn, pattern='^broadcast_flow$')],
        states={ASK_BROADCAST_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_broadcast_btn)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    ))
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_admin_btn, pattern='^add_admin_flow$')],
        states={ASK_ADMIN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_admin_id_btn)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    ))
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(start_set_topper, pattern='^topper_flow$')],
        states={ASK_TOPPER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_topper_name)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    ))

    app.add_handler(CallbackQueryHandler(button_handler, pattern='^menu_|status_|reset_|back_|fire_'))
    app.add_handler(CallbackQueryHandler(show_profile, pattern='^my_profile$'))
    app.add_handler(CallbackQueryHandler(show_leaderboard, pattern='^show_leaderboard$'))
    app.add_handler(CallbackQueryHandler(mark_attendance, pattern='attendance_done'))

    app.run_polling()
