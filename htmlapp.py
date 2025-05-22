from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from datetime import datetime, timedelta
import os
import openai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

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
    return redirect(url_for('log_session'))

@app.route('/log', methods=['GET', 'POST'])
def log_session():
    if request.method == 'POST':
        skill = request.form['skill']
        duration = int(request.form['duration'])
        notes = request.form['notes']
        timestamp = datetime.now()
        cursor.execute("INSERT INTO sessions (skill, duration, notes, timestamp) VALUES (%s, %s, %s, %s)",
                       (skill, duration, notes, timestamp))
        conn.commit()
        return redirect(url_for('dashboard'))
    return render_template('log.html')

@app.route('/dashboard')
def dashboard():
    cursor.execute("SELECT skill, SUM(duration) FROM sessions WHERE timestamp >= NOW() - INTERVAL 7 DAY GROUP BY skill")
    rows = cursor.fetchall()
    skills = [r[0] for r in rows]
    durations = [r[1] for r in rows]

    cursor.execute("SELECT skill, notes FROM sessions WHERE timestamp >= NOW() - INTERVAL 7 DAY")
    notes_data = cursor.fetchall()
    feedback = generate_feedback(notes_data)

    return render_template('dashboard.html', skills=skills, durations=durations, feedback=feedback)

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

# templates/log.html
# -------------------
# Form to submit skill sessions

"""
<!DOCTYPE html>
<html>
<head>
    <title>Log Skill Session</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
</head>
<body class="p-4">
    <div class="container">
        <h2>Log Learning Session</h2>
        <form method="POST">
            <div class="mb-3">
                <label class="form-label">Skill</label>
                <input type="text" name="skill" class="form-control" required>
            </div>
            <div class="mb-3">
                <label class="form-label">Duration (minutes)</label>
                <input type="number" name="duration" class="form-control" required>
            </div>
            <div class="mb-3">
                <label class="form-label">Notes</label>
                <textarea name="notes" class="form-control" required></textarea>
            </div>
            <button type="submit" class="btn btn-primary">Submit</button>
        </form>
    </div>
</body>
</html>
"""

# templates/dashboard.html
# -------------------------
# Displays skill time chart and AI feedback

"""
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
</head>
<body class="p-4">
    <div class="container">
        <h2>Weekly Skill Time Overview</h2>
        <canvas id="skillChart" width="400" height="200"></canvas>

        <h4 class="mt-4">AI Feedback</h4>
        <div class="alert alert-info">
            {{ feedback }}
        </div>
    </div>

    <script>
        const ctx = document.getElementById('skillChart');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: {{ skills | tojson }},
                datasets: [{
                    label: 'Minutes Spent',
                    data: {{ durations | tojson }},
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    </script>
</body>
</html>
"""
