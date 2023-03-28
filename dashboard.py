from flask import Flask, render_template
import sqlite3

app = Flask(__name__)
DB_PATH = 'db/pipemanager.db'

def get_dashboard_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM run_status')
    data = cursor.fetchall()
    conn.close()
    return data

def get_last_check():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT timestamp FROM last_check WHERE id = 1")
    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0]
    else:
        return None

@app.route('/dashboard')
def dashboard():
    data = get_dashboard_data()
    last_check = get_last_check()
    return render_template('dashboard.html', data=data, last_check=last_check)

if __name__ == '__main__':
    app.run(debug=True)
