import os
import glob
import subprocess
import sqlite3
import time
import openpyxl
import re
import dxpy
import pytz
from datetime import datetime

DB_PATH = 'db/pipemanager.db'

def setup_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS run_status (
            id INTEGER PRIMARY KEY,
            run_id INTEGER,
            dirpath TEXT,
            stage INTEGER,
            output_dir TEXT,
            status TEXT,
            job_id TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS last_check (
            id INTEGER PRIMARY KEY,
            timestamp TEXT
        )
    ''')

    conn.commit()
    conn.close()
    
def update_run_status(dirpath, stage, status, run_id=None, output_dir=None, job_id=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO run_status (id, run_id, dirpath, stage, output_dir, status, job_id)
        VALUES (
            (SELECT id FROM run_status WHERE dirpath = ?),
            COALESCE(?, (SELECT run_id FROM run_status WHERE dirpath = ?)),
            ?,
            ?,
            COALESCE(?, (SELECT output_dir FROM run_status WHERE dirpath = ?)),
            ?,
            COALESCE(?, (SELECT job_id FROM run_status WHERE dirpath = ?))
        )
    ''', (dirpath, run_id, dirpath, dirpath, stage, output_dir, dirpath, status, job_id, dirpath))
    
    conn.commit()
    conn.close()

def update_last_check():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    tz = pytz.timezone('Europe/London')
    now = datetime.now(tz)
    timestamp = now.strftime('%d-%m-%Y %H:%M:%S')

    cursor.execute("INSERT OR REPLACE INTO last_check (id, timestamp) VALUES (1, ?)", (timestamp,))
    conn.commit()
    conn.close()

def get_run_status(dirpath):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT run_id, stage, output_dir, status, job_id FROM run_status WHERE dirpath = ?', (dirpath,))
    result = cursor.fetchone()

    conn.close()

    if result:
        return {'run_id': result[0], 'stage': result[1], 'output_dir': result[2], 'status': result[3], 'job_id': result[4]}
    else:
        return None

def find_new_files(dirpath):
    return glob.glob(os.path.join(dirpath, '*.xlsx'))

def validate_xlsx_file(file):
    try:
        workbook = openpyxl.load_workbook(file)
        # Add your validation logic here
        # ...
        return True
    except (openpyxl.utils.exceptions.InvalidFileException, Exception) as e:
        print(f"Error reading xlsx file: {e}")
        return False

def get_dx_job_status(basename, project_id):
    '''Scrape the DNAnexus API for run status - IMPORTANT - REMOVE API TOKEN BEFORE MAKING REPO LIVE'''
    dxpy.set_security_context({"auth_token_type": "Bearer", "auth_token": "wWPpJGA9jPho4RjpOuzrGBAktQXCzVHf"})
    
    for job in dxpy.find_jobs(project=project_id):
        job_desc = dxpy.DXJob(job['id']).describe()
        if basename in str(job_desc['folder']):
            return job_desc['state'], job_desc['id']
    return None

def process_stage1(dirpath, file):
    '''Scan for new run_folders, check for a valid xlsx'''
    print(f"Processing Stage 1 for {dirpath}")

    # Add a validation function to check the validity of the xlsx file.
    if not validate_xlsx_file(file):
        print(f"Invalid xlsx file: {file}. Skipping the directory.")
        return

    # Process the file
    subprocess.run(['python3', 'ssgen.py', file], check=True)

    # Extract the run_id from the directory name
    basename = os.path.normpath(dirpath).split(os.sep)[-1]
    run_id_match = re.search(r"(\d+)", basename)
    if run_id_match is not None:
        run_id = run_id_match.group()
    else:
        print(f"Failed to extract run_id from directory name: {dirpath}. Skipping the directory.")
        return

    # Update the status in the database
    update_run_status(dirpath, 2, 'SampleSheet generated', run_id)

def process_stage2(dirpath, file):
    '''Move the SampleSheets to the correct location before dxstream begins'''
    print(f'Processing Stage 2 in {dirpath}')
    run_id = get_run_status(dirpath)['run_id']
    subprocess.run(['python3', 'ssmove.py', file, str(run_id)], check=True)
    update_run_status(dirpath, 3, 'RTA in progress')

def process_stage3(dirpath, file):
    '''Check RTA has completed, then begin polling for demultiplex status'''
    print(f'Processing Stage 3 (demultiplex) in {dirpath}')
    run_status = get_run_status(dirpath)
    run_id = run_status['run_id']
    output_dir = run_status['output_dir']

    if os.path.isfile(os.path.join(output_dir, 'RTAComplete.txt')):
        basename = os.path.basename(output_dir)
        # Run get_dx_job_status using the 'landing' directory as the base
        job_state, job_id = get_dx_job_status(basename, 'project-G20fB684yYBbqfXFBvGvzgXV')

        if job_state == 'done':
            print(f"Demultiplex for run {run_id} is complete. Proceeding to analysis.")
            update_run_status(dirpath, 4, 'Demultiplexing complete', job_id=job_id)
        else:
            print(f"Demultiplex for {run_id} is not complete. Current state: {job_state}")
            update_run_status(dirpath, 3, 'Demultiplex in progress', job_id=job_id)
    else:
        print(f'RTA in progress: {dirpath}')


def process_stage4(dirpath, file):
    '''Demultiplex complete, ensure the QC is valid before launching analysis'''
    print(f'Processing Stage 4 (analysis) in {dirpath}')
    with open(os.path.join(dirpath, 'move.txt'), 'r') as f:
        output_dir = f.read().strip()

    if os.path.isfile(os.path.join(output_dir, 'pipeline.launch')):
        print('Pipeline launched.') #debug
        return
    elif os.path.isfile(os.path.join(output_dir, 'qc.pass')):
        subprocess.run(['yes', 'Y'], check=True)
        subprocess.run(['python3', '/projects/dnanexus/tso500-prepare-inputs/create_inputs.py', output_dir, '-s', os.path.join(output_dir, 'SampleSheet.csv')], check=True)
        open(os.path.join(output_dir, 'pipeline.launch'), 'w').close()
    elif os.path.isfile(os.path.join(output_dir, 'RTAComplete.txt')):
        subprocess.run(['python3', 'q_scrape.py', output_dir, dirpath], check=True)

    update_run_status(dirpath, None, 'Run completed')

def main():
    setup_database()
    
    search_path = '/home/bioinf/george/pipeline_automation/*/*/*/'
    
    while True:
        directories = glob.glob(search_path, recursive=True)
        
        for dirpath in directories:
            run_status = get_run_status(dirpath)
            new_files = find_new_files(dirpath)
            
            if not new_files:
                continue

            file = new_files[0]

            if run_status is None:
                # New directory, start processing Stage 1
                process_stage1(dirpath, file)

            elif run_status['stage'] == 2:
                process_stage2(dirpath, file)
            elif run_status['stage'] == 3:
                process_stage3(dirpath, file)
            elif run_status['stage'] == 4:
                process_stage4(dirpath, file)

        update_last_check() # Update the database to reflect check has taken place
        time.sleep(30)  # Check for new directories every 30 seconds

if __name__ == '__main__':
    main()