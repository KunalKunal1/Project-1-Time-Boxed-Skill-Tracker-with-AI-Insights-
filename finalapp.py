from flask import Flask, render_template, request, redirect, url_for, session, send_file
import mysql.connector
from datetime import datetime, timedelta
import os
import openai
import csv
from io import StringIO
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "devkey")

# DB Connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="your_password",
    database="skill_tracker"
)
cursor = conn.cursor()

# OpenAI Key
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('log_session'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor.execute("SELECT id, password FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            return redirect(url_for('log_session'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/log', methods=['GET', 'POST'])
def log_session():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        skill = request.form['skill']
        duration = int(request.form['duration'])
        notes = request.form['notes']
        timestamp = datetime.now()
        cursor.execute("INSERT INTO sessions (user_id, skill, duration, notes, timestamp) VALUES (%s, %s, %s, %s, %s)",
                       (session['user_id'], skill, duration, notes, timestamp))
        conn.commit()
        return redirect(url_for('dashboard'))
    return render_template('log.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    cursor.execute("""
        SELECT skill, SUM(duration) FROM sessions
        WHERE user_id = %s AND timestamp >= NOW() - INTERVAL 7 DAY
        GROUP BY skill
    """, (session['user_id'],))
    rows = cursor.fetchall()
    skills = [r[0] for r in rows]
    durations = [r[1] for r in rows]

    cursor.execute("""
        SELECT skill, notes FROM sessions
        WHERE user_id = %s AND timestamp >= NOW() - INTERVAL 7 DAY
    """, (session['user_id'],))
    notes_data = cursor.fetchall()
    feedback = generate_feedback(notes_data)

    return render_template('dashboard.html', skills=skills, durations=durations, feedback=feedback)

@app.route('/export')
def export_csv():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    cursor.execute("SELECT skill, duration, notes, timestamp FROM sessions WHERE user_id = %s", (session['user_id'],))
    rows = cursor.fetchall()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Skill', 'Duration', 'Notes', 'Timestamp'])
    writer.writerows(rows)
    output.seek(0)
    return send_file(
        output,
        mimetype='text/csv',
        download_name='sessions.csv',
        as_attachment=True
    )

def generate_feedback(notes_data):
    text = "\n".join([f"Skill: {s}\nNote: {n}" for s, n in notes_data])
    prompt = f"""
You are a productivity coach. Analyze the following learning session notes and give suggestions:
{text}

Summarize insights and suggest focus skills for next week:
"""
    try:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            max_tokens=150
        )
        return response.choices[0].text.strip()
    except:
        return "Feedback generation failed."

if __name__ == '__main__':
    app.run(debug=True)
