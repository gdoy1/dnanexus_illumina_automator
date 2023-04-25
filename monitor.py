import os
import glob
import subprocess
import sqlite3
import time
import openpyxl
import re
import dxpy
import pytz
import slack_sdk
from datetime import datetime
import yaml


def load_config():
    with open("config.yaml", "r") as config_file:
        return yaml.safe_load(config_file)

config = load_config()
DB_PATH = config['db_path']
SEARCH_PATH = config['search_path']
RUN_DIR = config['run_dir']
DNANEXUS_PROJECT_ID_DEMUX = config['dnanexus_project_id_demux']
DNANEXUS_PROJECT_ID_ANALYSIS = config['dnanexus_project_id_analysis']
DX_API_KEY = os.environ.get('DX_API_KEY')
SLACK_BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN')
SLACK_CHANNEL = config['slack_channel']

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
            cluster_density REAL,
            qscore_histogram TEXT,
            scatter_plot TEXT,
            flowcell REAL,
            instrument REAL,
            side REAL,
            FOREIGN KEY (run_id) REFERENCES run_status(run_id)
        )
    ''')

    # Close the connection
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

    cursor.execute('''
        SELECT run_id, dirpath, stage, output_dir, status, job_id, analysis_id
        FROM run_status
        WHERE dirpath = ?
    ''', (dirpath,))

    result = cursor.fetchone()
    conn.close()

    if result:
        return {
            'run_id': result[0],
            'dirpath': result[1],
            'stage': result[2],
            'output_dir': result[3],
            'status': result[4],
            'job_id': result[5],
            'analysis_id': result[6]
        }
    else:
        return None

def get_run_metrics(run_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT q30, error_rate, yield, cluster_pf, cluster_density
        FROM run_metrics
        WHERE run_id = ?
    ''', (run_id,))

    result = cursor.fetchone()
    conn.close()

    if result:
        return {
            'q30': result[0],
            'error_rate': result[1],
            'yield': result[2],
            'cluster_pf': result[3],
            'cluster_density': result[4]
        }
    else:
        return None

def send_slack_message(channel, text):
    client = slack_sdk.WebClient(token=SLACK_BOT_TOKEN)
    try:
        response = client.chat_postMessage(channel=channel, text=text)
        if response['ok']:
            print(f"Message sent to Slack channel {channel}: {text}")
        else:
            print(f"Failed to send message to Slack channel {channel}: {response['error']}")
    except Exception as e:
        print(f"Error sending Slack message: {e}")

def post_slack_image(channel, image_path, title):
    client = slack_sdk.WebClient(token=SLACK_BOT_TOKEN)
    try:
        if os.path.exists(image_path):
            with open(image_path, "rb") as file:
                response = client.files_upload(
                    channels=channel,
                    file=file,
                    title=title,
                    filename=os.path.basename(image_path)
                )
            if response['ok']:
                print(f"Image '{title}' uploaded to Slack channel {channel}")
            else:
                print(f"Failed to upload image '{title}' to Slack channel {channel}: {response['error']}")
        else:
            print(f"Image '{title}' not found: {image_path}")
    except Exception as e:
        print(f"Error uploading Slack image: {e}")

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
    dxpy.set_security_context({"auth_token_type": "Bearer", "auth_token": DX_API_KEY})
    
    for job in dxpy.find_jobs(project=project_id):
        job_desc = dxpy.DXJob(job['id']).describe()
        if basename in str(job_desc['folder']):
            return job_desc['state'], job_desc['id']
    return None

