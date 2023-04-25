from flask import Flask, render_template
import sqlite3
import base64
import yaml

app = Flask(__name__)
CONFIG_PATH = 'config.yaml'

def get_config():
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
    return config

def get_run_status_data():
    db_path = get_config()['db_path']
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM run_status')
    data = cursor.fetchall()
    conn.close()
    return data

def get_run_metrics_data():
    db_path = get_config()['db_path']
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM run_metrics')
    data = cursor.fetchall()
    conn.close()
    return data

def get_last_check():
    db_path = get_config()['db_path']
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT timestamp FROM last_check WHERE id = 1")
    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0]
    else:
        return None

def get_image_paths(run_id):
    db_path = get_config()['db_path']
    conn = sqlite3.connect(db_path)
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