from flask import Flask, request, jsonify, render_template
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# เชื่อมต่อ PostgreSQL
conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT", 5432)
)
cursor = conn.cursor()

# สร้างตารางถ้ายังไม่มี
cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    number TEXT,
    student_id TEXT,
    name TEXT
);

CREATE TABLE IF NOT EXISTS attendance (
    date TEXT,
    student_number TEXT,
    status TEXT,
    note TEXT
);
""")
conn.commit()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/save", methods=["POST"])
def save():
    data = request.get_json()
    
    cursor.execute("DELETE FROM students")
    for student in data['students']:
        cursor.execute(
            "INSERT INTO students (number, student_id, name) VALUES (%s, %s, %s)",
            (student['number'], student['id'], student['name'])
        )

    cursor.execute("DELETE FROM attendance")
    for date, day_data in data['attendance'].items():
        for number, details in day_data['students'].items():
            cursor.execute(
                "INSERT INTO attendance (date, student_number, status, note) VALUES (%s, %s, %s, %s)",
                (date, number, details.get('status', ''), details.get('note', ''))
            )

    conn.commit()
    return jsonify({"success": True})

@app.route("/load")
def load():
    cursor.execute("SELECT number, student_id, name FROM students")
    students_data = cursor.fetchall()
    students = [
        {"number": s[0], "id": s[1], "name": s[2], "photo": ""}
        for s in students_data
    ]

    cursor.execute("SELECT date, student_number, status, note FROM attendance")
    attendance_data = cursor.fetchall()
    attendance = {}
    for row in attendance_data:
        date, number, status, note = row
        if date not in attendance:
            attendance[date] = {"students": {}}
        attendance[date]["students"][number] = {"status": status, "note": note}

    return jsonify({"success": True, "data": {"students": students, "attendance": attendance}})

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
