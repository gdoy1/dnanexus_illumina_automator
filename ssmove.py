# Developed by George
# 14/02/2023

# Script designed to move samplesheets to corresponding runfolder based on RunParameters.xml

import sys
import os
import openpyxl
import shutil
import xml.etree.ElementTree as ET
import glob

# parse settings.xml
settings_file = 'settings.xml'
settings_tree = ET.parse(settings_file)
settings_root = settings_tree.getroot()

# get path to the Excel file from argv1
excel_file = sys.argv[1]

# get ExperimentName
workbook = openpyxl.load_workbook(excel_file, data_only=True)
worksheet = workbook['TSO500 Combined Loading']
search_string = worksheet['B4'].value

# find the matching RunParameters.xml file and get the output directory
runs_dir = settings_root.find('directories/RTA_directory').text
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

            # move csv files in the input directory to the output directory
            excel_dir = os.path.dirname(excel_file)
            for file_name in os.listdir(excel_dir):
                if file_name.endswith('.csv'):
                    shutil.move(os.path.join(excel_dir, file_name), os.path.join(output_dir, file_name))

            # rename flag.txt to move.txt
            flag_file = os.path.join(os.path.dirname(excel_file), 'flag.txt')
            if os.path.exists(flag_file):
                os.rename(flag_file, os.path.join(os.path.dirname(excel_file), 'move.txt'))

            # store the run location in move.txt
            with open(os.path.join(os.path.dirname(excel_file), 'move.txt'), 'a') as f:
                f.write(f'{output_dir}\n')

            # log message
            print(f'Moved CSV files from {excel_dir} to {output_dir}')
            break

# log an error message if a matching RunParameters.xml file is not found
if output_dir is None:
    print(f'Error: Matching RunParameters.xml file not found for search string "{search_string}"')
