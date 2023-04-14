from flask import Flask, render_template
import sqlite3
import base64
# from io import BytesIO
# from PIL import Image, UnidentifiedImageError

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

def get_image_paths(run_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT qscore_histogram, scatter_plot FROM run_metrics WHERE run_id = ?", (run_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return result
    else:
        return None, None

@app.route('/dashboard')
def dashboard():
    run_status_data = get_run_status_data()
    run_metrics_data = get_run_metrics_data()
    for row in run_metrics_data:
        qscore_histogram_path, scatter_plot_path = get_image_paths(row[1])
        row += (qscore_histogram_path, scatter_plot_path)
    last_check = get_last_check()
    return render_template('dashboard.html', run_status_data=run_status_data, run_metrics_data=run_metrics_data, last_check=last_check)

if __name__ == '__main__':
    app.run(debug=True)