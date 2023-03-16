# Developed by George
# 14/02/2023

# Script designed to move samplesheets to corresponding runfolder based on RunParameters.xml

import sys
import os
import openpyxl
import shutil
import xml.etree.ElementTree as ET
import glob

def parse_settings(settings_file):
    """Parse settings.xml, return the root element."""
    settings_tree = ET.parse(settings_file)
    settings_root = settings_tree.getroot()
    return settings_root

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

def move_csv_files(excel_file, output_dir):
    """Move csv files to the output_dir."""
    excel_dir = os.path.dirname(excel_file)
    for file_name in os.listdir(excel_dir):
        if file_name.endswith('.csv'):
            shutil.move(os.path.join(excel_dir, file_name), os.path.join(output_dir, file_name))
    print(f'Moved CSV files from {excel_dir} to {output_dir}')

def rename_and_store_flag_file(excel_file, output_dir):
    """Rename flag.txt to move.txt, store output_dir inside."""
    flag_file = os.path.join(os.path.dirname(excel_file), 'flag.txt')
    if os.path.exists(flag_file):
        os.rename(flag_file, os.path.join(os.path.dirname(excel_file), 'move.txt'))
        with open(os.path.join(os.path.dirname(excel_file), 'move.txt'), 'a') as f:
            f.write(f'{output_dir}\n')

def main(excel_file):
    settings_file = 'settings.xml'
    settings_root = parse_settings(settings_file)
    runs_dir = settings_root.find('directories/RTA_directory').text

    workbook = openpyxl.load_workbook(excel_file, data_only=True)
    worksheet = workbook['TSO500 Combined Loading']
    search_string = worksheet['B4'].value
    run_params_file, output_dir = find_matching_run_params_file(runs_dir, search_string)

    if output_dir is not None:
        move_csv_files(excel_file, output_dir)
        rename_and_store_flag_file(excel_file, output_dir)
    else:
        print(f'Error: Matching RunParameters.xml file not found for search string "{search_string}"')

if __name__ == "__main__":
    excel_file = sys.argv[1]
    main(excel_file)
