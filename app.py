from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import sqlite3
import csv
from datetime import datetime
from firebase_config import db

app = Flask(__name__)
CORS(app)

# === SQLite Setup ===
def get_db_connection():
    conn = sqlite3.connect('attendance.db')
    conn.execute("PRAGMA foreign_keys = 1")
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            class TEXT NOT NULL,
            parent_contact TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            date TEXT,
            status TEXT,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# === Routes ===

@app.route('/register_student', methods=['POST'])
def register_student():
    data = request.get_json()
    name = data.get('name')
    class_name = data.get('class')
    parent_contact = data.get('parent_contact', '')

    if not name or not class_name:
        return jsonify({'error': 'Name and class required'}), 400

    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO students (name, class, parent_contact) VALUES (?, ?, ?)',
              (name, class_name, parent_contact))
    conn.commit()
    student_id = c.lastrowid
    conn.close()

    db.collection('students').document(str(student_id)).set({
        'name': name,
        'class': class_name,
        'parent_contact': parent_contact,
        'created_at': datetime.now().isoformat()
    })

    return jsonify({'message': 'Student registered', 'student_id': student_id}), 201


@app.route('/attendance_report', methods=['GET'])
def attendance_report():
    student_id = request.args.get('student_id')
    conn = get_db_connection()
    c = conn.cursor()

    if student_id:
        c.execute('SELECT date, status FROM attendance WHERE student_id=? ORDER BY date', (student_id,))
        records = [{'date': r[0], 'status': r[1]} for r in c.fetchall()]
    else:
        c.execute('SELECT student_id, date, status FROM attendance ORDER BY student_id, date')
        records = [{'student_id': r[0], 'date': r[1], 'status': r[2]} for r in c.fetchall()]

    conn.close()
    return jsonify(records), 200


@app.route('/students', methods=['GET'])
def get_students():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT id, name, class, parent_contact FROM students')
    students = [{'id': r[0], 'name': r[1], 'class': r[2], 'parent_contact': r[3]} for r in c.fetchall()]
    conn.close()
    return jsonify(students), 200


@app.route('/attendance_percentage', methods=['GET'])
def attendance_percentage():
    student_id = request.args.get('student_id')
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM attendance WHERE student_id=?', (student_id,))
    total = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM attendance WHERE student_id=? AND status=?', (student_id, 'Present'))
    present = c.fetchone()[0]
    conn.close()

    percentage = (present / total * 100) if total > 0 else 0
    return jsonify({'student_id': student_id, 'percentage': round(percentage, 2)}), 200


@app.route('/download_students_csv', methods=['GET'])
def download_students_csv():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT id, name, class, parent_contact FROM students')
    data = c.fetchall()
    conn.close()

    response = make_response()
    response.headers['Content-Disposition'] = 'attachment; filename=students.csv'
    response.headers['Content-Type'] = 'text/csv'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Name', 'Class', 'Parent Contact'])
    for row in data:
        writer.writerow(row)

    return response


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