def get_dx_analysis_status(basename, project_id):
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

    # Check if SampleSheet.csv exists in the directory
    samplesheet_path = os.path.join(dirpath, "SampleSheet.csv")
    if not os.path.exists(samplesheet_path):
        print(f"SampleSheet.csv was not generated correctly in: {dirpath}. Skipping the directory.")
        send_slack_message(SLACK_CHANNEL, f':x: *SampleSheet.csv not generated correctly: {dirpath}* \n\n Please manually generate this run before continuing.')
        return

    # Extract the run_id from the directory name
    basename = os.path.normpath(dirpath).split(os.sep)[-1]
    run_id_match = re.search(r"(\d+)", basename)
    if run_id_match is not None:
        run_id = run_id_match.group()
    else:
        print(f"Failed to extract run_id from directory name: {dirpath}. Skipping the directory.")
        send_slack_message(SLACK_CHANNEL, f':x: *Failed to extract the run_id from foldername: {dirpath}* \n\n Please manually correct this run before continuing.')
        return

    # Update the status in the database
    update_run_status(dirpath, 2, 'SampleSheet generated', run_id)

    # Send a Slack message after completing Stage 1
    send_slack_message(SLACK_CHANNEL, f'*New sequencing run folder detected: {dirpath}* \n\n SampleSheet has been generated :page_facing_up:')


def process_stage2(dirpath, file):
    '''Move the SampleSheets to the correct location before dxstream begins'''
    print(f'Processing Stage 2 in {dirpath}')
    run_status = get_run_status(dirpath)
    run_id = run_status['run_id']

    subprocess.run(['python3', 'ssmove.py', file, str(run_id)], check=True)

    # Refresh run_status after running ssmove.py
    run_status = get_run_status(dirpath)
    output_dir = run_status['output_dir']

    if output_dir is not None:
        update_run_status(dirpath, 3, 'RTA in progress')
        send_slack_message(SLACK_CHANNEL, f':dna: *RTA is currently in progress: {run_id}* \n\n The current run directory is: {output_dir}')
    else:
        print(f'Output directory not found for {dirpath} after running ssmove.py. Skipping the update for this stage.')
        send_slack_message(SLACK_CHANNEL, f':x: *Failed to find the corresponding run directory: {dirpath}*: \n\n Please manually verify this run before continuing.')

def process_stage3(dirpath, file):
    dnanexus_project_id_demux = DNANEXUS_PROJECT_ID_DEMUX
    '''Check RTA has completed, then begin polling for demultiplex status using DNAnexus API'''
    print(f'Processing Stage 3 (demultiplex) in {dirpath}')
    run_status = get_run_status(dirpath)
    run_id = run_status['run_id']
    output_dir = run_status['output_dir']

    if os.path.isfile(os.path.join(output_dir, 'RTAComplete.txt')):
        basename = os.path.basename(output_dir)
        # Run get_dx_job_status using the 'landing' directory as the base
        job_state, job_id = get_dx_job_status(basename, dnanexus_project_id_demux)

        if job_state == 'done':
            print(f"Demultiplex for run {run_id} is complete. Proceeding to analysis.")
            update_run_status(dirpath, 4, 'Demultiplexing complete', job_id=job_id)
            send_slack_message(SLACK_CHANNEL, f':white_check_mark: *Demultiplex complete: {run_id}* \n\n ```{job_id}```')
        else:
            print(f"Demultiplex for {run_id} is not complete. Current state: {job_state}")
            update_run_status(dirpath, 3, 'Demultiplex in progress', job_id=job_id)
            send_slack_message(SLACK_CHANNEL, f':hourglass: *Demultiplex is currently in progress: {run_id}* \n\n ```{job_id}```')
    else:
        print(f'RTA in progress: {dirpath}')


def process_stage4(dirpath, file):
    '''Run q_scrape after demultiplex is complete'''
    print(f'Processing Stage 4 (QC checking) in {dirpath}')
    run_status = get_run_status(dirpath)
    output_dir = run_status['output_dir']

    subprocess.run(['python3', 'q_scrape.py', output_dir, str(run_status['run_id'])], check=True)
    update_run_status(dirpath, 5, 'QC PASS')

    # Pass data to Slack
    run_id = run_status['run_id']
    run_metrics = get_run_metrics(run_id)
    q30 = round(run_metrics.get('q30', 'N/A'), 2)
    er = round(run_metrics.get('error_rate', 'N/A'), 2)
    cpf = round(run_metrics.get('cluster_pf', 'N/A'), 2)
    cden = round(run_metrics.get('cluster_density', 'N/A'), 2)
    yie = round(run_metrics.get('yield', 'N/A'), 2)

    send_slack_message(SLACK_CHANNEL, f':partying_face: *Quality control check PASSED: {run_id}* \n\n Run level metrics: \n\n Q30: {q30}%\n Error rate: {er}%\n Cluster PF: {cpf}%\n Cluster density: {cden} K/mm2\n Yield: {yie} Gb')

    # Post images to Slack using relative paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(script_dir, 'static', 'qscore_histograms', f'qscore_histogram_{run_id}.png')
    post_slack_image(SLACK_CHANNEL, image_path, f"Q-score histogram for run {run_id}")
    image_path = os.path.join(script_dir, 'static', 'scatter_plots', f'scatter_plot_{run_id}.png')
    post_slack_image(SLACK_CHANNEL, image_path, f"Scatter plot for run {run_id}")

