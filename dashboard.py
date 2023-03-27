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

@app.route('/dashboard')
def dashboard():
    data = get_dashboard_data()
    return render_template('dashboard.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)
