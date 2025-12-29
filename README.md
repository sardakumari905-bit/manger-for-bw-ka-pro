# 🦅 RBSE Ultimate Manager Bot (v10.0)

![Status](https://img.shields.io/badge/Status-Online-brightgreen?style=for-the-badge&logo=telegram)
![Python](https://img.shields.io/badge/Built_With-Python_3.11-blue?style=for-the-badge&logo=python)
![Platform](https://img.shields.io/badge/Deploy-Render-violet?style=for-the-badge&logo=render)

**The most advanced Coaching Management System on Telegram.**
Designed specifically for RBSE Class 12th Groups to automate Quizzes, Attendance, Discipline, and Results.

---

## 🌟 Exclusive Features

### 📅 1. Smart Scheduler (Set & Forget)
* **Calendar System:** Schedule tests for specific dates (e.g., `01-01-2026`). The bot automatically wakes up on that date and runs the test.
* **No Daily Setup:** Setup the whole month in one go.

### 🤖 2. Auto-Attendance & Topper
* **Forward Magic:** Just forward the `@QuizBot` result to the group.
* **Auto-Action:** The bot detects the **Topper's Name** AND marks **Attendance** for all students listed in the leaderboard automatically (Backup for those who forgot to click the button).

### 🛡️ 3. Three-Layer Test Security
* **Layer 1 (00:00):** Attendance Call with Button `[🙋‍♂️ PRESENT SIR]`.
* **Layer 2 (00:01):** Warning Alert ("1 Min Left") -> **Pinned**.
* **Layer 3 (00:02):** The real Quiz Link is sent.

### ⏰ 4. Morning Motivation & Exam Countdown
* **6:00 AM Alarm:** Wakes up students with:
    * Days Left for Board Exams.
    * A fresh Motivational Quote.
    * Today's Test Schedule check.

### 🚫 5. Strict Discipline System (Auto-Kick)
* Tracks user attendance via unique ID.
* **3-Strike Rule:** If a student misses 3 tests in a row -> **Auto Ban/Kick**.

---

## 🛠️ Commands List

### 👑 Admin Commands (Owner Only)
| Command | Usage | Description |
| :--- | :--- | :--- |
| `/start` | Menu | Opens the Admin Control Panel. |
| `/add_test` | Interactive | Schedule a test for a future date (Date -> Topic -> Link). |
| `/custom_time` | `/custom_time 15:00` | Change test timing instantly. |
| `/broadcast` | `/broadcast Hello` | Send a message to all connected groups. |
| `/set_topper` | `/set_topper Name` | Manually set the topper if auto-detect fails. |
| `/add_user` | `/add_user 123456` | Promote a friend to Admin. |
| `/reset_all` | Command | **FACTORY RESET:** Deletes all data/schedule. |
| `/status` | Command | Check total groups and scheduled tests. |

### 👤 Student Commands
| Command | Description |
| :--- | :--- |
| `/profile` | View Report Card (Attendance, Rank, Strikes). |
| `/leaderboard` | View Top 10 Most Regular Students. |

---

## ⚙️ Configuration & Setup

### 1. File Setup
Ensure these 6 files are in your repository:
* `main.py`
* `config.py`
* `database.py`
* `handlers.py`
* `jobs.py`
* `requirements.txt`

### 2. Edit `config.py`
```python
BOT_TOKEN = "YOUR_TOKEN_HERE"  # Get from @BotFather
OWNER_ID = 123456789             # Your numeric ID
