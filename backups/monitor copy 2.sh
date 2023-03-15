#!/bin/bash

# Settings.xml variables
PROJECT=$(grep -oPm1 "(?<=<project>)[^<]+" settings.xml)
VENV_PATH=$(grep -oPm1 "(?<=<virtual_env>)[^<]+" settings.xml)
RUN_DIRECTORY=$(grep -oPm1 "(?<=<run_directory>)[^<]+" settings.xml)

# Loop through all run directories
for dir in "${RUN_DIRECTORY}"
do
  # Check for new .xlsx files in the directory
  new_files=$(find $dir -maxdepth 1 -type f -name "*.xlsx")

  # Check if flag or move file exists in the directory
  for file in $new_files; do
    dir=$(dirname "$file")
    if [ -f "${dir}/flag.txt" ]; then
      echo "flag.txt detected in ${dir}"
      # Flag file exists, run ssmove.py and skip this file
      source ${VENV_PATH}/bin/activate
      python3 ssmove.py "$file"
      continue
    elif [ -f "${dir}/move.txt" ]; then
      # Read the output directory from move.txt
      echo "flag.txt detected in ${dir}"
      output_dir=$(cat "${dir}/move.txt")
      # Check if RTAComplete exists
      if [ -f "${output_dir}/pipeline.launch" ]; then
          continue
      elif [ -f "${output_dir}/qc.pass" ]; then
          yes Y | python3 /projects/dnanexus/tso500-prepare-inputs/create_inputs.py "$output_dir" -s "${output_dir}/SampleSheet.csv"
          touch "${output_dir}/pipeline.launch"
      elif [ -f "${output_dir}/RTAComplete.txt" ]; then
          python3 /home/bioinf/george/pipeline_automation/q_scrape.py "$output_dir" "$dir"
      fi
      continue
    fi

    # No flag or move file, process the new files
    if [[ -n "$new_files" ]]; then
      # Loop through the new files found
      for file in $new_files; do
        # Extract filename from path and store in variable
        filename=$(basename "$file")
        # New .xlsx file detected, activate virtual environment and run Python script
        source ${VENV_PATH}/bin/activate
        python3 ssgen.py "$file"
        # Call trello.py with filename and filepath as arguments
        # python3 /home/bioinf/george/pipeline_automation/trello.py -n "$filename" -c "$file"
        # Log message and create flag file
        echo "New SampleSheet detected in: $file"
      done
    fi
  done
done