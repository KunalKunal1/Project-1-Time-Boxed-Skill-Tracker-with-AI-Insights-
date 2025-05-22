# Project-1-Time-Boxed-Skill-Tracker-with-AI-Insights-
Users log learning sessions (skill, duration, notes). The app tracks time, shows trends, and uses GPT to suggest improvements.

Tech Stack:
Backend: Python (Flask)
Database: MySQL
Frontend: HTML/CSS + Chart.js
AI: OpenAI GPT API
Extras: Bootstrap 5 UI

Pseudocode Plan:
Setup DB: MySQL tables for users and sessions.
Flask Backend:
User login/signup
Session logging
Weekly summary
GPT feedback route

Frontend UI:
Add Session page
Dashboard: Chart + AI tips
Chart.js for Visuals
OpenAI integration:
Summarize usage
Suggest skill shifts

File Structure
skill_tracker/
├── app.py
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   └── log.html
├── static/
│   └── chart.js
├── .env
├── requirements.txt
