# 🦅 RBSE Manager Bot (Version 8.0)

![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge&logo=telegram)
![Python](https://img.shields.io/badge/Language-Python_3.11-blue?style=for-the-badge&logo=python)
![Platform](https://img.shields.io/badge/Deploy-Render-violet?style=for-the-badge&logo=render)

**The Ultimate Coaching Management System for Telegram.**
Automates daily quizzes, tracks attendance, enforces discipline, and motivates students with an exam countdown.

---

## 🌟 Key Features (Ultra Pro Max)

### 🌅 1. Morning Routine (6:00 AM)
* **Exam Countdown:** Automatically calculates days left for RBSE Board Exams.
* **Motivation Dose:** Sends a fresh motivational quote daily to wake up students.

### 🚀 2. The 3-Step Test Sequence
* **Step 1 (Warning):** Sends "Attendance Button" first.
* **Step 2 (Alert):** Sends "1 Minute Left" & **Pins** the message.
* **Step 3 (Action):** Sends the **Quiz Link** (Start in Group).

### 🛡️ 3. Discipline & Security
* **Smart Attendance:** Tracks students via User ID (Button Click).
* **3-Strikes Rule:**
    * Miss 1 = Warning ⚠️
    * Miss 2 = Critical 🚨
    * Miss 3 = **AUTO KICK 🚫** (Banned from group).

### 📊 4. Reporting & Dashboard
* **Nightly Report (9:30 PM):** Auto-publishes Topper Name, Absentee List & Banned Users.
* **Auto-Topper:** Detects topper name from forwarded `@QuizBot` results.
* **Student Profile:** `/profile` generates a digital report card for students.
* **Leaderboard:** Displays Top 10 most regular students.

### 👑 5. Admin Control Panel
* **🚀 Quick Start:** Launch a test instantly (for surprise tests).
* **📢 Broadcast:** Send announcements to all connected groups.
* **⏰ Flexible Timer:** Change test time (4 PM - 9 PM) with one click.
* **👮 Add Admin:** Allow other users to manage the bot via `/add_user`.

---

## 🛠️ Commands List

| Command | Description | Access |
| :--- | :--- | :--- |
| `/start` | Open Main Menu & Dashboard | Everyone |
| `/profile` | View My Report Card (Attendance/Strikes) | Everyone |
| `/leaderboard` | View Top 10 Students | Everyone |
| `/add_group` | Connect a Group to the Bot | Admin (In Group) |
| `/add_link` | Add Quiz Link (Conversation Mode) | Admin |
| `/broadcast` | Send Message to All Groups | Admin |
| `/set_topper` | Manually Set Topper Name | Admin |
| `/add_user` | Promote a User to Admin | Owner Only |
| `/status` | Check Bot Health & Queue | Admin |

---

## 🚀 Deployment Guide (Render.com)

This bot is optimized to run **Free 24/7** on Render.

### Step 1: Prepare Files
Ensure your GitHub repository has these **6 Files**:
1.  `main.py` (Main Controller)
2.  `config.py` (Settings & Token)
3.  `database.py` (Data Manager)
4.  `handlers.py` (Commands & Logic)
5.  `jobs.py` (Automation & Scheduler)
6.  `requirements.txt` (Dependencies)

### Step 2: Configure `config.py`
Open `config.py` and set your credentials:
```python
BOT_TOKEN = "123456:ABC-DEF..."  # From @BotFather
OWNER_ID = 123456789             # Your Telegram User ID
