import os
import glob
import subprocess
import sqlite3
import time
import openpyxl
import re

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
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

def update_run_status(dirpath, stage, status, run_id=None, output_dir=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO run_status (id, run_id, dirpath, stage, output_dir, status)
        VALUES (
            (SELECT id FROM run_status WHERE dirpath = ?),
            COALESCE(?, (SELECT run_id FROM run_status WHERE dirpath = ?)),
            ?,
            ?,
            COALESCE(?, (SELECT output_dir FROM run_status WHERE dirpath = ?)),
            ?
        )
    ''', (dirpath, run_id, dirpath, dirpath, stage, output_dir, dirpath, status))
    
    conn.commit()
    conn.close()


def get_run_status(dirpath):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT run_id, stage, output_dir, status FROM run_status WHERE dirpath = ?', (dirpath,))
    result = cursor.fetchone()

    conn.close()

    if result:
        return {'run_id': result[0], 'stage': result[1], 'output_dir': result[2], 'status': result[3]}
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

def process_stage1(dirpath, file):
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
    print(f'Processing Stage 2 in {dirpath}')
    run_id = get_run_status(dirpath)['run_id']
    subprocess.run(['python3', 'ssmove.py', file, str(run_id)], check=True)
    update_run_status(dirpath, 3, 'Sequencing in progress')

def process_stage3(dirpath, file):
    print(f'Processing Stage 3 in {dirpath}')
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

    update_run_status(dirpath, None, 'completed')

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
        
        time.sleep(30)  # Check for new directories every 30 seconds

if __name__ == '__main__':
    main()
