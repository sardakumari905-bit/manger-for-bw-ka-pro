# 🤖 Board Wallah (BW) Manager Bot [v17.0]

![Status](https://img.shields.io/badge/Status-Online-brightgreen?style=for-the-badge&logo=telegram)
![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)
![Deploy](https://img.shields.io/badge/Deploy-Render-violet?style=for-the-badge&logo=render)

**The Ultimate "All-in-One" Coaching Management System for Telegram.**
Designed for **RBSE Class 12th** to automate Tests, Attendance, Discipline, and Results using a Smart Menu System.

---

## 🌟 Key Features (Pro Edition)

### 🌅 1. Morning Routine (5:00 AM)
* **Auto-Alarm:** Wakes up students daily at 5 AM.
* **Content:** Sends a Motivational Quote + Board Exam Countdown.

### 📝 2. The Smart Test System (4:00 PM)
* **Step 1:** Sends "Attendance Button" `[🙋‍♂️ PRESENT SIR]`.
* **Step 2:** Sends Warning Alert & Pins the Message.
* **Step 3:** Automatically sends the Quiz Link.

### 🛡️ 3. Strict Discipline (Auto-Kick)
* **3-Strike Rule:** If a student misses attendance for **3 consecutive days**, the bot **Auto-Kicks (Bans)** them from the group.
* **No Mercy:** Keeps the group active and disciplined.

### 🧠 4. Intelligent Attendance
* **Button Mode:** Students mark present by clicking a button.
* **Auto-Recovery:** If they forget, just forward the `@QuizBot` result to the group. The bot detects the name and marks attendance automatically!

### 🎮 5. Hybrid Admin Panel (Menu Based)
No need to remember commands! Just use the Button Menu:
* **➕ Schedule Test:** Add future tests via Calendar.
* **📢 Broadcast:** Send announcements to all groups via buttons.
* **⏰ Set Time:** Change test timing instantly.
* **🏆 Set Topper:** Manually announce the daily winner.
* **👮 Add Admin:** Promote team members easily.

---

## 🛠️ How to Use (Commands)

### 👑 Admin Menu (Owner)
Just type **/start** to open the **Control Panel**.
| Button | Description |
| :--- | :--- |
| **🚀 QUICK START** | Fire a scheduled test immediately. |
| **➕ Schedule Test** | Add Date, Topic & Link for future tests. |
| **📢 Broadcast** | Send a message to all connected groups. |
| **⏰ Set Time** | Change daily test timing (e.g., 16:00). |
| **🏆 Set Topper** | Manually set today's topper name. |
| **👮 Add Admin** | Add a new Admin by User ID. |
| **🗑️ RESET BOT** | Factory Reset (Delete all data). |

### 👤 Student Menu
Just type **/start** in Bot PM.
| Button | Description |
| :--- | :--- |
| **👤 My Profile** | View Attendance count & Strike status. |
| **🏆 Leaderboard** | View Top 10 Regular Students. |

---

## 🚀 Deployment Guide (Render)

### Step 1: Files Required
Ensure your GitHub repository has these 6 files:
1. `main.py`
2. `handlers.py`
3. `jobs.py`
4. `database.py`
5. `config.py`
6. `requirements.txt`

### Step 2: Edit `config.py`
Open `config.py` and enter your details:
```python
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE" 
OWNER_ID = 1234567890  # Your Numeric Telegram ID
