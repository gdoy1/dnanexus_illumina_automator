from flask import Flask, render_template
import sqlite3

app = Flask(__name__)
DB_PATH = 'db/pipemanager.db'

def get_run_status_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM run_status')
    data = cursor.fetchall()
    conn.close()
    return data

def get_run_metrics_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM run_metrics')
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
    run_status_data = get_run_status_data()
    run_metrics_data = get_run_metrics_data()
    last_check = get_last_check()
    return render_template('dashboard.html', run_status_data=run_status_data, run_metrics_data=run_metrics_data, last_check=last_check)

if __name__ == '__main__':
    app.run(debug=True)