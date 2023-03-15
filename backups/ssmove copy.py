import sys
import os
import openpyxl
import shutil
import xml.etree.ElementTree as ET

# Parse the settings.xml file
settings_file = 'settings.xml'
settings_tree = ET.parse(settings_file)
settings_root = settings_tree.getroot()

# Get the path to the Excel file from the command line argument
excel_file = sys.argv[1]

# Get the value of cell B4 in the TSO500 Combined Loading tab
workbook = openpyxl.load_workbook(excel_file, data_only=True)
worksheet = workbook['TSO500 Combined Loading']
search_string = worksheet['B4'].value

# Find the matching RunParameters.xml file and get the output directory
# runs_dir = '/home/bioinf/george/pipeline_automation/dxstream/runs'
runs_dir = settings_root.find('directories/RTA_directory').text
run_params_file = None
output_dir = None
for root, dirs, files in os.walk(runs_dir):
    if 'RunParameters.xml' in files:
        params_path = os.path.join(root, 'RunParameters.xml')
        params_tree = ET.parse(params_path)
        params_root = params_tree.getroot()
        if search_string in params_root.find('ExperimentName').text:
            run_params_file = params_path
            output_dir = os.path.dirname(run_params_file)
            break

# Move all CSV files in the input directory to the output directory
if output_dir is not None:
    excel_dir = os.path.dirname(excel_file)
    for file_name in os.listdir(excel_dir):
        if file_name.endswith('.csv'):
            shutil.move(os.path.join(excel_dir, file_name), os.path.join(output_dir, file_name))

    # Log a message
    print(f'Moved CSV files from {excel_dir} to {output_dir}')
else:
    # Log an error message if a matching RunParameters.xml file is not found
    print(f'Error: Matching RunParameters.xml file not found for search string "{search_string}"')

# Rename flag.txt to move.txt
flag_file = os.path.join(os.path.dirname(excel_file), 'flag.txt')
if os.path.exists(flag_file):
    os.rename(flag_file, os.path.join(os.path.dirname(excel_file), 'move.txt'))

# Store the run location in move.txt
with open(os.path.join(os.path.dirname(excel_file), 'move.txt'), 'a') as f:
    f.write(f'{output_dir}\n')

