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
    start, add_group, reset_all_text_cmd, button_handler, mark_attendance,
    start_add_link, receive_date, receive_topic, receive_link, cancel, 
    start_broadcast_btn, send_broadcast_btn, broadcast_text_cmd,
    start_add_admin_btn, receive_admin_id_btn, add_user_text_cmd,
    custom_time_text_cmd,
    show_leaderboard, show_profile, handle_forwarded_result, set_topper_cmd,
    ASK_DATE, ASK_TOPIC, ASK_LINK, ASK_BROADCAST_MSG, ASK_ADMIN_ID
)
from jobs import job_send_test, job_nightly_report, job_morning_motivation

app_web = Flask('')
@app_web.route('/')
def home(): return "Hybrid Bot Live 🟢"
def run_http(): app_web.run(host='0.0.0.0', port=8080)
def keep_alive(): t = Thread(target=run_http); t.start()

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

async def post_init(app):
    await app.bot.set_my_commands([
        ("start", "Menu Panel"),
        ("add_test", "Schedule (Text)"),
        ("broadcast", "Msg (Text)"),
        ("add_user", "Add Admin (Text)"),
        ("custom_time", "Set Time (Text)"),
        ("profile", "My Report"),
        ("leaderboard", "Top List")
    ])
    
    db = load_data()
    t_str = db["settings"].get("time", "18:00")
    h, m = map(int, t_str.split(":"))
    
    app.job_queue.run_daily(job_send_test, time(hour=h, minute=m, tzinfo=pytz.timezone('Asia/Kolkata')))
    app.job_queue.run_daily(job_nightly_report, time(hour=21, minute=30, tzinfo=pytz.timezone('Asia/Kolkata')))
    app.job_queue.run_daily(job_morning_motivation, time(hour=5, minute=0, tzinfo=pytz.timezone('Asia/Kolkata')))
    
    print("✅ Ultra Pro Bot (v15.0 Hybrid) Started!")

if __name__ == "__main__":
    keep_alive()
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # --- 1. DIRECT TEXT COMMANDS ---
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add_group", add_group))
    app.add_handler(CommandHandler("reset_all", reset_all_text_cmd))
    app.add_handler(CommandHandler("custom_time", custom_time_text_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_text_cmd)) # Text: /broadcast Hello
    app.add_handler(CommandHandler("add_user", add_user_text_cmd))   # Text: /add_user 123
    app.add_handler(CommandHandler("set_topper", set_topper_cmd))
    app.add_handler(CommandHandler("profile", show_profile))
    app.add_handler(CommandHandler("leaderboard", show_leaderboard))

    # --- 2. INTERACTIVE BUTTON CONVERSATIONS ---
    
    # Schedule (Works for both /add_test AND Button)
    conv_schedule = ConversationHandler(
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
    app.add_handler(conv_schedule)

    # Broadcast (Button Only Flow)
    conv_broadcast = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_broadcast_btn, pattern='^broadcast_flow$')],
        states={ASK_BROADCAST_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_broadcast_btn)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(conv_broadcast)

    # Add Admin (Button Only Flow)
    conv_admin = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_admin_btn, pattern='^add_admin_flow$')],
        states={ASK_ADMIN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_admin_id_btn)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(conv_admin)

    # General Buttons
    app.add_handler(CallbackQueryHandler(button_handler, pattern='^menu_|time_|status_|show_|my_|reset_|back_|fire_'))
    app.add_handler(CallbackQueryHandler(mark_attendance, pattern='attendance_done'))

    # Forward Handler
    app.add_handler(MessageHandler(filters.FORWARDED & filters.TEXT, handle_forwarded_result))

    app.run_polling()
