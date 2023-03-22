# Developed by George
# 14/02/2023

# Script designed to poll for changes in technical directory, generate SampleSheets in appropriate directory, 
# poll for RTA completion, and launch pipeline via create_inputs.py

import os
import glob
import subprocess

def find_new_files(dirpath):
    return glob.glob(os.path.join(dirpath, '*.xlsx'))

def process_flag_file(dirpath, file):
    print(f'flag.txt detected in {dirpath}')
    subprocess.run(['python3', 'ssmove.py', file], check=True)

def process_move_file(dirpath, file):
    print(f'move.txt detected in {dirpath}')
    with open(os.path.join(dirpath, 'move.txt'), 'r') as f:
        output_dir = f.read().strip()

    if os.path.isfile(os.path.join(output_dir, 'pipeline.launch')):
        return
    elif os.path.isfile(os.path.join(output_dir, 'qc.pass')):
        subprocess.run(['yes', 'Y'], check=True)
        subprocess.run(['python3', '/projects/dnanexus/tso500-prepare-inputs/create_inputs.py', output_dir, '-s', os.path.join(output_dir, 'SampleSheet.csv')], check=True)
        open(os.path.join(output_dir, 'pipeline.launch'), 'w').close()
    elif os.path.isfile(os.path.join(output_dir, 'RTAComplete.txt')):
        subprocess.run(['python3', 'q_scrape.py', output_dir, dirpath], check=True)

def process_file_without_flag_or_move(file):
    filename = os.path.basename(file)
    subprocess.run(['python3', 'ssgen.py', file], check=True)

def main():
    for dirpath in glob.glob('/home/bioinf/george/pipeline_automation/*/*/*/', recursive=True):
        new_files = find_new_files(dirpath)
        
        for file in new_files:
            if os.path.isfile(os.path.join(dirpath, 'flag.txt')):
                process_flag_file(dirpath, file)
            elif os.path.isfile(os.path.join(dirpath, 'move.txt')):
                process_move_file(dirpath, file)
            else:
                process_file_without_flag_or_move(file)

if __name__ == '__main__':
    main()
