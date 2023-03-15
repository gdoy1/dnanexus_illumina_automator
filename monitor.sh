# Developed by George
# 14/02/2023

# Script designed to poll for changes in technical directory, generate SampleSheets in appropriate directory, 
# poll for RTA completion, and launch pipeline via create_inputs.py

#!/bin/bash

# settings.xml variables
PROJECT=$(grep -oPm1 "(?<=<project>)[^<]+" settings.xml)
VENV_PATH=$(grep -oPm1 "(?<=<virtual_env>)[^<]+" settings.xml)
RUN_DIRECTORY=$(grep -oPm1 "(?<=<run_directory>)[^<]+" settings.xml)

# loop through technical directories
for dir in "${RUN_DIRECTORY}"
do
  # check for new .xlsx files in the directory
  new_files=("$dir"/*.xlsx)

  # check if flag or move file exists in the directory
  for file in $new_files; do
    dir=$(dirname "$file")
    if [ -f "${dir}/flag.txt" ]; then
      echo "flag.txt detected in ${dir}"
      # flag file exists, run ssmove.py and skip this file
      source ${VENV_PATH}/bin/activate
      python3 ssmove.py "$file"
      continue
    elif [ -f "${dir}/move.txt" ]; then
      # read the RTA directory from move.txt
      echo "move.txt detected in ${dir}"
      output_dir=$(cat "${dir}/move.txt")
      # run is complete, ignore
      if [ -f "${output_dir}/pipeline.launch" ]; then
          continue
      # QC has passed, launch create_inputs.py
      elif [ -f "${output_dir}/qc.pass" ]; then
          yes Y | python3 /projects/dnanexus/tso500-prepare-inputs/create_inputs.py "$output_dir" -s "${output_dir}/SampleSheet.csv"
          touch "${output_dir}/pipeline.launch"
      # RTA has finished, commence QC check
      elif [ -f "${output_dir}/RTAComplete.txt" ]; then
          python3 q_scrape.py "$output_dir" "$dir"
      fi
    else
      # no flag or move file, extract filename from path and store in variable
      filename=$(basename "$file")
      # activate virtual environment and run ssgen.py
      source ${VENV_PATH}/bin/activate
      python3 ssgen.py "$file"
      # DISABLED - call trello.py with filename and filepath as arguments
      # python3 /home/bioinf/george/pipeline_automation/trello.py -n "$filename" -c "$file"
    fi
  done
done