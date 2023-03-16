# Developed by George
# 14/02/2023

# Script designed to move samplesheets to corresponding runfolder based on RunParameters.xml

import sys
import os
import openpyxl
import shutil
import xml.etree.ElementTree as ET
import glob

# parse settings.xml, return the root element
def parse_settings(settings_file):
    settings_tree = ET.parse(settings_file)
    settings_root = settings_tree.getroot()
    return settings_root

# find matching RunParameters.xml file and output_dir from RTA_directory
def find_matching_run_params_file(runs_dir, search_string):
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

# move csv files to the output_dir
def move_csv_files(excel_file, output_dir):
    excel_dir = os.path.dirname(excel_file)
    for file_name in os.listdir(excel_dir):
        if file_name.endswith('.csv'):
            shutil.move(os.path.join(excel_dir, file_name), os.path.join(output_dir, file_name))
    print(f'Moved CSV files from {excel_dir} to {output_dir}')

# rename flag.txt to move.txt, store output_dir inside
def rename_and_store_flag_file(excel_file, output_dir):
    flag_file = os.path.join(os.path.dirname(excel_file), 'flag.txt')
    if os.path.exists(flag_file):
        os.rename(flag_file, os.path.join(os.path.dirname(excel_file), 'move.txt'))
        with open(os.path.join(os.path.dirname(excel_file), 'move.txt'), 'a') as f:
            f.write(f'{output_dir}\n')

# function to run the script
def main(excel_file):
    settings_file = 'settings.xml'
    settings_root = parse_settings(settings_file)
    runs_dir = settings_root.find('directories/RTA_directory').text

    # open the TSO500 Combined Loading worksheet to extract ExperimentName
    workbook = openpyxl.load_workbook(excel_file, data_only=True)
    worksheet = workbook['TSO500 Combined Loading']
    search_string = worksheet['B4'].value
    run_params_file, output_dir = find_matching_run_params_file(runs_dir, search_string)

    # move csv files and rename flag.txt if a match was found
    if output_dir is not None:
        move_csv_files(excel_file, output_dir)
        rename_and_store_flag_file(excel_file, output_dir)
    else:
        print(f'Error: Matching RunParameters.xml file not found for search string "{search_string}"')

# run the main function if called from the command line
if __name__ == "__main__":
    excel_file = sys.argv[1]
    main(excel_file)