def process_stage5(dirpath, file):
    '''Ensure the QC is valid before launching analysis'''
    print(f'Processing Stage 5 (launch analysis) in {dirpath}')
    run_status = get_run_status(dirpath)
    output_dir = run_status['output_dir']
    run_id = run_status['run_id']

    run_metrics = get_run_metrics(run_id)
        
    if run_metrics and run_metrics['q30'] > 80 and run_metrics['error_rate'] < 2:
        #subprocess.run(['yes', 'Y'], check=True)
        #subprocess.run(['python3', '/projects/dnanexus/tso500-prepare-inputs/create_inputs.py', output_dir, '-s', os.path.join(output_dir, 'SampleSheet.csv')], check=True)
        command = 'python3 ' + '/projects/dnanexus/tso500-prepare-inputs/create_inputs.py ' + output_dir + ' -s ' + os.path.join(output_dir, 'SampleSheet.csv')
        print(f'Pipeline launched for run: {run_id}')
        update_run_status(dirpath, 6, 'Pipeline launched')
        send_slack_message(SLACK_CHANNEL, f':computer: *Pipeline has been launched: {run_id}* \n\n ``` {command} ```')
    else:
        print(f'Run: {run_id} has failed quality control and cannot automatically be launched. Please check this run manually before proceeding.')
        send_slack_message(SLACK_CHANNEL, f':x: *Failed to find the corresponding run directory: {dirpath}*: \n\n Please manually verify this run before continuing.')
        return

    #update_run_status(dirpath, None, 'Run completed')

def process_stage6(dirpath, file):
    dnanexus_project_id_analysis = DNANEXUS_PROJECT_ID_ANALYSIS
    '''Begin polling for analysis status using DNAnexus API'''
    print(f'Processing Stage 6 (check analysis) in {dirpath}')
    run_status = get_run_status(dirpath)
    run_id = run_status['run_id']
    output_dir = run_status['output_dir']
    basename = os.path.basename(output_dir)
    # Run get_dx_job_status using the 'landing' directory as the base
    job_state, job_id = get_dx_analysis_status(basename, dnanexus_project_id_analysis)

    if job_state == 'done':
        print(f"Analysis for run {run_id} is complete.")
        update_run_status(dirpath, 7, 'Analysis complete', analysis_id=job_id)
        send_slack_message(SLACK_CHANNEL, f':star2: *Pipeline has completed successfully: {run_id}* \n\n ```{job_id}```')
    elif job_state == 'failed':
        print(f"Analysis for run {run_id} failed.")
        update_run_status(dirpath, 0, 'FAILED', analysis_id=job_id)
        send_slack_message(SLACK_CHANNEL, f':x: *Pipeline has failed: {run_id}* \n\n ```{job_id}```')
    else:
        print(f"Analysis for {run_id} is not complete. Current state: {job_state}")
        update_run_status(dirpath, 6, 'Pipeline in progress', analysis_id=job_id)
        send_slack_message(SLACK_CHANNEL, f':hourglass_flowing_sand: *Pipeline is currently in progress: {run_id}* \n\n ```{job_id}```')

def main():
# Create the necessary SQLite structure
    setup_database()
    search_path = SEARCH_PATH

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
        print('Loop complete. Repeating...')
        time.sleep(30)  # Check for new directories every 30 seconds

if __name__ == '__main__':
    main()