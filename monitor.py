# Developed by George
# 20/03/2023

# Script designed to poll for changes in technical directory, generate SampleSheets in appropriate directory, 
# poll for RTA completion, and launch pipeline via create_inputs.py

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
DX_API_KEY = os.environ.get('DX_API_KEY')

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
            job_id TEXT,
            analysis_id TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS last_check (
            id INTEGER PRIMARY KEY,
            timestamp TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS run_metrics (
            id INTEGER PRIMARY KEY,
            run_id INTEGER,
            q30 REAL,
            error_rate REAL,
            yield REAL,
            cluster_pf REAL,
            FOREIGN KEY (run_id) REFERENCES run_status(run_id)
        )
    ''')

    conn.commit()
    conn.close()
    
def update_run_status(dirpath, stage, status, run_id=None, output_dir=None, job_id=None, analysis_id=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO run_status (id, run_id, dirpath, stage, output_dir, status, job_id, analysis_id)
        VALUES (
            (SELECT id FROM run_status WHERE dirpath = ?),
            COALESCE(?, (SELECT run_id FROM run_status WHERE dirpath = ?)),
            ?,
            ?,
            COALESCE(?, (SELECT output_dir FROM run_status WHERE dirpath = ?)),
            ?,
            COALESCE(?, (SELECT job_id FROM run_status WHERE dirpath = ?)),
            COALESCE(?, (SELECT analysis_id FROM run_status WHERE dirpath = ?))
        )
    ''', (dirpath, run_id, dirpath, dirpath, stage, output_dir, dirpath, status, job_id, dirpath, analysis_id, dirpath))

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

def get_run_metrics(run_id):
    '''Grab q30 and error rate from run_metrics table'''
    conn = sqlite3.connect("db/pipemanager.db")
    cursor = conn.cursor()

    cursor.execute("SELECT q30, error_rate FROM run_metrics WHERE run_id = ?", (run_id,))
    result = cursor.fetchone()

    conn.close()

    if result:
        return result
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
    dxpy.set_security_context({"auth_token_type": "Bearer", "auth_token": DX_API_KEY})
    
    for job in dxpy.find_jobs(project=project_id):
        job_desc = dxpy.DXJob(job['id']).describe()
        if basename in str(job_desc['folder']):
            return job_desc['state'], job_desc['id']
    return None

def get_dx_analysis_status(basename, project_id):
    '''Scrape the DNAnexus API for run status - IMPORTANT - REMOVE API TOKEN BEFORE MAKING REPO LIVE'''
    dxpy.set_security_context({"auth_token_type": "Bearer", "auth_token": DX_API_KEY})
    
    for analysis in dxpy.find_analyses(project=project_id, no_parent_job=True, include_subjobs=False):
        analysis_desc = dxpy.DXAnalysis(analysis['id']).describe()
        if basename in str(analysis_desc['folder']):
            return analysis_desc['state'], analysis_desc['id']
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
    '''Check RTA has completed, then begin polling for demultiplex status using DNAnexus API'''
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
    '''Run q_scrape after demultiplex is complete'''
    print(f'Processing Stage 4 (QC checking) in {dirpath}')
    run_status = get_run_status(dirpath)
    output_dir = run_status['output_dir']

    subprocess.run(['python3', 'q_scrape.py', output_dir, dirpath, str(run_status['run_id'])], check=True)
    update_run_status(dirpath, 5, 'QC check complete')

def process_stage5(dirpath, file):
    '''Ensure the QC is valid before launching analysis'''
    print(f'Processing Stage 5 (launch analysis) in {dirpath}')
    run_status = get_run_status(dirpath)
    output_dir = run_status['output_dir']
    run_id = run_status['run_id']

    run_metrics = get_run_metrics(run_id)
        
    if run_metrics and run_metrics[0] > 80 and run_metrics[1] < 2:
        #subprocess.run(['yes', 'Y'], check=True)
        #subprocess.run(['python3', '/projects/dnanexus/tso500-prepare-inputs/create_inputs.py', output_dir, '-s', os.path.join(output_dir, 'SampleSheet.csv')], check=True)
        print('python3 ' + ' /projects/dnanexus/tso500-prepare-inputs/create_inputs.py ' + output_dir + ' -s ' + os.path.join(output_dir, 'SampleSheet.csv'))
        print(f'Pipeline launched for run: {run_id}')
        update_run_status(dirpath, 6, 'Pipeline launched')
    else:
        print(f'Run: {run_id} has failed quality control and cannot automatically be launched. Please check this run manually before proceeding.')
        return

    #update_run_status(dirpath, None, 'Run completed')

def process_stage6(dirpath, file):
    '''Begin polling for analysis status using DNAnexus API'''
    print(f'Processing Stage 6 (check analysis) in {dirpath}')
    run_status = get_run_status(dirpath)
    run_id = run_status['run_id']
    output_dir = run_status['output_dir']
    basename = os.path.basename(output_dir)
    # Run get_dx_job_status using the 'landing' directory as the base
    job_state, job_id = get_dx_analysis_status(basename, 'project-G20fJgQ4V6pqf5GqFF4ZZfGV')

    if job_state == 'done':
        print(f"Analysis for run {run_id} is complete.")
        update_run_status(dirpath, 7, 'Analysis complete', analysis_id=job_id)
    else:
        print(f"Analysis for {run_id} is not complete. Current state: {job_state}")
        update_run_status(dirpath, 6, 'Pipeline in progress', analysis_id=job_id)

def main():
    # Create the necessary SQLite structure
    setup_database()
    # Define the technical directory for locating the xlsx files
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
            # Iterate through all the stages of the pipeline depending on the run_folder status
            elif run_status['stage'] == 2:
                process_stage2(dirpath, file)
            elif run_status['stage'] == 3:
                process_stage3(dirpath, file)
            elif run_status['stage'] == 4:
                process_stage4(dirpath, file)
            elif run_status['stage'] == 5:
                process_stage5(dirpath, file)
            elif run_status['stage'] == 6:
                process_stage6(dirpath, file)

        update_last_check() # Update the database to reflect check has taken place
        time.sleep(30)  # Check for new directories every 30 seconds

if __name__ == '__main__':
    main()