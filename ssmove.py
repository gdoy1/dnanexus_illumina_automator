# Developed by George
# 14/02/2023

# Script designed to move samplesheets to corresponding runfolder based on RunParameters.xml

import sys
import os
import openpyxl
import shutil
import xml.etree.ElementTree as ET
import glob
import sqlite3
import yaml

def load_config(config_file='config.yaml'):
    with open(config_file) as file:
        return yaml.safe_load(file)

def find_matching_run_params_file(runs_dir, search_string):
    """Find matching RunParameters.xml file and output_dir from RTA_directory."""
    rta_dirs = glob.glob(os.path.join(runs_dir))
    run_params_file = None
    output_dir = None
    for rta_dir in rta_dirs:
        params_path = os.path.join(rta_dir, 'RunParameters.xml')
        if os.path.exists(params_path):
            params_tree = ET.parse(params_path)
            params_root = params_tree.getroot()
            if search_string in params_root.find('ExperimentName').text:
                run_params_file = params_path
                output_dir = os.path.dirname(run_params_file)
                break
    return run_params_file, output_dir

def update_run_status_output_dir(search_string, output_dir, config):
    db_path = config['db_path']
    DB_PATH = db_path
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('UPDATE run_status SET output_dir = ? WHERE run_id = ?', (output_dir, int(search_string)))
    conn.commit()
    conn.close()

def move_csv_files(excel_file, output_dir):
    """Move csv files to the output_dir."""
    excel_dir = os.path.dirname(excel_file)
    for file_name in os.listdir(excel_dir):
        if file_name.endswith('.csv'):
            shutil.move(os.path.join(excel_dir, file_name), os.path.join(output_dir, file_name))
    print(f'Moved CSV files from {excel_dir} to {output_dir}')

def main(excel_file, search_string, config):
    runs_dir = config['run_dir']
    run_params_file, output_dir = find_matching_run_params_file(runs_dir, search_string)

    if output_dir is not None:
        move_csv_files(excel_file, output_dir)
        update_run_status_output_dir(search_string, output_dir, config)
    else:
        print(f'Error: Matching RunParameters.xml file not found for search string "{search_string}"')

if __name__ == "__main__":
    excel_file = sys.argv[1]
    search_string = sys.argv[2]
    config = load_config()
    main(excel_file, search_string, config)